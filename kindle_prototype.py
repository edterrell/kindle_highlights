#!/usr/bin/env python
# coding: utf-8


#import csv
#import numpy as np
import pandas as pd
import re
from pathlib import Path
import textwrap
import streamlit as st
from io import StringIO
import tempfile
from numpy.random import default_rng
rng = default_rng()

# Get highlights directly from 'My Clippings.txt'

def clean_text(text):
    """Remove BOM and unwanted whitespace/control characters."""
    if text is None:
        return text
    # Remove BOM (zero-width no-break space)
    text = text.replace('\ufeff', '')
    # Remove brackets with ref numbers
    text = re.sub(r'\[\d+\]', '', text)
    # Strip leading/trailing whitespace including newlines
    text = text.strip()
    return text

def parse_kindle_highlights(filepath):
    with open(filepath, 'r', encoding='utf-8-sig') as file:
        lines = [clean_text(line) for line in file if clean_text(line)]
    highlights = []
    current_title = None
    current_metadata = None
    current_text_lines = []

    for line in lines:
        if line == "==========":
            if current_title and current_metadata and current_text_lines:
                highlight_text = ' '.join(current_text_lines).strip()
                highlights.append({
                    'title': clean_text(current_title),
                    'metadata': clean_text(current_metadata),
                    'highlight': highlight_text
                })
            # Reset
            current_title = None
            current_metadata = None
            current_text_lines = []
            continue
        if not current_title:
            current_title = line
        elif not current_metadata and line.startswith("- Your Highlight"):
            current_metadata = line
        elif current_metadata:
            current_text_lines.append(line)

    # Build DataFrame
    df = pd.DataFrame(highlights)
    # Extract location and added_on
    if not df.empty:
        df[['location', 'added_on']] = df['metadata'].str.extract(
            r'Location ([\d\-]+) \| Added on (.+)'
        )
        df['location']  = df['location'].apply(clean_text)
        df['added_on']  = df['added_on'].apply(clean_text)
        df['title']     = df['title'].apply(clean_text)
        df['highlight'] = df['highlight'].apply(clean_text)
    return df[['title', 'location', 'added_on', 'highlight']]


# Get context (lines above and below with same title)
def get_context(df, index):
    try:
        current_row = df.loc[index]
    except KeyError:
        return {
            'title': None,
            'above': None,
            'current': None,
            'below': None
        }
    title = current_row['title']
    same_title_df = df[df['title'] == title]

    if index not in same_title_df.index:
        return {
            'title': title,
            'above': None,
            'current': current_row['highlight'],
            'below': None
        }
    locs = same_title_df.index.tolist()
    i = locs.index(index)
    above = same_title_df.loc[locs[i - 1]]['highlight'] if i > 0 else None
    below = same_title_df.loc[locs[i + 1]]['highlight'] if i < len(locs) - 1 else None
    current = same_title_df.loc[index]['highlight']
    return {
        'title': title,
        'above': above,
        'current': current,
        'below': below
    }

# Exclusion list
def get_random_highlight_excluding(df, exclude_keywords):
    # Create a mask to exclude titles containing any of the keywords (case-insensitive)
    # ~ inverts the boolean series (everything except the keywords)
    mask = ~df['title'].str.contains('|'.join(exclude_keywords), case=False, na=False)
    filtered_df = df[mask]  # Apply the mask to get the filtered DataFrame
    
    # If no titles remain after filtering, raise an error
    if filtered_df.empty:
        raise ValueError("No titles remaining after exclusions.")
    
    # df.sample is a function that returns 1 row from the df
    # row selection uses default_rng for consistent randomness but can be replaced (e.g. 42 for testing)
    random_row = filtered_df.sample(n=1, random_state=rng.integers(1_000_000))
    
    # Return the row itself and its original index in the full DataFrame
    return random_row.iloc[0], random_row.index[0]


# show all highlights for a specific title
def show_highlights_for_title(df):
    keyword = input("Enter the title or author name. Return generates a list: ").strip().lower()

    # Create a cleaned version of the title column
    df = df.copy()
    df['clean_title'] = df['title'].fillna('').apply(lambda t: t.replace('\ufeff', '').strip().lower())

    # Find titles that contain the keyword
    matched_rows = df[df['clean_title'].str.contains(keyword)]
    matched_titles = matched_rows['title'].unique()

    if len(matched_titles) == 0:
        print(f"No titles found containing '{keyword}'.")
        return

    if len(matched_titles) == 1:
        selected_title = matched_titles[0]
        print(f"\nShowing highlights for: {selected_title}\n")
    else:
        print("\nMultiple titles found:")
        for i, title in enumerate(matched_titles):
            print(f"{i}: {title}")
        
        try:
            selection = int(input("\nEnter the number of the title you want: "))
            selected_title = matched_titles[selection]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

    # Show highlights using original title
    print()
    print(selected_title)
    matches = df[df['title'] == selected_title]
    for i, row in matches.iterrows():
        wrapped(f"[{i}]", row['highlight'])
        print('-' * 40)

    # Prompt user to export
    export = input(f"\nExport highlights as csv? (y/n): ").strip().lower()
    if export == 'y':
        # Sanitize title: remove special characters, replace spaces with underscores, limit to 40 chars
        safe_title = re.sub(r'[\\/*?:"<>|(),]', "", selected_title)   # Remove invalid characters
        safe_title = safe_title.replace(" ", "_")[:40]             # Replace spaces and limit length
        filename = f"{safe_title}.txt"
    
        with open(filename, "w", encoding="utf-8") as f:
            for i, row in matches.iterrows():
                f.write(f"[{i}] {row['highlight']}\n{'-'*40}\n")

        print(f"\n✅ Highlights exported to: {filename}")

