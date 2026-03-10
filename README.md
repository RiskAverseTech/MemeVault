# 🗂 MemeVault

**A local-first image browser and curation tool — no cloud, no uploads, your files stay yours.**

MemeVault is a lightweight Python app that runs entirely on your computer. Point it at any folder of images, tag them with custom color-coded categories, and export exactly the ones you want. Built for meme collectors, Discord hoarders, and anyone who has ever had a folder called `memes_final_v3`.

> Open source by [Risk Averse Technology Company](https://github.com/riskaversetechnology) · Built for the [Create a Meme](https://www.createa.meme) community

---

## ✨ Features

- **Thumbnail grid browser** — lazy-loads thousands of images without slowing down
- **Custom heart categories** — create as many as you want, each with its own name and color
- **Multi-category tagging** — one image can belong to multiple categories at once
- **Filter by category** — instantly see only the images tagged a certain way
- **Filename search** — filter by name in real time
- **Click to zoom** — any image opens in a full modal with prev/next navigation and keyboard shortcuts
- **Export marked images** — pick which categories to export, choose a destination folder, copy or move
- **Persistent marks** — everything saves to a `.memevault_data.json` file in your images folder automatically
- **Zero data leaves your machine** — runs on `localhost:5000`, nothing is uploaded anywhere

---

## 🚀 Quick Start

**Requirements:** Python 3.8+ · Flask

```bash
# 1. Install Flask (one time)
python -m pip install flask

# 2. Run MemeVault pointed at your images folder
python meme_vault.py --folder /path/to/your/images

# 3. Open in your browser
# → http://localhost:5000
```

On Mac you can drag your images folder from Finder into the terminal after `--folder ` to auto-fill the path.

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
git clone https://github.com/riskaversetechnology/MemeVault.git
cd MemeVault
python -m pip install flask
python meme_vault.py --folder /your/images/folder
```

---

## 🤝 Contributing

PRs welcome. This is intentionally kept simple — one Python file, one HTML template, no build tools. If you're adding a feature, keep it local-first and dependency-light.

---

## 📄 License

MIT — do whatever you want with it.

---

## 🏢 About

MemeVault is an open source project by [Risk Averse Technology Company](https://riskaverse.tech) (RATC), an AI product studio.

Other RATC open source projects: [see our GitHub](https://github.com/riskaversetechnology)

A [Create a Meme](https://www.createa.meme) open source project for the memer community.
