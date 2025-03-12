import streamlit as st
import pandas as pd
import re
import io
import PyPDF2
from pdfminer.high_level import extract_text
import matplotlib.pyplot as plt
import seaborn as sns

# Function to extract text from PDF (with password support)
def extract_pdf_text(file, password=None):
    # First use PyPDF2 to handle password if needed
    pdf_reader = PyPDF2.PdfReader(file)
    
    if pdf_reader.is_encrypted:
        if password:
            try:
                pdf_reader.decrypt(password)
            except:
                return "Incorrect password. Please try again."
        else:
            return "PDF is encrypted. Please provide a password."
    
    # Save decrypted PDF to a buffer
    output = io.BytesIO()
    writer = PyPDF2.PdfWriter()
    for page in pdf_reader.pages:
        writer.add_page(page)
    writer.write(output)
    output.seek(0)
    
    # Use pdfminer for accurate text extraction with spacing preserved
    text = extract_text(output)
    return text

# Function to extract transactions from PDF
def extract_transactions(pdf_file, password=None):
    input_text = extract_pdf_text(pdf_file, password)
    
    # Check if there was an error with the password
    if isinstance(input_text, str) and (input_text.startswith("PDF is encrypted") or input_text.startswith("Incorrect password")):
        return input_text
    
    # Define the pattern for transaction lines
    pattern = re.compile(r'^\d{2}[A-Za-z]{3}.*', re.MULTILINE)

    # Filter matching lines
    lines = [line.strip() for line in pattern.findall(input_text)]
    
    data = []
    for line in lines:
        # Extract fields based on column positions
        fecha_proceso = line[:5].strip()
        fecha_consumo = line[5:14].strip()
        description = line[14:63].strip()
        operation_type = line[63:80].strip()
        soles = line[80:95].strip()
        dolares = line[95:].strip()

        # Filter only "CONSUMOS" transactions
        if "CONSUMO" in operation_type:
            # Convert amounts to float (handling empty values)
            soles = float(soles.replace(",", "").replace("S/", "").strip() or 0) if soles else 0
            dolares = float(dolares.replace(",", "").replace("$", "").strip() or 0) if dolares else 0

            data.append([fecha_proceso, fecha_consumo, description, operation_type, soles, dolares])

    # If no data was found
    if not data:
        return "No transaction data found in the PDF. Check if the format matches expectations."
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=["Fecha Proceso", "Fecha Consumo", "Descripción", "Tipo de Operación", "Monto en Soles", "Monto en Dólares"])
    return df

# Function to create bar charts
def create_charts(df):
    # Group by description and sum the amounts
    soles_by_desc = df.groupby('Descripción')['Monto en Soles'].sum().sort_values(ascending=False)
    dollars_by_desc = df.groupby('Descripción')['Monto en Dólares'].sum().sort_values(ascending=False)
    
    # Filter out zero values
    soles_by_desc = soles_by_desc[soles_by_desc > 0]
    dollars_by_desc = dollars_by_desc[dollars_by_desc > 0]
    
    # Create the charts
    fig, axes = plt.subplots(2, 1, figsize=(10, 12))
    
    # Soles chart
    if not soles_by_desc.empty:
        sns.barplot(x=soles_by_desc.values, y=soles_by_desc.index, ax=axes[0], palette='Blues_d')
        axes[0].set_title('Transactions in Soles (Descending Order)')
        axes[0].set_xlabel('Amount in Soles')
        axes[0].set_ylabel('Description')
    else:
        axes[0].text(0.5, 0.5, 'No transactions in Soles', ha='center', va='center')
        axes[0].set_title('Transactions in Soles')
    
    # Dollars chart
    if not dollars_by_desc.empty:
        sns.barplot(x=dollars_by_desc.values, y=dollars_by_desc.index, ax=axes[1], palette='Greens_d')
        axes[1].set_title('Transactions in Dollars (Descending Order)')
        axes[1].set_xlabel('Amount in Dollars')
        axes[1].set_ylabel('Description')
    else:
        axes[1].text(0.5, 0.5, 'No transactions in Dollars', ha='center', va='center')
        axes[1].set_title('Transactions in Dollars')
    
    plt.tight_layout()
    return fig

# Streamlit app
st.title("Bank Statement Transaction Analyzer")
st.write("Upload your PDF bank statement to analyze transactions")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
password = st.text_input("Password (if needed)", type="password")

if uploaded_file is not None:
    if st.button("Extract and Analyze"):
        # Show a spinner while processing
        with st.spinner("Processing PDF..."):
            result = extract_transactions(uploaded_file, password)
            
            if isinstance(result, str):
                st.error(result)
            else:
                # Show the dataframe
                st.subheader("Extracted Transactions")
                st.dataframe(result)
                
                # Show charts
                st.subheader("Transaction Analysis")
                fig = create_charts(result)
                st.pyplot(fig)
                
                # Provide download link for the data
                csv = result.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Transactions as CSV",
                    data=csv,
                    file_name="transactions.csv",
                    mime="text/csv"
                )
