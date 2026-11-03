# 🗂 MemeVault

**A local-first image browser and curation tool — no cloud, no uploads, your files stay yours.**

MemeVault is a lightweight Python app that runs entirely on your computer. Point it at any folder of images, tag them with custom color-coded categories, and export exactly the ones you want. Built for meme collectors, Discord hoarders, and anyone who has ever had a folder called `memes_final_v3`.

> Open source by [Risk Averse Technology Company](https://github.com/RiskAverseTech) · Built for the [Create a Meme](https://www.createa.meme) community

---

## ✨ Features

- **Thumbnail grid browser** — lazy-loads thousands of images without slowing down
- **Custom heart categories** — create as many as you want, each with its own name and color
- **Multi-category tagging** — one image can belong to multiple categories at once
- **Filter by category** — instantly see only the images tagged a certain way
- **Filename search** — filter by name in real time
- **Click to zoom** — any image opens in a full modal with prev/next navigation and keyboard shortcuts
- **Works on a phone screen** — the grid, toolbar and dialogs rearrange below 640px
- **Export marked images** — pick which categories to export, choose a destination folder, copy or move
- **Persistent marks** — everything saves to a `.memevault_data.json` file in your images folder automatically
- **Reads what your folder actually holds** — jpg, png, gif, webp, bmp, tiff, avif, svg, and the `photo.jpg%3alarge` names that downloads from X leave behind; iPhone HEIC too with one optional package; `--recursive` includes subfolders
- **Add photos from your phone** — opt-in `--lan` mode prints a one-time link; open it on a phone on the same Wi-Fi and use **📱 Add Images** to copy photos straight into the folder
- **Zero data leaves your machine** — runs on `localhost:5000` by default and talks to no outside server, ever. With `--lan` on, nothing leaves your local network

---

## 🚀 Quick Start

**Requirements:** Python 3.8+ · Flask. Optional: Pillow + pillow-heif for iPhone HEIC photos, qrcode for a scannable link in `--lan` mode.

```bash
# 1. Install Flask (one time). Add the optional packages if you want them.
python -m pip install flask
python -m pip install pillow pillow-heif qrcode   # optional

# 2. Run MemeVault pointed at your images folder
python meme_vault.py --folder /path/to/your/images

# 3. Open in your browser
# → http://localhost:5000
```

On Mac you can drag your images folder from Finder into the terminal after `--folder ` to auto-fill the path.

| Flag | What it does |
|---|---|
| `--folder PATH` | The images folder. Required. Marks are saved there in `.memevault_data.json`. |
| `--port N` | Port to listen on. Default 5000. |
| `--recursive` | Include images in subfolders. Marks are keyed by the relative path. |
| `--lan` | Also listen on your local network so a phone can open the vault and add photos. See below. |

### Formats

MemeVault lists jpg, jpeg, png, gif, webp, bmp, tiff, avif and svg. Files whose
name carries a URL tail after the real extension, like `photo.jpg%3alarge` or
`photo.jpg:large` from X/Twitter downloads, are recognised by the extension in
front of the tail. HEIC and HEIF (the iPhone default) are listed when Pillow and
pillow-heif are installed; MemeVault converts them to JPEG for display on the
fly and keeps the converted copies in `.memevault_cache` inside your folder. The
originals are never modified. Without pillow-heif, HEIC files are skipped and the
startup message says how many.

### Phone photos: `--lan` mode

Most memes live on a phone. `--lan` is how they get into the vault without a
cloud in between.

```bash
python meme_vault.py --folder /path/to/your/images --lan
```

MemeVault then also listens on your local network and prints a link containing
a random one-time token (and a QR code if `qrcode` is installed). Open that link
on a phone on the same Wi-Fi, tap **📱 Add Images**, and pick photos from the
camera roll. They are copied into the folder on your computer and nowhere else.
iPhones convert HEIC to JPEG when uploading through the browser, so most photos
arrive ready to view even without pillow-heif.

What the token does and does not do:

- Every request needs it. Without the exact link, the phone sees a refusal and
  the images are not served.
- It is new on every start and dies when you quit MemeVault.
- Anyone on your Wi-Fi who has the link can see the whole folder and add to it.
  Treat the link like a key: do not paste it into a group chat.
- Requests whose `Host` header is not this machine are refused, in both modes,
  so a web page you visit elsewhere cannot steer the vault through your browser.
- Uploads are checked: the file name is sanitised, the extension must be an
  image type MemeVault lists, the first bytes must match that type, and SVGs
  containing scripts are refused. Images are served with a Content-Security-Policy
  that stops any script inside an SVG from running if one is opened directly.

With `--lan` off (the default) MemeVault binds to `127.0.0.1` only and nothing
on your network can reach it.

---

## 🎨 Custom Categories

MemeVault ships with three default categories (Fave, Funny, Send) but you can create your own:

1. Click **🎨 Categories** in the toolbar
2. Type a name, pick a color, hit **+ Add**
3. Your categories appear as filter tabs and in the heart picker on every image

Categories are stored in the same `.memevault_data.json` file as your marks — delete the file to start fresh, or just delete individual categories from the UI.

**Suggested categories if you're organizing a Create a Meme Discord download:**

| Category | Color |
|---|---|
| CAM Originals | `#ff4d6d` |
| Stolen | `#ffd166` |
| Faceswap | `#a78bfa` |
| GM | `#06d6a0` |
| Templates | `#60a5fa` |
| GIF | `#fb923c` |

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `←` / `→` | Navigate images in modal |
| `Esc` | Close modal or picker |

---

## 📁 Export

1. Mark images by hovering a thumbnail and clicking the **♥** button
2. Pick one or more categories in the heart picker
3. Click **📁 Export** in the toolbar
4. Choose which categories to include, set a destination path, pick Copy or Move
5. Hit **Export Now**

---

## 🛠 Tech Stack

- **Python 3** + **Flask** — local HTTP server
- **Vanilla JS** — no build step, no dependencies, runs in any browser
- **JSON** — marks and categories stored as a single flat file

---

## 📦 Installation from Source

```bash
git clone https://github.com/RiskAverseTech/MemeVault.git
cd MemeVault
python -m pip install flask
python meme_vault.py --folder /your/images/folder
```

---

## 🤝 Contributing

PRs welcome. This is intentionally kept simple — one Python file, one HTML template, no build tools. If you're adding a feature, keep it local-first and dependency-light.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

## 🏢 About

MemeVault is an open source project by [Risk Averse Technology Company](https://www.riskaversetechnology.company/) (RATC), an AI product studio.

Other RATC open source projects: [see our GitHub](https://github.com/RiskAverseTech)

A [Create a Meme](https://www.createa.meme) open source project for the memer community.
