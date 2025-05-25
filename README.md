# Kindle Highlights CLI Tool

This script creates a random highlight from your Kindle's "My Clippings.txt" file.


## Setup

1. Make sure you have Python 3.8+ installed.
2. Install dependencies: pip install -r requirements.txt. The dependencies are pandas and numpy
3. Run the script: python kindle.py
4. Copy the 'My Clippings.txt' to your desktop. (See Note below). 

## Features

- View a random highlight and its context.
- View all highlights from a selected book
- View all book titles you've read. The "show all titles' provides a list of title, author, and year read (year of the first highlight)

- (Optional) Filter out keywords to exclude certain titles from the random highlight.

## Note

Your Kindle highlights file is usually named `My Clippings.txt` and can be found in the
Kindle device's Documents folder when connected via USB.
