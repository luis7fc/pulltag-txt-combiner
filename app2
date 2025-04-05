Python 3.13.1 (v3.13.1:06714517797, Dec  3 2024, 14:00:22) [Clang 15.0.0 (clang-1500.3.9.4)] on darwin
Type "help", "copyright", "credits" or "license()" for more information.
>>> import streamlit as st
... import pandas as pd
... from io import StringIO
... from datetime import datetime
... 
... # Streamlit App
... st.title("🚀 Pulltag TXT Combiner")
... 
... # Inputs
... uploaded_files = st.file_uploader("Drag and Drop .txt Files Here:", accept_multiple_files=True, type=['txt'])
... 
... title = st.text_input("Enter the Title:")
... kit_date = st.date_input("Select Kit Date:")
... 
... if st.button("Combine Files"):
...     if uploaded_files and title and kit_date:
...         combined_lines = []
... 
...         # Add header lines as specified
...         formatted_date = kit_date.strftime("%m-%d-%y")
...         header_line1 = f'I,{title},{formatted_date},{formatted_date},,"",,,,,,,,,\n'
...         header_line2 = ',,,,,"",,,,,,,,,\n'
... 
...         combined_lines.append(header_line1)
...         combined_lines.append(header_line2)
... 
...         header_added = False  # To add header only once
... 
...         for uploaded_file in uploaded_files:
...             stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
...             lines = stringio.readlines()
... 
...             for line in lines:
...                 # Add header from first file only once
...                 if not header_added and line.startswith(";"):
...                     combined_lines.append(line.strip() + "\n")
...                     header_added = True
...                     continue
...                 elif line.startswith(";"):
...                     continue  # Skip subsequent file headers
... 
...                 # Append Kit Date to "IL" lines
...                 if line.startswith("IL"):
...                     line = line.strip() + f",{formatted_date}\n"
...                     combined_lines.append(line)
...                 else:
...                     combined_lines.append(line)
... 
...         # Join all lines
...         combined_txt = ''.join(combined_lines)
... 
...         st.success("🎉 Files combined successfully!")
... 
...         # Download link
...         st.download_button(
...             label="📥 Download Combined TXT",
...             data=combined_txt,
...             file_name=f"{title}_{formatted_date}.txt",
...             mime="text/plain"
...         )
...     else:
        st.warning("⚠️ Please upload files and provide Title and Kit Date.")
