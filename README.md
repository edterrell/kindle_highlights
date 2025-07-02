# 📚 Kindle Highlights Viewer

A simple, elegant tool to explore your Kindle highlights — either through a web app or on your local machine.

---

## 🌐 Use the App Online (No Setup Needed)

The easiest way to use this tool is through the live Streamlit web app:

👉 **[Launch the App](https://kindle.streamlit.app)**

### How it works:
1. Export your Kindle highlights (`My Clippings.txt`) from your device.
2. Upload the file into the app.
3. Browse random quotes, search by title/author, or view all your books!
4. Full text search and an ad-free viewing experience

---

## 🔍 Features

#### 	🎲 Random highlight browser with local context
#### 	📖 View all highlights from a selected book
#### 	📚 See a complete list of your books (with title, author, and year read)
####  🔍 Full text search

---

### Using Your Highlights
Connect your Kindle to your computer via USB. Copy the My Clippings.txt file from your Kindle (usually in it's "documents" folder). It may convenient to upload it to your desktop for easy retrieval later. When prompted by the app, upload the file.

### 💬 Questions?
Feel free to open an issue or reach out via GitHub.

---
### 🖥️ Run Locally (For Developers or Offline Use)
#### Requirements
- Python 3.8+
- `pandas`, `numpy`, `streamlit`, `watchdog`

#### Option A: Conda Environment
`bash
conda env create -f environment.yml
conda activate streamlit
`
#### Option B: pip
``pip install -r requirements.txt``

#### Launch the App
``streamlit run kindle_prototype.py``


---


