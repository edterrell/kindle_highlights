#!/usr/bin/env python
# coding: utf-8
# Usage: streamlit run kindle_prototype.py
# Comments: see README.md

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

# Get Random highlight excluding
def get_random_highlight_excluding(df, exclude_keywords):
    # Create a mask to exclude titles containing any of the keywords (case-insensitive)
    # ~ inverts the boolean series (everything except the keywords)
    mask = ~df['title'].str.contains('|'.join(exclude_keywords), case=False, na=False)
    filtered_df = df[mask]  # Apply the mask to get the filtered DataFrame
    
    # If no titles remain after filtering, raise an error
    if filtered_df.empty:
        raise ValueError("No titles remaining after exclusions.")
    
    # df.sample is a function that returns 1 row from the df
    # row selection uses default_rng for consistent randomness but can be replaced (e.g. random_state=42 for testing)
    random_row = filtered_df.sample(n=1, random_state=rng.integers(1_000_000))
    
    # Return the row itself and its original index in the full DataFrame
    return random_row.iloc[0], random_row.index[0]

# show all highlights for a specific title
def show_highlights_for_title():
    df = st.session_state.get("df")
    if df is None:
        st.warning("No data loaded.")
        return

    unique_titles = sorted(df['title'].dropna().unique())

    filtered_titles = [title for title in unique_titles]

    placeholder = "Select a title..."
    options_with_placeholder = [placeholder] + filtered_titles

    selected_title = st.selectbox(
        "Search titles or select:",
        options=options_with_placeholder,
        index=0,
        key="title_select"
    )
    
    # Ignore the placeholder if selected
    if selected_title == placeholder:
        return

    if selected_title:
        st.subheader(f"{selected_title}")
        highlights_text = f"Highlights from: {selected_title}\n\n"
        filtered = df[df['title'] == selected_title]

        if filtered.empty:
            st.info("No highlights found for this title.")
            return
    
        for _, row in filtered.iterrows():
            highlight = row['highlight']
            cleaned = re.sub(r"\.\s*\d+", ".", highlight)
            highlights_text += f"{cleaned.strip()}\n---\n"
            wrapped = textwrap.fill(cleaned.strip(), width=50)
            st.text(wrapped)
            st.markdown("---")
    
        # Safe filename from title
        safe_title = re.sub(r'[\\/*?:"<>|]', "", selected_title)
        file_name = f"{safe_title}_highlights.txt"

        st.download_button(
            label="📥 Download highlights as TXT",
            data=highlights_text,
            file_name=file_name,
            mime="text/plain"
        )

import re

# Clean up titles
def extract_title_author(text):
    # Find all parenthetical groups
    parens = re.findall(r'\([^)]*\)', text)
    if not parens:
        return text.strip()  # nothing to clean

    # Extract last group as author, remove the rest
    author = parens[-1]
    text_without_parens = re.sub(r'\s*\([^)]*\)', '', text).strip()
    
    # Reattach just the author
    return f"{text_without_parens} {author}"


# Search
def search_highlights():
    df = st.session_state.get("df")
    if df is None:
        st.warning("No data loaded.")
        return

    search_term = st.text_input("🔍 Search your highlights:")

    
    if search_term:
        results = df[df['highlight'].str.contains(search_term, case=False, na=False)]
        if results.empty:
            st.info("No highlights found.")
        else:
            st.write(f"Results for '{search_term}':")
            st.dataframe(results[['title', 'highlight']])   

# helper function for small screens
# this is currently only being used in the get_context fuction
def wrapped_streamlit(label, text, width=40):
    if text:
        wrapped_text = textwrap.fill(text, width=width)
        st.markdown(f"**{label}:**")
        st.info(wrapped_text)
    else:
         st.markdown(f"**{label}:** _No highlight available._")

# show surrounding context for a highlight
def context(df, random_index):
    try:
        result = get_context(df, random_index)
        
        st.markdown("Context View")
        st.subheader(f"{result['title']}")

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
    kindle_sum.sort_values('Title',inplace=True)
    filtered_df = kindle_sum.copy()
    
    # --- Book Count ---
    st.markdown(f"**Total Books Displayed: {len(filtered_df)}**")

    # --- Display Table ---
    st.dataframe(filtered_df, use_container_width=True)

    # --- Download Button ---
    csv_buffer = StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv_buffer.getvalue(),
        file_name="kindle_books_filtered.csv",
        mime="text/csv"
    )

# Split main into smaller functions
def handle_file_upload():
    uploaded_file = st.file_uploader(
        "Upload your 'My Clippings.txt' file", 
        type=["txt"],
        key="file_upload_main"
    )
    return uploaded_file

def process_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    df = parse_kindle_highlights(tmp_path)
    df.sort_values('added_on', inplace=True)

    # Drop clip limit messages and duplicates
    clip_message = "You have reached the clipping limit for this item"
    df = df[~df['highlight'].str.contains(clip_message, na=False)]
    df = df.drop_duplicates(subset=['title', 'location'])
    return df

# Begin execution
def main():
    st.title("Kindle Highlights Viewer")
    uploaded_file = handle_file_upload()

    if uploaded_file is not None and 'df' not in st.session_state:
        df = process_uploaded_file(uploaded_file)
        df["title"] = df["title"].apply(extract_title_author)
        st.session_state["df"] = df  # Save back if needed
        kindle_sum = setup_summary(df)

        # Titles containing these words will be excluded 
        exclude_keywords = ["Reggie", "Bicycling", "Python"]
        st.session_state.exclude_keywords = exclude_keywords

        try:
            row, random_index = get_random_highlight_excluding(df, exclude_keywords)
        except ValueError as e:
            st.error(f"Error: {e}")
            return
    
        cleaned_highlight = re.sub(r"\.\s*\d+", ".", row['highlight'])
       
        # Store in session state
        st.session_state.df = df
        st.session_state.title = row['title']
        st.session_state.cleaned_highlight = cleaned_highlight
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
        st.markdown("Random Highlight")
        st.subheader(f"{st.session_state.title}")
        # retains mono font, no syntax highlight
        st.info(textwrap.fill(st.session_state.cleaned_highlight, width=45))

        action = st.radio(
            "What would you like to do next?",
            ("Random Highlight", 
                "Get context", 
                "Show highlights for selected title", 
                "Search all text",
                "Show all titles")
        )
        # Always run this — Streamlit needs to render the UI every time
        if action == "Get context":
            if st.button("🚀 RUN 'Get context'"):
                context(df, random_index)

        elif action == "Random Highlight":
            if st.button("🚀 RUN 'Random Highlight'"):
                try:
                    exclude_keywords = st.session_state.exclude_keywords
                    row, random_index = get_random_highlight_excluding(df, exclude_keywords)
                    cleaned = re.sub(r"\.\s*\d+", ".", row['highlight'])
    
                    # Save to session state for reuse
                    st.session_state.random_index = random_index
                    st.session_state.title = row['title']
                    st.session_state.cleaned_highlight = cleaned
    
                    # Display the new highlight
                    st.markdown("Random Highlight:")
                    st.subheader(f"{row['title']}")
                    st.info(textwrap.fill(cleaned, width=45))
    
                except ValueError as e:
                    st.error(f"No suitable highlight found: {e}")

        elif action == "Show highlights for selected title":
            show_highlights_for_title()  # This function should render UI directly with selectbox

        elif action == "Search all text":
            search_highlights ()  # This function should render UI directly with selectbox

        elif action == "Show all titles":
            if st.button("🚀 RUN 'Show all titles'"):
                process_kindle_sum(kindle_sum)


