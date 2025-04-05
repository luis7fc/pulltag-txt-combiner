import streamlit as st
import pandas as pd
from io import StringIO
from datetime import datetime
import re

st.set_page_config(page_title="TXT Combiner", layout="centered")
st.title("🧰 Pulltag TXT Combiner")

# Inputs
uploaded_files = st.file_uploader("📂 Drag and Drop .txt Files Here", accept_multiple_files=True, type=['txt'])

title = st.text_input("📋 Enter the Title:")
kit_date = st.date_input("📅 Select Kit Date")

if st.button("🔀 Combine Files"):
    if uploaded_files and title and kit_date:
        combined_lines = []

        # Format title-safe filename
        title_cleaned = re.sub(r'\W+', '_', title.strip())
        formatted_date = kit_date.strftime("%m-%d-%y")

        # Header rows
        header_line1 = f'I,{title},{formatted_date},{formatted_date},,"",,,,,,,,,\n'
        header_line2 = ',,,,,"",,,,,,,,,\n'
        combined_lines.append(header_line1)
        combined_lines.append(header_line2)

        header_written = False

        for file in uploaded_files:
            content = file.read().decode("utf-8")
            lines = content.splitlines()

            for line in lines:
                if line.startswith(";") and not header_written:
                    combined_lines.append(line + "\n")
                    header_written = True
                elif line.startswith("IL"):
                    combined_lines.append(line.strip() + f",{formatted_date}\n")

        final_output = "".join(combined_lines)

        st.success("🎉 Files combined successfully!")

        # Generate downloadable file name
        file_name = f"{title_cleaned}_{formatted_date}.txt"

        st.download_button(
            label="📥 Download Combined TXT",
            data=final_output,
            file_name=file_name,
            mime="text/plain"
        )
    else:
        st.warning("⚠️ Please upload at least one file, enter a title, and select a kit date.")
