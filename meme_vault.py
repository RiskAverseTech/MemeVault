#!/usr/bin/env python3
"""
MemeVault - Local Image Browser & Curation Tool
Run: python meme_vault.py --folder /path/to/your/images
Then open: http://localhost:5000
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string

app = Flask(__name__)

IMAGE_FOLDER = None
DATA_FILE = None
DATA = {}
IMAGES = []

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.avif'}

DEFAULT_CATEGORIES = [
    {"id": "fave",  "name": "Fave",   "color": "#ff4d6d"},
    {"id": "funny", "name": "Funny",  "color": "#ffd166"},
    {"id": "send",  "name": "Send",   "color": "#06d6a0"},
]

def load_images():
    global IMAGES
    folder = Path(IMAGE_FOLDER)
    IMAGES = sorted([
        f.name for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])
    print(f"✓ Found {len(IMAGES)} images in {IMAGE_FOLDER}")

def load_data():
    global DATA
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            DATA = json.load(f)
    if 'marks' not in DATA:
        DATA['marks'] = {}
    if 'categories' not in DATA:
        DATA['categories'] = DEFAULT_CATEGORIES

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(DATA, f, indent=2)

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MemeVault</title>
<style>
:root {
  --bg: #0a0a0f; --surface: #13131a; --surface2: #1c1c26;
  --border: #2a2a3a; --text: #e8e8f0; --muted: #6b6b85; --radius: 8px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; min-height: 100vh; }

header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(10,10,15,0.93); backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  padding: 0 20px; height: 58px; display: flex; align-items: center; gap: 16px;
}
.logo { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; white-space: nowrap; }
.logo span { color: #ff4d6d; }
.stats { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; color: var(--muted); white-space: nowrap; }
.stats b { color: #ffd166; }
.header-spacer { flex: 1; }
.search-wrap { position: relative; flex: 1; max-width: 260px; }
.search-wrap input {
  width: 100%; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; padding: 7px 12px 7px 30px; color: var(--text);
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 12px; outline: none; transition: border-color 0.2s;
}
.search-wrap input:focus { border-color: #ff4d6d; }
.search-icon { position: absolute; left: 9px; top: 50%; transform: translateY(-50%); color: var(--muted); font-size: 13px; pointer-events: none; }

.toolbar {
  display: flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-bottom: 1px solid var(--border); flex-wrap: wrap;
}
.btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text);
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.btn:hover { background: var(--surface2); border-color: var(--muted); }
.btn.danger { border-color: #ff4444; color: #ff4444; }
.btn.danger:hover { background: #ff4444; color: white; }
.sep { width: 1px; height: 22px; background: var(--border); margin: 0 2px; }
.size-control { display: flex; align-items: center; gap: 6px; margin-left: auto; }
.size-control label { font-size: 11px; color: var(--muted); font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
.size-control input[type=range] { width: 80px; accent-color: #ff4d6d; cursor: pointer; }

.filter-bar {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 20px; border-bottom: 1px solid var(--border); overflow-x: auto; flex-wrap: wrap;
}
.filter-tab {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 12px; border-radius: 20px; border: 1.5px solid var(--border);
  background: var(--surface); color: var(--text);
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 12px; font-weight: 700;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}
.filter-tab .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.filter-tab:hover { border-color: var(--muted); }
.filter-count { font-size: 10px; opacity: 0.7; font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }

.grid-wrap { padding: 16px 20px; }
#grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 7px; }

.thumb-card {
  position: relative; background: var(--surface);
  border-radius: var(--radius); overflow: visible; cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s; aspect-ratio: 1;
}
.thumb-card .img-wrap { width: 100%; height: 100%; border-radius: 6px; overflow: hidden; position: relative; }
.thumb-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 1; }
.thumb-card img { width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity 0.3s; }
.thumb-card img.loading { opacity: 0; }
.thumb-card img.loaded { opacity: 1; }

.cat-dots {
  position: absolute; top: 5px; left: 5px;
  display: flex; gap: 3px; flex-wrap: wrap; max-width: calc(100% - 10px);
  pointer-events: none; z-index: 2;
}
.cat-dot {
  width: 11px; height: 11px; border-radius: 50%;
  border: 1.5px solid rgba(0,0,0,0.4); box-shadow: 0 1px 4px rgba(0,0,0,0.5);
}
.heart-btn {
  position: absolute; bottom: 5px; right: 5px;
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(10,10,15,0.85); border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; opacity: 0; transform: scale(0.8);
  transition: opacity 0.15s, transform 0.15s; cursor: pointer; z-index: 3;
}
.thumb-card:hover .heart-btn { opacity: 1; transform: scale(1); }
.filename-overlay {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  padding: 18px 6px 5px; font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 10px; color: rgba(255,255,255,0.65);
  opacity: 0; transition: opacity 0.15s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  pointer-events: none; border-radius: 0 0 6px 6px;
}
.thumb-card:hover .filename-overlay { opacity: 1; }

.cat-picker {
  position: absolute; bottom: 36px; right: 0;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 8px; min-width: 160px; z-index: 200;
  box-shadow: 0 8px 32px rgba(0,0,0,0.7); display: none; flex-direction: column; gap: 4px;
}
.cat-picker.open { display: flex; }
.cat-picker-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px; border-radius: 6px; cursor: pointer;
  font-size: 13px; font-weight: 600; transition: background 0.1s; user-select: none;
}
.cat-picker-item:hover { background: var(--surface2); }
.cat-picker-item.selected { background: var(--surface2); }
.cat-picker-item.selected::after { content: '✓'; margin-left: auto; font-size: 11px; opacity: 0.7; }
.cdot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

.empty { grid-column: 1/-1; text-align: center; padding: 80px 20px; color: var(--muted); }
.empty .empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty h3 { font-size: 18px; margin-bottom: 8px; color: var(--text); }

.pagination { display: flex; align-items: center; justify-content: center; gap: 5px; padding: 20px; }
.page-btn {
  width: 34px; height: 34px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface); color: var(--text);
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 12px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.page-btn:hover { background: var(--surface2); }
.page-btn.active { background: #ff4d6d; border-color: #ff4d6d; color: white; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-info { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; color: var(--muted); padding: 0 6px; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.88);
  z-index: 1000; display: none; align-items: center; justify-content: center;
  backdrop-filter: blur(8px);
}
.modal-overlay.open { display: flex; }
.modal {
  position: relative; max-width: min(90vw,1200px); max-height: 90vh;
  display: flex; flex-direction: column;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; overflow: hidden;
  box-shadow: 0 32px 80px rgba(0,0,0,0.8); animation: slideUp 0.2s ease;
}
@keyframes slideUp { from { transform: translateY(16px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.modal-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.modal-filename { flex: 1; font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.modal-counter { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; color: var(--muted); white-space: nowrap; }
.modal-body { flex: 1; display: flex; align-items: center; justify-content: center; padding: 16px; min-height: 0; overflow: hidden; }
.modal-body img { max-width: 100%; max-height: calc(90vh - 130px); object-fit: contain; border-radius: 4px; }
.modal-footer { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border); flex-wrap: wrap; }
.nav-btn {
  width: 34px; height: 34px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--surface2); color: var(--text);
  cursor: pointer; font-size: 15px; display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.nav-btn:hover { border-color: var(--muted); }
.nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.close-btn {
  position: absolute; top: 8px; right: 8px; width: 28px; height: 28px; border-radius: 50%;
  border: 1px solid var(--border); background: var(--surface2); color: var(--text);
  cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center;
  z-index: 10; transition: all 0.15s;
}
.close-btn:hover { background: #ff4d6d; border-color: #ff4d6d; }
.modal-cat-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 12px; border-radius: 20px; border: 1.5px solid;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 12px; font-weight: 700; cursor: pointer; transition: all 0.15s;
}

.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 2000; display: none; align-items: center; justify-content: center; }
.dialog-overlay.open { display: flex; }
.dialog-box {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 24px; width: min(500px, 92vw); box-shadow: 0 24px 60px rgba(0,0,0,0.7);
  max-height: 90vh; overflow-y: auto;
}
.dialog-box h3 { font-size: 16px; margin-bottom: 16px; }
.cat-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.cat-row {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px;
}
.cat-swatch { width: 22px; height: 22px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.15); flex-shrink: 0; }
.cat-row-name { flex: 1; font-weight: 700; font-size: 13px; }
.cat-row-count { font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 11px; color: var(--muted); }
.icon-btn {
  width: 26px; height: 26px; border-radius: 5px; border: 1px solid var(--border);
  background: transparent; color: var(--muted); cursor: pointer; font-size: 13px;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.icon-btn:hover { background: var(--surface); color: var(--text); }
.icon-btn.del:hover { border-color: #ff4444; color: #ff4444; }
.new-cat-form { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.new-cat-form input[type=text] {
  flex: 1; min-width: 100px; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; padding: 8px 12px; color: var(--text);
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 13px; font-weight: 600; outline: none; transition: border-color 0.2s;
}
.new-cat-form input[type=text]:focus { border-color: #ff4d6d; }
.new-cat-form input[type=color] {
  width: 38px; height: 34px; padding: 2px; border: 1px solid var(--border);
  border-radius: 6px; background: var(--surface2); cursor: pointer; outline: none;
}
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }

.export-box { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; width: min(480px, 92vw); box-shadow: 0 24px 60px rgba(0,0,0,0.7); }
.export-box h3 { font-size: 16px; margin-bottom: 8px; }
.export-box p { font-size: 12px; color: var(--muted); margin-bottom: 16px; line-height: 1.5; }
.field-label { font-size: 11px; color: var(--muted); display: block; margin-bottom: 5px; font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }
.export-box input[type=text] {
  width: 100%; background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; padding: 9px 12px; color: var(--text);
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 12px; outline: none; margin-bottom: 14px; transition: border-color 0.2s;
}
.export-box input[type=text]:focus { border-color: #ffd166; }
.cat-select-grid { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.cat-select-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 11px; border-radius: 20px; border: 1.5px solid;
  font-size: 12px; font-weight: 700; cursor: pointer; transition: opacity 0.15s; opacity: 0.4;
}
.cat-select-chip.on { opacity: 1; }
.mode-row { display: flex; gap: 8px; margin-bottom: 14px; }
.mode-opt { flex: 1; padding: 9px; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; text-align: center; font-size: 12px; font-weight: 600; transition: all 0.15s; }
.mode-opt.sel { border-color: #ffd166; color: #ffd166; background: rgba(255,209,102,0.07); }

#toast {
  position: fixed; bottom: 24px; left: 50%;
  transform: translateX(-50%) translateY(70px);
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 8px; padding: 9px 18px; font-size: 13px; font-weight: 600;
  z-index: 3000; transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1); white-space: nowrap; pointer-events: none;
}
#toast.show { transform: translateX(-50%) translateY(0); }
#toast.ok { border-color: #06d6a0; color: #06d6a0; }
#toast.err { border-color: #ff4d6d; color: #ff4d6d; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<header>
  <div class="logo">Meme<span>Vault</span></div>
  <div class="stats" id="stats-text">Loading…</div>
  <div class="header-spacer"></div>
  <div class="search-wrap">
    <span class="search-icon">⌕</span>
    <input type="text" id="search" placeholder="search filenames…" oninput="handleSearch(this.value)">
  </div>
</header>

<div class="toolbar">
  <button class="btn" onclick="openCatManager()">🎨 Categories</button>
  <div class="sep"></div>
  <button class="btn" onclick="markAllVisible()">✓ Mark Visible</button>
  <button class="btn danger" onclick="clearAllMarks()">✕ Clear All</button>
  <div class="sep"></div>
  <button class="btn" style="border-color:#ffd166;color:#ffd166" onclick="openExport()">📁 Export</button>
  <div class="size-control">
    <label>SIZE</label>
    <input type="range" min="100" max="320" value="180" oninput="setThumbSize(this.value)">
  </div>
</div>

<div class="filter-bar" id="filter-bar"></div>
<div class="grid-wrap"><div id="grid"></div></div>
<div class="pagination" id="pagination"></div>

<!-- IMAGE MODAL -->
<div class="modal-overlay" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <button class="close-btn" onclick="closeModal()">✕</button>
    <div class="modal-header">
      <span class="modal-filename" id="modal-filename"></span>
      <span class="modal-counter" id="modal-counter"></span>
    </div>
    <div class="modal-body"><img id="modal-img" src="" alt=""></div>
    <div class="modal-footer">
      <button class="nav-btn" id="btn-prev" onclick="navigate(-1)">←</button>
      <div id="modal-cats" style="display:flex;gap:6px;flex-wrap:wrap;justify-content:center"></div>
      <button class="nav-btn" id="btn-next" onclick="navigate(1)">→</button>
    </div>
  </div>
</div>

<!-- CATEGORY MANAGER -->
<div class="dialog-overlay" id="cat-dialog">
  <div class="dialog-box">
    <h3>🎨 Manage Categories</h3>
    <div class="cat-list" id="cat-list"></div>
    <div class="field-label">ADD NEW CATEGORY</div>
    <div class="new-cat-form">
      <input type="text" id="new-cat-name" placeholder="Category name" maxlength="24"
        onkeydown="if(event.key==='Enter')addCategory()">
      <input type="color" id="new-cat-color" value="#a78bfa">
      <button class="btn" style="border-color:#a78bfa;color:#a78bfa" onclick="addCategory()">+ Add</button>
    </div>
    <div class="dialog-actions">
      <button class="btn" onclick="closeCatManager()">Done</button>
    </div>
  </div>
</div>

<!-- EXPORT DIALOG -->
<div class="dialog-overlay" id="export-dialog">
  <div class="export-box">
    <h3>📁 Export Images</h3>
    <p>Choose which heart categories to include, then pick a destination folder.</p>
    <div class="field-label">CATEGORIES TO INCLUDE</div>
    <div class="cat-select-grid" id="export-cat-grid"></div>
    <div class="field-label">DESTINATION PATH</div>
    <input type="text" id="export-path" placeholder="/Users/you/Desktop/my-memes-export">
    <div class="field-label">MODE</div>
    <div class="mode-row">
      <div class="mode-opt sel" id="mode-copy" onclick="selMode('copy')">📋 Copy</div>
      <div class="mode-opt" id="mode-move" onclick="selMode('move')">✂️ Move</div>
    </div>
    <div id="export-preview" style="font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace;font-size:11px;color:var(--muted);margin-bottom:14px;"></div>
    <div class="dialog-actions">
      <button class="btn" onclick="closeExport()">Cancel</button>
      <button class="btn" style="border-color:#ffd166;color:#ffd166" onclick="runExport()">Export Now</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
const PAGE_SIZE = 120;
let allImages = [], filteredImages = [];
let categories = [], marks = {};
let currentFilter = 'all', searchQuery = '';
let currentPage = 1, modalIndex = -1;
let exportMode = 'copy', exportSelectedCats = new Set();
let openPickerImg = null;

async function init() {
  const [ir, dr] = await Promise.all([fetch('/api/images'), fetch('/api/data')]);
  allImages = await ir.json();
  const d = await dr.json();
  categories = d.categories;
  marks = d.marks;
  renderFilterBar();
  applyFilters();
  updateStats();
}

function updateStats() {
  const total = Object.keys(marks).length;
  document.getElementById('stats-text').innerHTML =
    '<b>' + allImages.length + '</b> images &nbsp;·&nbsp; <b>' + total + '</b> marked';
}

function renderFilterBar() {
  const counts = { all: 0 };
  categories.forEach(c => counts[c.id] = 0);
  Object.values(marks).forEach(cats => {
    if (cats && cats.length) {
      counts.all++;
      cats.forEach(cid => { if (counts[cid] !== undefined) counts[cid]++; });
    }
  });

  const tab = (filter, label, color) => {
    const isActive = currentFilter === filter;
    const style = isActive ? 'border-color:' + color + ';background:' + color + '22' : '';
    return '<div class="filter-tab" style="' + style + '" onclick="setFilter(\'' + filter + '\')">' + label + '</div>';
  };

  let html = tab('all', '🖼 All <span class="filter-count">(' + allImages.length + ')</span>', '#ff4d6d');
  html += tab('marked', '❤ Any Mark <span class="filter-count">(' + counts.all + ')</span>', '#ff4d6d');
  categories.forEach(c => {
    const isActive = currentFilter === c.id;
    const style = isActive ? 'border-color:' + c.color + ';background:' + c.color + '22' : '';
    html += '<div class="filter-tab" style="' + style + '" onclick="setFilter(\'' + c.id + '\')">'
      + '<span class="dot" style="background:' + c.color + '"></span>'
      + c.name + ' <span class="filter-count">(' + (counts[c.id] || 0) + ')</span></div>';
  });
  document.getElementById('filter-bar').innerHTML = html;
}

function setFilter(f) { currentFilter = f; currentPage = 1; renderFilterBar(); applyFilters(); }
function handleSearch(q) { searchQuery = q.toLowerCase(); currentPage = 1; applyFilters(); }

function applyFilters() {
  filteredImages = allImages.filter(img => {
    const imgCats = marks[img] || [];
    let mf = true;
    if (currentFilter === 'marked') mf = imgCats.length > 0;
    else if (currentFilter !== 'all') mf = imgCats.includes(currentFilter);
    return mf && (!searchQuery || img.toLowerCase().includes(searchQuery));
  });
  renderPage();
  renderPagination();
}

function renderPage() {
  const grid = document.getElementById('grid');
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageImages = filteredImages.slice(start, start + PAGE_SIZE);

  if (!pageImages.length) {
    grid.innerHTML = '<div class="empty"><div class="empty-icon">' +
      (currentFilter !== 'all' ? '💔' : '🖼') + '</div><h3>' +
      (currentFilter !== 'all' ? 'Nothing here yet' : 'No images found') + '</h3></div>';
    return;
  }

  grid.innerHTML = pageImages.map((img, i) => {
    const imgCats = marks[img] || [];
    const dots = imgCats.map(cid => {
      const c = categories.find(x => x.id === cid);
      return c ? '<span class="cat-dot" style="background:' + c.color + '" title="' + c.name + '"></span>' : '';
    }).join('');
    const safeImg = img.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    return '<div class="thumb-card" onclick="handleCardClick(event,\'' + safeImg + '\',' + (start+i) + ')">'
      + '<div class="img-wrap">'
      + '<img src="/img/' + encodeURIComponent(img) + '" alt="" loading="lazy" class="loading" onload="this.classList.replace(\'loading\',\'loaded\')" onerror="this.style.display=\'none\'">'
      + '<div class="cat-dots">' + dots + '</div>'
      + '<div class="filename-overlay">' + img + '</div>'
      + '</div>'
      + '<div class="heart-btn" onclick="event.stopPropagation();togglePicker(event,\'' + safeImg + '\')">♥</div>'
      + '<div class="cat-picker" id="picker-' + i + '">' + renderPickerHTML(img) + '</div>'
      + '</div>';
  }).join('');

  // store page offset for picker lookup
  renderPage._start = start;
  renderPage._pageImages = pageImages;
}
renderPage._start = 0;
renderPage._pageImages = [];

function renderPickerHTML(img) {
  const imgCats = marks[img] || [];
  return categories.map(c => {
    const safeImg = img.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    return '<div class="cat-picker-item ' + (imgCats.includes(c.id) ? 'selected' : '') + '" onclick="event.stopPropagation();toggleCat(\'' + safeImg + '\',\'' + c.id + '\')">'
      + '<span class="cdot" style="background:' + c.color + '"></span>' + c.name + '</div>';
  }).join('');
}

function handleCardClick(e, img, idx) {
  if (openPickerImg) { closePicker(); return; }
  openModal(idx);
}

function togglePicker(e, img) {
  const pageImages = renderPage._pageImages;
  const localIdx = pageImages.indexOf(img);
  if (localIdx === -1) return;
  const pickerId = 'picker-' + localIdx;
  const picker = document.getElementById(pickerId);
  if (!picker) return;

  if (openPickerImg === img) { closePicker(); return; }
  if (openPickerImg) closePicker();

  picker.innerHTML = renderPickerHTML(img);
  picker.classList.add('open');
  openPickerImg = img;
  setTimeout(() => document.addEventListener('click', outsideClick, { once: true }), 0);
}

function outsideClick() { closePicker(); }
function closePicker() {
  if (!openPickerImg) return;
  const pageImages = renderPage._pageImages;
  const localIdx = pageImages.indexOf(openPickerImg);
  const picker = document.getElementById('picker-' + localIdx);
  if (picker) picker.classList.remove('open');
  openPickerImg = null;
}

async function toggleCat(img, catId) {
  let imgCats = marks[img] ? [...marks[img]] : [];
  if (imgCats.includes(catId)) imgCats = imgCats.filter(c => c !== catId);
  else imgCats.push(catId);
  if (!imgCats.length) delete marks[img]; else marks[img] = imgCats;

  // refresh picker
  const pageImages = renderPage._pageImages;
  const localIdx = pageImages.indexOf(img);
  const picker = document.getElementById('picker-' + localIdx);
  if (picker) picker.innerHTML = renderPickerHTML(img);

  // refresh dots
  const card = picker ? picker.parentElement : null;
  if (card) {
    const dotsEl = card.querySelector('.cat-dots');
    if (dotsEl) {
      dotsEl.innerHTML = (marks[img] || []).map(cid => {
        const c = categories.find(x => x.id === cid);
        return c ? '<span class="cat-dot" style="background:' + c.color + '" title="' + c.name + '"></span>' : '';
      }).join('');
    }
  }

  updateStats(); renderFilterBar();
  if (currentFilter !== 'all' && currentFilter !== 'marked') applyFilters();

  await fetch('/api/mark', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ filename: img, cats: marks[img] || [] })
  });
}

// MODAL
function openModal(idx) { modalIndex = idx; renderModal(); document.getElementById('modal').classList.add('open'); }
function closeModal() { document.getElementById('modal').classList.remove('open'); }
function navigate(d) { modalIndex = Math.max(0, Math.min(filteredImages.length-1, modalIndex+d)); renderModal(); }

function renderModal() {
  const img = filteredImages[modalIndex];
  if (!img) return;
  document.getElementById('modal-img').src = '/img/' + encodeURIComponent(img);
  document.getElementById('modal-filename').textContent = img;
  document.getElementById('modal-counter').textContent = (modalIndex+1) + ' / ' + filteredImages.length;
  document.getElementById('btn-prev').disabled = modalIndex === 0;
  document.getElementById('btn-next').disabled = modalIndex === filteredImages.length - 1;

  const imgCats = marks[img] || [];
  document.getElementById('modal-cats').innerHTML = categories.map(c => {
    const on = imgCats.includes(c.id);
    const safeImg = img.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
    return '<button class="modal-cat-btn" style="border-color:' + c.color + ';color:' + (on?'#000':c.color) + ';background:' + (on?c.color:'transparent') + '" onclick="toggleCatModal(\'' + safeImg + '\',\'' + c.id + '\')">'
      + (on ? '✓ ' : '+ ') + c.name + '</button>';
  }).join('');
}

async function toggleCatModal(img, catId) { await toggleCat(img, catId); renderModal(); }

document.addEventListener('keydown', e => {
  if (document.getElementById('modal').classList.contains('open')) {
    if (e.key==='ArrowLeft') navigate(-1);
    if (e.key==='ArrowRight') navigate(1);
    if (e.key==='Escape') closeModal();
  } else if (e.key==='Escape') closePicker();
});

function setThumbSize(v) { document.getElementById('grid').style.gridTemplateColumns = 'repeat(auto-fill,minmax(' + v + 'px,1fr))'; }

async function markAllVisible() {
  if (!categories.length) { toast('Create a category first!', 'err'); return; }
  const catId = categories[0].id;
  const start = (currentPage - 1) * PAGE_SIZE;
  const page = filteredImages.slice(start, start + PAGE_SIZE);
  page.forEach(img => { if (!marks[img]) marks[img] = []; if (!marks[img].includes(catId)) marks[img].push(catId); });
  await fetch('/api/marks/batch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({marks})});
  renderPage(); updateStats(); renderFilterBar();
  toast('✓ Marked ' + page.length + ' as "' + categories[0].name + '"', 'ok');
}

async function clearAllMarks() {
  if (!confirm('Clear ALL marks from ALL images?')) return;
  marks = {};
  await fetch('/api/marks/batch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({marks})});
  applyFilters(); updateStats(); renderFilterBar();
  toast('✕ All marks cleared', 'err');
}

// CATEGORY MANAGER
function openCatManager() { renderCatList(); document.getElementById('cat-dialog').classList.add('open'); }
function closeCatManager() { document.getElementById('cat-dialog').classList.remove('open'); renderFilterBar(); renderPage(); }

function renderCatList() {
  const counts = {};
  categories.forEach(c => counts[c.id] = 0);
  Object.values(marks).forEach(cats => (cats||[]).forEach(cid => { if(counts[cid]!==undefined) counts[cid]++; }));
  const list = document.getElementById('cat-list');
  if (!categories.length) { list.innerHTML = '<div style="font-size:12px;color:var(--muted);padding:8px">No categories yet.</div>'; return; }
  list.innerHTML = categories.map(c =>
    '<div class="cat-row"><div class="cat-swatch" style="background:' + c.color + '"></div>'
    + '<div class="cat-row-name">' + c.name + '</div>'
    + '<div class="cat-row-count">' + (counts[c.id]||0) + ' imgs</div>'
    + '<button class="icon-btn del" onclick="deleteCategory(\'' + c.id + '\')" title="Delete">✕</button></div>'
  ).join('');
}

async function addCategory() {
  const name = document.getElementById('new-cat-name').value.trim();
  const color = document.getElementById('new-cat-color').value;
  if (!name) { toast('Enter a name', 'err'); return; }
  const id = name.toLowerCase().replace(/[^a-z0-9]/g, '_') + '_' + Date.now();
  categories.push({ id, name, color });
  await fetch('/api/categories', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({categories})});
  document.getElementById('new-cat-name').value = '';
  renderCatList();
  toast('✓ Added "' + name + '"', 'ok');
}

async function deleteCategory(catId) {
  const c = categories.find(x => x.id === catId);
  const count = Object.values(marks).filter(cats => (cats||[]).includes(catId)).length;
  if (!confirm('Delete "' + c.name + '"? Removes it from ' + count + ' image(s).')) return;
  categories = categories.filter(x => x.id !== catId);
  Object.keys(marks).forEach(img => {
    marks[img] = (marks[img]||[]).filter(x => x !== catId);
    if (!marks[img].length) delete marks[img];
  });
  await fetch('/api/categories', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({categories})});
  await fetch('/api/marks/batch', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({marks})});
  renderCatList();
  toast('Deleted "' + c.name + '"', 'err');
}

// EXPORT
function openExport() {
  exportSelectedCats = new Set(categories.map(c => c.id));
  document.getElementById('export-cat-grid').innerHTML = categories.map(c =>
    '<div class="cat-select-chip on" id="echip-' + c.id + '" style="border-color:' + c.color + ';color:' + c.color + '" onclick="toggleExportCat(\'' + c.id + '\')">'
    + '<span style="background:' + c.color + ';width:8px;height:8px;border-radius:50%;display:inline-block"></span> ' + c.name + '</div>'
  ).join('');
  updateExportPreview();
  document.getElementById('export-dialog').classList.add('open');
}
function closeExport() { document.getElementById('export-dialog').classList.remove('open'); }

function toggleExportCat(catId) {
  if (exportSelectedCats.has(catId)) exportSelectedCats.delete(catId); else exportSelectedCats.add(catId);
  const chip = document.getElementById('echip-' + catId);
  if (chip) chip.classList.toggle('on', exportSelectedCats.has(catId));
  updateExportPreview();
}

function updateExportPreview() {
  const count = Object.keys(marks).filter(img => (marks[img]||[]).some(cid => exportSelectedCats.has(cid))).length;
  document.getElementById('export-preview').textContent = count + ' image(s) will be exported';
}

function selMode(m) {
  exportMode = m;
  document.getElementById('mode-copy').classList.toggle('sel', m==='copy');
  document.getElementById('mode-move').classList.toggle('sel', m==='move');
}

async function runExport() {
  const dest = document.getElementById('export-path').value.trim();
  if (!dest) { toast('Enter a destination path', 'err'); return; }
  const files = Object.keys(marks).filter(img => (marks[img]||[]).some(cid => exportSelectedCats.has(cid)));
  if (!files.length) { toast('No images match selected categories', 'err'); return; }
  const res = await fetch('/api/export', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ dest, mode: exportMode, files })
  });
  const data = await res.json();
  if (data.success) {
    toast('✓ Exported ' + data.count + ' images', 'ok');
    closeExport();
    if (exportMode === 'move') { marks = {}; await init(); }
  } else {
    toast('Error: ' + data.error, 'err');
  }
}

// PAGINATION
function renderPagination() {
  const total = Math.ceil(filteredImages.length / PAGE_SIZE);
  const pag = document.getElementById('pagination');
  if (total <= 1) { pag.innerHTML = ''; return; }
  const getRange = (cur, tot) => {
    const s = new Set([1, tot]);
    for (let i=Math.max(2,cur-2); i<=Math.min(tot-1,cur+2); i++) s.add(i);
    return [...s].sort((a,b)=>a-b);
  };
  let h = '<button class="page-btn" onclick="goPage(' + (currentPage-1) + ')" ' + (currentPage===1?'disabled':'') + '>‹</button>';
  let prev = null;
  for (const p of getRange(currentPage, total)) {
    if (prev !== null && p-prev > 1) h += '<span class="page-info">…</span>';
    h += '<button class="page-btn ' + (p===currentPage?'active':'') + '" onclick="goPage(' + p + ')">' + p + '</button>';
    prev = p;
  }
  h += '<button class="page-btn" onclick="goPage(' + (currentPage+1) + ')" ' + (currentPage===total?'disabled':'') + '>›</button>';
  h += '<span class="page-info">' + filteredImages.length + ' images</span>';
  pag.innerHTML = h;
}

function goPage(p) {
  const total = Math.ceil(filteredImages.length / PAGE_SIZE);
  if (p<1||p>total) return;
  currentPage = p; renderPage(); renderPagination();
  window.scrollTo({top:0,behavior:'smooth'});
}

function toast(msg, type='') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}

init();
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/img/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

@app.route('/api/images')
def api_images():
    return jsonify(IMAGES)

@app.route('/api/data')
def api_data():
    return jsonify({'categories': DATA['categories'], 'marks': DATA['marks']})

@app.route('/api/mark', methods=['POST'])
def api_mark():
    d = request.get_json()
    filename = d.get('filename')
    cats = d.get('cats', [])
    if filename:
        if cats:
            DATA['marks'][filename] = cats
        else:
            DATA['marks'].pop(filename, None)
        save_data()
    return jsonify({'ok': True})

@app.route('/api/marks/batch', methods=['POST'])
def api_batch():
    d = request.get_json()
    DATA['marks'] = {k: v for k, v in d.get('marks', {}).items() if v}
    save_data()
    return jsonify({'ok': True})

@app.route('/api/categories', methods=['POST'])
def api_categories():
    DATA['categories'] = request.get_json().get('categories', [])
    save_data()
    return jsonify({'ok': True})

def resolve_in_folder(filename):
    """Return the absolute path of a listed image, or None if the name is not
    one the app itself listed or would resolve outside the image folder."""
    if not isinstance(filename, str) or filename not in IMAGES:
        return None
    root = Path(IMAGE_FOLDER).resolve()
    src = (root / filename).resolve()
    try:
        src.relative_to(root)
    except ValueError:
        return None
    return src

@app.route('/api/export', methods=['POST'])
def api_export():
    d = request.get_json() or {}
    dest_raw = str(d.get('dest', '')).strip()
    mode = d.get('mode', 'copy')
    files = d.get('files', [])
    if not dest_raw or mode not in ('copy', 'move') or not isinstance(files, list):
        return jsonify({'success': False, 'error': 'Bad export request'})
    dest = Path(dest_raw).expanduser()
    try:
        dest.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    count = 0
    for filename in files:
        src = resolve_in_folder(filename)
        if src is None or not src.is_file():
            continue
        try:
            if mode == 'move':
                shutil.move(str(src), str(dest / filename))
                if filename in IMAGES:
                    IMAGES.remove(filename)
            else:
                shutil.copy2(str(src), str(dest / filename))
            count += 1
        except Exception:
            pass
    save_data()
    return jsonify({'success': True, 'count': count})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MemeVault')
    parser.add_argument('--folder', '-f', required=True, help='Path to images folder')
    parser.add_argument('--port', '-p', type=int, default=5000)
    args = parser.parse_args()

    IMAGE_FOLDER = os.path.abspath(args.folder)
    if not os.path.isdir(IMAGE_FOLDER):
        print(f"❌ Error: '{IMAGE_FOLDER}' is not a valid directory")
        sys.exit(1)

    DATA_FILE = os.path.join(IMAGE_FOLDER, '.memevault_data.json')
    load_images()
    load_data()

    print(f"\n🎮 MemeVault running!")
    print(f"   Folder : {IMAGE_FOLDER}")
    print(f"   Data   : {DATA_FILE}")
    print(f"   Open   : http://localhost:{args.port}\n")

    app.run(debug=False, port=args.port, host='127.0.0.1')
