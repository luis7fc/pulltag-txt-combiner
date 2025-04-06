import streamlit as st
import pandas as pd
from io import StringIO
import re
from datetime import datetime

st.set_page_config(page_title="TXT Combiner + Verifier", layout="wide")
st.title("🧰 Pulltag TXT Combiner + High $ Scan Verifier")

# Inputs
uploaded_txt_files = st.file_uploader("📂 Drag & Drop .txt Files", accept_multiple_files=True, type=['txt'])
scan_log_file = st.file_uploader("📋 (Optional) Upload Scan Log CSV", type=['csv'])

title = st.text_input("📋 Enter the Title:")
kit_date = st.date_input("📅 Select Kit Date")

if st.button("🔀 Combine Files"):
    if uploaded_txt_files and title and kit_date:
        combined_lines = []

        # Format title-safe filename
        title_cleaned = re.sub(r'\W+', '_', title.strip()).strip('_')
        formatted_date = kit_date.strftime("%m-%d-%y")

        # Header lines
        header_line1 = f'I,{title},{formatted_date},{formatted_date},,"",,,,,,,,,\n'
        header_line2 = ',,,,,"",,,,,,,,,\n'
        combined_lines.append(header_line1)
        combined_lines.append(header_line2)

        header_written = False
        txt_data = []

        for file in uploaded_txt_files:
            lines = file.read().decode("utf-8").splitlines()
            for line in lines:
                if line.startswith(";") and not header_written:
                    combined_lines.append(line + "\n")
                    header_written = True
                elif line.startswith("IL"):
                    modified_line = line.strip() + f",{formatted_date}\n"
                    combined_lines.append(modified_line)

                    # Extract item code, job, lot, and quantity for verification
                    parts = line.split(',')
                    txt_data.append({
                        "Item Code": parts[2],
                        "Job Number": parts[9],
                        "Lot Number": parts[10],
                        "Expected Qty": int(parts[3])
                    })

        combined_txt = ''.join(combined_lines)
        file_name = f"{title_cleaned}.txt"

        st.download_button(
            label="📥 Download Combined TXT",
            data=combined_txt,
            file_name=file_name,
            mime="text/plain"
        )

        # Verification logic
        if scan_log_file:
            scan_df = pd.read_csv(scan_log_file)
            scan_grouped = (
                scan_df.groupby(['Item Code', 'Job Number', 'Lot Number'])
                .size()
                .reset_index(name='Scanned Qty')
            )

            txt_df = pd.DataFrame(txt_data)
            scan_grouped[['Job Number', 'Lot Number']] = scan_grouped[['Job Number', 'Lot Number']].astype(str)
            txt_df[['Job Number', 'Lot Number']] = txt_df[['Job Number', 'Lot Number']].astype(str)

            merged = pd.merge(scan_grouped, txt_df, on=['Item Code', 'Job Number', 'Lot Number'], how='outer')
            merged['Scanned Qty'] = merged['Scanned Qty'].fillna(0).astype(int)
            merged['Expected Qty'] = merged['Expected Qty'].fillna(0).astype(int)

            def get_status(row):
                if row['Scanned Qty'] == row['Expected Qty']:
                    return '✅ Match'
                elif row['Scanned Qty'] == 0:
                    return '❌ Missing'
                else:
                    return '⚠️ Mismatch'

            merged['Status'] = merged.apply(get_status, axis=1)

            st.subheader("🔍 Verification Results")
            st.dataframe(merged)

            summary_csv = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Verification Summary CSV",
                data=summary_csv,
                file_name=f"{title_cleaned}_verification.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ Please upload at least one .txt file and enter Title and Kit Date.")
