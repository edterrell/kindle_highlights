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

## 🖥️ Run Locally (For Developers or Offline Use)

### Requirements
- Python 3.8+
- `pandas`, `numpy`, `streamlit`, `watchdog`

### Option A: Conda Environment
```bash
conda env create -f environment.yml
conda activate streamlit
