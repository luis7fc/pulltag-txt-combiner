import streamlit as st
import pandas as pd
import re
import csv
from io import BytesIO

st.set_page_config(page_title="TXT Combiner + Verifier", layout="wide")
st.title("🧰 Pulltag TXT Combiner + High $ Scan Verifier")

# Inputs
uploaded_txt_files = st.file_uploader("📂 Drag & Drop .txt Files", accept_multiple_files=True, type=["txt"])
scan_log_file = st.file_uploader("📋 (Optional) Upload Scan Log CSV", type=["csv"])

title = st.text_input("📋 Enter the Title:")
kit_date = st.date_input("📅 Select Kit Date")

if st.button("🔀 Combine Files"):
    if not (uploaded_txt_files and title and kit_date):
        st.warning("⚠️ Please upload at least one .txt file and enter Title and Kit Date.")
        st.stop()

    combined_lines = []
    line_items = []  # <-- collect all IL rows for master quantity + verification

    # Format title-safe filename
    title_cleaned = re.sub(r"\W+", "_", title.strip()).strip("_")
    formatted_date = kit_date.strftime("%m-%d-%y")

    # Header lines
    header_line1 = f'I,{title},{formatted_date},{formatted_date},,"",,,,,,,,,\n'
    header_line2 = ',,,,,"",,,,,,,,,\n'
    combined_lines.extend([header_line1, header_line2])

    header_written = False

    for file in uploaded_txt_files:
        lines = file.read().decode("utf-8", errors="replace").splitlines()

        for line in lines:
            if line.startswith(";") and not header_written:
                combined_lines.append(line + "\n")
                header_written = True
                continue

            if not line.startswith("IL"):
                continue

            # Keep existing combined TXT behavior
            combined_lines.append(line.strip() + f",{formatted_date}\n")

            # Robust parse (handles commas inside quoted description fields)
            row = next(csv.reader([line]))

            item_code = row[2].strip() if len(row) > 2 else ""
            description = row[5].strip() if len(row) > 5 else ""
            job_number = row[9].strip() if len(row) > 9 else ""
            lot_number = row[10].strip() if len(row) > 10 else ""

            qty = pd.to_numeric(row[3], errors="coerce")
            if pd.isna(qty):
                qty = 0
            qty = int(qty)

            line_items.append(
                {
                    "Job Number": str(job_number),
                    "Lot Number": str(lot_number),
                    "Item Code": item_code,
                    "Description": description,
                    "Expected Qty": qty,
                }
            )

    # Download combined TXT
    combined_txt = "".join(combined_lines)
    st.download_button(
        label="📥 Download Combined TXT",
        data=combined_txt,
        file_name=f"{title_cleaned}.txt",
        mime="text/plain",
    )

    # -------------------------
    # Master quantity summary
    # -------------------------
    if not line_items:
        st.info("No IL lines found in the uploaded TXT files.")
        st.stop()

    raw_txt_df = pd.DataFrame(line_items)

    # Sum expected qty across *all uploaded txt files* by item code per lot (and job)
    master_qty_df = (
        raw_txt_df.groupby(["Job Number", "Lot Number", "Item Code"], as_index=False)
        .agg(
            Description=("Description", "first"),
            Master Qty=("Expected Qty", "sum"),
        )
        .sort_values(["Job Number", "Lot Number", "Item Code"])
    )

    st.subheader("📦 Master Quantity Summary (Sum of all uploaded TXTs)")
    st.dataframe(master_qty_df, use_container_width=True)

    master_csv = master_qty_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Master Quantity CSV",
        data=master_csv,
        file_name=f"{title_cleaned}_master_qty.csv",
        mime="text/csv",
    )

    # Optional XLSX download (nice if users want an Excel table)
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            master_qty_df.to_excel(writer, index=False, sheet_name="Master Qty")
        st.download_button(
            label="📥 Download Master Quantity XLSX",
            data=output.getvalue(),
            file_name=f"{title_cleaned}_master_qty.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception:
        # If openpyxl isn't available in the environment, CSV still works
        pass

    # -------------------------
    # Verification logic
    # -------------------------
    if scan_log_file:
        scan_df = pd.read_csv(scan_log_file)

        scan_grouped = (
            scan_df.groupby(["Item Code", "Job Number", "Lot Number"])
            .size()
            .reset_index(name="Scanned Qty")
        )

        # Use the grouped expected qty (master) for verification to avoid duplicates
        expected_df = master_qty_df.rename(columns={"Master Qty": "Expected Qty"})[
            ["Item Code", "Job Number", "Lot Number", "Expected Qty"]
        ]

        # Make join keys consistent
        for c in ["Job Number", "Lot Number"]:
            scan_grouped[c] = scan_grouped[c].astype(str)
            expected_df[c] = expected_df[c].astype(str)

        merged = pd.merge(
            scan_grouped,
            expected_df,
            on=["Item Code", "Job Number", "Lot Number"],
            how="outer",
        )
        merged["Scanned Qty"] = merged["Scanned Qty"].fillna(0).astype(int)
        merged["Expected Qty"] = pd.to_numeric(merged["Expected Qty"], errors="coerce").fillna(0).astype(int)

        def get_status(row):
            if row["Scanned Qty"] == row["Expected Qty"]:
                return "✅ Match"
            elif row["Scanned Qty"] == 0:
                return "❌ Missing"
            else:
                return "⚠️ Mismatch"

        merged["Status"] = merged.apply(get_status, axis=1)

        st.subheader("🔍 Verification Results")
        st.dataframe(merged, use_container_width=True)

        summary_csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Verification Summary CSV",
            data=summary_csv,
            file_name=f"{title_cleaned}_verification.csv",
            mime="text/csv",
        )
