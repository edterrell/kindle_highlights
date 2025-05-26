# Kindle Highlights CLI Tool

This script creates a random highlight from your Kindle's "My Clippings.txt" file.


## Setup

1. **Make sure you have Python 3.8+ installed.**

2. **(Option A) Create a new environment using conda:**

   conda env create -f environment.yml
   conda activate streamlit
   
3. **(Option B) Install dependencies (if not using environment.yml)**
   Required packages: pandas, numpy, streamlit and watchdog

   pip install -r requirements.txt

5. Run the app:
   streamlit run kindle_prototype.py
   
6. Prepare your Kindle highlights:
Copy the My Clippings.txt file from your Kindle to your desktop.
When prompted, drag and drop this file into the app.



## Features

- View a random highlight and its context.
- View all highlights from a selected book
- View all book titles you've read. The "show all titles' provides a list of title, author, and year read (year of the first highlight)

- (Optional) Filter out keywords to exclude certain titles from the random highlight.

## Note

Your Kindle highlights file is usually named `My Clippings.txt` and can be found in the
Kindle device's Documents folder when connected via USB.
