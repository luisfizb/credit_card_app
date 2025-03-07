import streamlit as st
import pandas as pd
import re
import pdfplumber
import matplotlib.pyplot as plt

def extract_transactions_from_pdf(pdf_file, password=None):
    transactions = []
    pattern = r"(\d{2}\w{3})\s+(\d{2}\w{3})\s+(.+?)\s+([A-Z]{2})\s+(CONSUMO|PAGO|PAGOSERVIC)\s+([\d.,-]+)"
    
    with pdfplumber.open(pdf_file, password=password) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    match = re.search(pattern, line)
                    if match:
                        posting_date = match.group(1)
                        transaction_date = match.group(2)
                        description = match.group(3).strip()
                        country = match.group(4)
                        transaction_type = match.group(5)
                        amount = float(match.group(6).replace(',', ''))  # Convert amount to decimal
                        
                        # Determine currency based on description position
                        currency = "USD" if re.search(r"\b[A-Za-z]+\b\s+[\d.,-]+$", line) else "PEN"
                        
                        transactions.append([posting_date, transaction_date, description, country, transaction_type, amount, currency])
    
    return pd.DataFrame(transactions, columns=["Posting Date", "Transaction Date", "Description", "Country", "Type", "Amount", "Currency"])

# Streamlit App
st.title("PDF Transaction Extractor")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
password = st.text_input("Enter password (if needed)", type="password")

if uploaded_file is not None:
    st.write("Extracting transactions...")
    transactions_df = extract_transactions_from_pdf(uploaded_file, password)
    
    if not transactions_df.empty:
        # Separate transactions by currency
        transactions_pen = transactions_df[transactions_df["Currency"] == "PEN"]
        transactions_usd = transactions_df[transactions_df["Currency"] == "USD"]
        
        # Aggregate amounts by description and select top 20
        def plot_top_transactions(df, currency):
            agg_df = df.groupby("Description")["Amount"].sum().reset_index()
            agg_df = agg_df.sort_values(by="Amount", ascending=False).head(20)
            
            # Plot improved horizontal bar chart
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.barh(agg_df["Description"], agg_df["Amount"], color='skyblue', edgecolor='black')
            ax.set_xlabel(f"Amount ({currency})", fontsize=12)
            ax.set_ylabel("Description", fontsize=12)
            ax.set_title(f"Top 20 Transaction Amounts in {currency}", fontsize=14, fontweight='bold')
            plt.xticks(fontsize=10)
            plt.yticks(fontsize=10)
            plt.gca().invert_yaxis()
            
            # Add rounded values at the end of each bar
            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
                        va='center', fontsize=10, fontweight='bold', color='black')
            
            st.pyplot(fig)
        
        if not transactions_pen.empty:
            plot_top_transactions(transactions_pen, "PEN")
        if not transactions_usd.empty:
            plot_top_transactions(transactions_usd, "USD")
    else:
        st.error("No transactions extracted. Check the password or file format.")
