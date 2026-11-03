"""MemeVault checks. Standard library only.

    python test_meme_vault.py            # formats, host guard, uploads, export, LAN token flow
    python test_meme_vault.py --heic     # also HEIC, needs pillow + pillow-heif installed

Starts meme_vault.py twice (localhost mode, then --lan --recursive) against a
temporary folder, drives it over HTTP, and removes the folder afterwards.
"""
import subprocess, sys, time, json, os, io, re, shutil, struct, zlib, tempfile, urllib.request, urllib.error
from http.cookiejar import CookieJar

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'meme_vault.py')
WANT_HEIC = '--heic' in sys.argv
S = tempfile.mkdtemp(prefix='mv2-')
imgs = os.path.join(S, 'imgs'); sub = os.path.join(imgs, 'sub'); out = os.path.join(S, 'out')
os.makedirs(sub); os.makedirs(out)

def png_bytes():
    raw = b''.join(b'\x00' + b'\xff\x00\x00' * 4 for _ in range(4))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 4, 4, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
PNG = png_bytes()
SVG = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4"/></svg>'
BAD_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

open(os.path.join(imgs, 'a.png'), 'wb').write(PNG)
open(os.path.join(imgs, 'tweet.jpg%3alarge'), 'wb').write(b'\xff\xd8\xff\xe0' + b'\x00' * 32)
open(os.path.join(imgs, 'icon.svg'), 'wb').write(SVG)
open(os.path.join(imgs, 'notes.txt'), 'wb').write(b'hello')
open(os.path.join(sub, 'deep.png'), 'wb').write(PNG)
open(os.path.join(S, 'secret.txt'), 'w').write('outside')
if WANT_HEIC:
    from PIL import Image
    import pillow_heif; pillow_heif.register_heif_opener()
    Image.new('RGB', (8, 8), (10, 200, 10)).save(os.path.join(imgs, 'phone.heic'), format='HEIF')
    HEIC = open(os.path.join(imgs, 'phone.heic'), 'rb').read()

results = []
def check(name, ok): results.append((name, bool(ok))); print(('PASS' if ok else 'FAIL'), name, flush=True)
import atexit
PROCS = []
atexit.register(lambda: [pr.kill() for pr in PROCS if pr.poll() is None])

def start(extra):
    import socket
    port = 5080 + len(extra)
    with socket.socket() as sk:
        if sk.connect_ex(('127.0.0.1', port)) == 0: raise SystemExit(f'port {port} already in use; stale server?')
    p = subprocess.Popen([sys.executable, '-u', APP, '--folder', imgs, '--port', str(port)] + extra,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    PROCS.append(p)
    base = f'http://127.0.0.1:{port}'
    banner = ''
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            urllib.request.urlopen(urllib.request.Request(base + '/api/status', headers={'Host': f'127.0.0.1:{port}'}), timeout=1); break
        except urllib.error.HTTPError:
            break
        except Exception:
            time.sleep(0.2)
    return p, base, port

def req(opener, url, method='GET', data=None, headers=None, ctype=None):
    h = dict(headers or {})
    body = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body = json.dumps(data).encode(); h['Content-Type'] = ctype or 'application/json'
        else:
            body = data; h['Content-Type'] = ctype or 'application/octet-stream'
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = opener.open(r, timeout=10); return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)

def multipart(files):
    b = b'----mvboundary'
    body = b''
    for name, content in files:
        body += (b'--' + b + b'\r\nContent-Disposition: form-data; name="files"; filename="' + name.encode() + b'"\r\n'
                 b'Content-Type: application/octet-stream\r\n\r\n') + content + b'\r\n'
    body += b'--' + b + b'--\r\n'
    return body, 'multipart/form-data; boundary=' + b.decode()

plain = urllib.request.build_opener()

# ---------------- localhost mode, flat ----------------
p, base, port = start([])
st, body, hdr = req(plain, base + '/api/images')
listed = json.loads(body)
check('flat: lists png, svg, %3alarge; skips txt and subfolder', listed == sorted(['a.png', 'icon.svg', 'tweet.jpg%3alarge'] + (['phone.heic'] if WANT_HEIC else [])))
st, body, hdr = req(plain, base + '/img/' + urllib.parse.quote('tweet.jpg%3alarge'))
check('%3alarge served as image/jpeg', st == 200 and hdr.get('Content-Type', '').startswith('image/jpeg'))
st, body, hdr = req(plain, base + '/img/icon.svg')
check('svg served with CSP and nosniff', st == 200 and "default-src 'none'" in hdr.get('Content-Security-Policy', '') and hdr.get('X-Content-Type-Options') == 'nosniff')
if WANT_HEIC:
    st, body, hdr = req(plain, base + '/img/phone.heic')
    check('heic served as converted jpeg', st == 200 and body[:3] == b'\xff\xd8\xff' and hdr.get('Content-Type', '').startswith('image/jpeg'))
    check('heic cache written inside folder', os.path.isdir(os.path.join(imgs, '.memevault_cache')))
