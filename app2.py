import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader

def read_pdf_content(pdf_file, password=None):
    """Extract text from an uploaded PDF file, handling password protection"""
    reader = PdfReader(pdf_file)
    
    if reader.is_encrypted:
        if password:
            reader.decrypt(password)
        else:
            st.error("This PDF is password-protected. Please enter a password.")
            return ""
    
    text_content = ""
    for page in reader.pages:
        text_content += page.extract_text() + "\n"
    return text_content

def extract_transactions_from_pdf(pdf_file, password=None):
    content = read_pdf_content(pdf_file, password)
    if not content:
        return pd.DataFrame()
    
    lines = content.split('\n')
    transactions = []

    for line in lines:
        if re.match(r'\d{2}[A-Za-z]{3}', line) and 'PAGO' not in line:
            transactions.append(line)

    pattern = r'(\d{2}[A-Za-z]{3})\s+(\d{2}[A-Za-z]{3})\s+(.*?)\s+([A-Z]{2})\s+([A-Z]+)\s+([0-9,.]+)'
    split_transactions = [re.findall(pattern, t) for t in transactions]
    flat_transactions = [item for sublist in split_transactions for item in sublist]
    
    return pd.DataFrame(flat_transactions, columns=['Posting Date', 'Transaction Date', 'Description', 'Country', 'Type', 'Amount'])

# Streamlit App
st.title("PDF Transaction Extractor")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
password = st.text_input("Enter password (if needed)", type="password")

if uploaded_file is not None:
    st.write("Extracting transactions...")
    transactions_df = extract_transactions_from_pdf(uploaded_file, password)
    
    if not transactions_df.empty:
        st.dataframe(transactions_df)
        
        # Provide option to download as CSV
        csv = transactions_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "transactions.csv", "text/csv")
    else:
        st.error("No transactions extracted. Check the password or file format.")