# helper function for small screens
def wrapped_streamlit(label, text, width=70):
    wrapped_text = textwrap.fill(text, width=width)
    st.markdown(f"**{label}:**")
    st.code(wrapped_text)

# show surrounding context for a highlight
def context(df, random_index):
    try:
        result = get_context(df, random_index)
        
        st.subheader("Context View")
        st.markdown(f"**Title:** {result['title']}")

        wrapped_streamlit("Above highlight", result['above'])
        wrapped_streamlit("Current highlight", result['current'])
        wrapped_streamlit("Below highlight", result['below'])

    except ValueError as e:
        st.error(f"Error: {e}")


def setup_summary(df):
    # Kindle Summary of all titles and authors
    kindle_sum = pd.DataFrame()
    
    # Split into title and author columns using regex
    kindle_sum[['Title', 'Author']] = df['title'].str.extract(r'^(.*)\s\(([^()]+)\)$').copy()
    
    # Extract only the year using regex
    kindle_sum ['Year Read'] = df.added_on.str.extract(r'\b(\d{4})\b').copy()
    #breakpoint()
    return kindle_sum

def process_kindle_sum(kindle_sum):
    import io

    kindle_sum = kindle_sum.copy()

    # --- Clean and prep ---
    kindle_sum = kindle_sum.drop_duplicates("Title", keep='first')
    kindle_sum['Title'] = kindle_sum['Title'].str.replace(r'\s*\([^)]*\)|[\(\)]', '', regex=True).str.strip()
    kindle_sum['Author'] = kindle_sum['Author'].astype(str).str.strip()
    kindle_sum['Year Read'] = kindle_sum['Year Read'].astype(str).str.strip()

    # --- Sort selection ---
    st.subheader("📚 All Books")

    
    kindle_sum = kindle_sum.reset_index(drop=True)
    filtered_df = kindle_sum.copy()
    
    # --- Book Count ---
    st.markdown(f"**Total Books Displayed: {len(filtered_df)}**")

    # --- Display Table ---
    st.dataframe(filtered_df, use_container_width=True)

    # --- Download Button ---
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv_buffer.getvalue(),
        file_name="kindle_books_filtered.csv",
        mime="text/csv"
    )

# Begin execution
def main():

    st.title("Kindle Highlights Viewer")
    uploaded_file = st.file_uploader(
        "Upload your 'My Clippings.txt' file", 
        type=["txt"],
        key="file_upload_main"
    )

    if uploaded_file is not None and 'df' not in st.session_state:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name
    
        # Optional: read first few lines for debugging
        with open(tmp_path, encoding="utf-8") as f:
            sample = ''.join([next(f) for _ in range(10)])
        st.text("Sample of uploaded file:")
        st.code(sample)
        
        df = parse_kindle_highlights(tmp_path)
        #st.dataframe(df)

        df.sort_values('added_on',inplace=True)
        kindle_sum = setup_summary(df)

        # Drop clip limit messages and duplicates with same location values
        clip_message = "You have reached the clipping limit for this item"
        df = df[~df['highlight'].str.contains(clip_message, na=False)]
        df = df.drop_duplicates(subset=['title', 'location'])

        # Get random title - highlight (excludes keywords)
        # Modify this list to add or change titles to be excluded 
        exclude_keywords = ["Reggie", "Bicycling"]

        
        try:
            row, random_index = get_random_highlight_excluding(df, exclude_keywords)
        except ValueError as e:
            st.error(f"Error: {e}")
            return

        title = row['title']
        text = row['highlight']
        cleaned_highlight = re.sub(r"\.\s*\d+", ".", text)
        # Store in session state
        st.session_state.title = title
        st.session_state.cleaned_highlight = cleaned_highlight


        # Store in session state
        st.session_state.df = df
        st.session_state.random_index = random_index
        st.session_state.kindle_sum = kindle_sum
        st.success("Highlights loaded successfully!")


if __name__ == "__main__":
    main()

    if 'df' in st.session_state:
        df = st.session_state.df
        random_index = st.session_state.random_index
        kindle_sum = st.session_state.kindle_sum

    if 'title' in st.session_state and 'cleaned_highlight' in st.session_state:
        st.subheader("Random Highlight")
        st.markdown(f"**{st.session_state.title}**")
        st.code(textwrap.fill(st.session_state.cleaned_highlight, width=80))


        action = st.radio(
            "What would you like to do next?",
            ("Get context", "Show highlights for a specific title", "Show all titles")
        )
        if st.button("Run selected action"):
            if action == "Get context":
                context(df, random_index)
            elif action == "Show highlights for a specific title":
                show_highlights_for_title(df)
            elif action == "Show all titles":
                process_kindle_sum(kindle_sum)



        #st.markdown("---")
        #if st.button("Exit App"):
        #    st.success("Goodbye!")  # symbolic; can't really "exit" in Streamlit
    