st, body, hdr = req(plain, base + '/api/images', headers={'Host': 'evil.example:' + str(port)})
check('wrong Host header refused (403)', st == 403)
st, body, hdr = req(plain, base + '/api/images', headers={'Host': f'localhost:{port}'})
check('localhost Host accepted', st == 200)
st, body, hdr = req(plain, base + '/api/mark', 'POST', data=b'garbage', ctype='text/plain')
check('/api/mark without JSON does not crash', st == 200)
# uploads
files = [('new.png', PNG), ('../escape.png', PNG), ('fake.png', b'MZ' + b'\x00' * 64), ('run.exe', b'MZ' + b'\x00' * 64),
         ('vector.svg', SVG), ('evil.svg', BAD_SVG), ('a.png', PNG)]
body, ct = multipart(files)
st, resp, hdr = req(plain, base + '/api/upload', 'POST', data=body, ctype=ct)
r = json.loads(resp)
check('upload: valid png saved', 'new.png' in r['saved'])
check('upload: traversal name sanitized, saved inside folder', any(n.endswith('escape.png') for n in r['saved']) and not os.path.exists(os.path.join(S, 'escape.png')))
check('upload: png with non-png bytes rejected', any(x['name'] == 'fake.png' for x in r['rejected']))
check('upload: exe rejected', any(x['name'] == 'run.exe' for x in r['rejected']))
check('upload: clean svg accepted', 'vector.svg' in r['saved'])
check('upload: svg with script rejected', any(x['name'] == 'evil.svg' for x in r['rejected']))
check('upload: duplicate name gets suffix, original untouched', 'a-1.png' in r['saved'] and open(os.path.join(imgs, 'a.png'), 'rb').read() == PNG)
st, body, hdr = req(plain, base + '/api/images')
check('upload: listing refreshed', 'new.png' in json.loads(body))
# export still guarded
st, resp, hdr = req(plain, base + '/api/export', 'POST', data={'dest': out, 'mode': 'copy', 'files': ['../secret.txt', 'a.png']})
check('export: traversal skipped, legit copied', json.loads(resp).get('count') == 1 and not os.path.exists(os.path.join(out, 'secret.txt')))
st, body, hdr = req(plain, base + '/')
check('page has Add Images and no external URL', b'Add Images' in body and b'googleapis' not in body)
p.terminate(); p.wait(timeout=5)
banner1 = p.stdout.read().decode('utf-8','replace')

# ---------------- LAN mode, recursive ----------------
p, base, port = start(['--lan', '--recursive'])
time.sleep(0.3)
# read the banner from the raw pipe until the phone link has been printed
import select
fd = p.stdout.fileno(); buf = b''; deadline = time.time() + 8
while b'Phone' not in buf and time.time() < deadline:
    r, _, _ = select.select([fd], [], [], 0.5)
    if r:
        chunk = os.read(fd, 65536)
        if not chunk: break
        buf += chunk
log = buf.decode('utf-8', 'replace')
m = re.search(r'\?t=([A-Za-z0-9_\-]+)', log)
token = m.group(1) if m else ''
check('lan: banner prints a token link', bool(token))
st, body, hdr = req(plain, base + '/api/images')
check('lan: no token -> 403', st == 403)
st, body, hdr = req(plain, base + '/api/images?t=wrongtoken')
check('lan: wrong token -> 403', st == 403)
st, body, hdr = req(plain, base + '/img/a.png')
check('lan: images also need the token', st == 403)
jar = CookieJar(); cookied = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
st, body, hdr = req(cookied, base + '/?t=' + token)
check('lan: token link sets cookie and lands on page', st == 200 and any(c.name == 'memevault_token' for c in jar) and b'MemeVault' in body)
st, body, hdr = req(cookied, base + '/api/images')
check('lan: cookie grants API; recursive lists sub/deep.png', st == 200 and 'sub/deep.png' in json.loads(body))
st, body, hdr = req(cookied, base + '/img/sub/deep.png')
check('lan: subfolder image served', st == 200)
st, body, hdr = req(cookied, base + '/api/status')
check('lan: status reports lan=true', json.loads(body).get('lan') is True)
body, ct = multipart([('from-phone.png', PNG)])
st, resp, hdr = req(cookied, base + '/api/upload', 'POST', data=body, ctype=ct)
check('lan: upload with cookie works', 'from-phone.png' in json.loads(resp)['saved'])
body, ct = multipart([('intruder.png', PNG)])
st, resp, hdr = req(plain, base + '/api/upload', 'POST', data=body, ctype=ct)
check('lan: upload without token refused', st == 403 and not os.path.exists(os.path.join(imgs, 'intruder.png')))
st, resp, hdr = req(cookied, base + '/api/export', 'POST', data={'dest': out, 'mode': 'copy', 'files': ['sub/deep.png']})
check('lan: export keeps subfolder path', json.loads(resp).get('count') == 1 and os.path.exists(os.path.join(out, 'sub', 'deep.png')))
p.terminate(); p.wait(timeout=5)

ok = all(v for _, v in results)
for n, v in results: print(('PASS' if v else 'FAIL'), n)
print(f"{sum(v for _, v in results)}/{len(results)} passed" + (" (HEIC exercised)" if WANT_HEIC else " (HEIC skipped: no pillow-heif)"))
shutil.rmtree(S, ignore_errors=True)
sys.exit(0 if ok else 1)
