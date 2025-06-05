# 📚 Kindle Highlights Viewer

A simple, elegant tool to explore your Kindle highlights — either through a web app or on your local machine.

---

## 🌐 Use the App Online (No Setup Needed)

The easiest way to use this tool is through the live Streamlit web app:

👉 **[Launch the App](https://your-streamlit-app-url.streamlit.app/)**

### How it works:
1. Export your Kindle highlights (`My Clippings.txt`) from your device.
2. Upload the file into the app.
3. Browse random quotes, search by title, or view all your books!

---

🔍 Features

🎲 Random highlight browser with full context
📖 View all highlights from a selected book
📚 See a full list of books (with title, author, and year read)
🔎 (Optional) Filter keywords to exclude certain books from random selection

### Using Your Highlights
Copy the My Clippings.txt file from your Kindle (usually in the Kindle Documents folder).
When prompted by the app, upload the file.

💬 Questions?


## 🖥️ Run Locally (For Developers or Offline Use)

### Requirements
- Python 3.8+
- `pandas`, `numpy`, `streamlit`, `watchdog`

### Option A: Conda Environment
`bash
conda env create -f environment.yml
conda activate streamlit
`

### Option B: pip
``pip install -r requirements.txt``

### Launch the App
``streamlit run kindle_prototype.py``


---


