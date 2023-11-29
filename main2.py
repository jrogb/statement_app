import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd
import camelot

class PDFExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Extractor")

        # Label to display the selected PDF name
        self.selected_pdf_label = tk.Label(root, text="Selected Statement: None")
        self.selected_pdf_label.pack(pady=10)

        # Buttons
        choose_button = tk.Button(root, text='Choose a Statement', command=self.choose_pdf)
        choose_button.pack(pady=5, side=tk.TOP)

        # Labels for specific values
        self.account_number_label = tk.Label(root, text="Account number:")
        self.account_number_label.pack(side=tk.TOP)

        self.account_holder_label = tk.Label(root, text="Account holder:")
        self.account_holder_label.pack(side=tk.TOP)

        self.product_name_label = tk.Label(root, text="Product name:")
        self.product_name_label.pack(side=tk.TOP)

        extract_button = tk.Button(root, text='Extract Transactions', command=self.extract_and_save_csv)
        extract_button.pack(pady=5, side=tk.TOP)

        # Dataframes
        self.customer_details_df = pd.DataFrame()
        self.transactions_df = pd.DataFrame()

        # Label for indicating ongoing operations
        self.operations_label = tk.Label(root, text="")
        self.operations_label.pack()

    def choose_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[('PDF Files', '*.pdf')])
        if file_path:
            pdf_file_name = os.path.basename(file_path)
            self.pdf_file_path = file_path
            self.selected_pdf_label.config(text=f"Selected PDF: {pdf_file_name}")

            # Add a visual indicator
            self.operations_label.config(text="Processing... Please wait.")
            self.root.update_idletasks()

            self.extract_data()

            # Remove the visual indicator
            self.operations_label.config(text="")

    def extract_data(self):
        if hasattr(self, 'pdf_file_path'):
            tables = camelot.read_pdf(self.pdf_file_path, flavor='stream', pages='all')

            # Extract Customer Details (first 17 rows)
            self.customer_details_df = pd.concat([table.df for table in tables[:17]], ignore_index=True)

            # Extract specific values
            account_number = self.customer_details_df.iloc[8, 0]

            account_holder_row = self.customer_details_df[self.customer_details_df[0].str.contains('Account holder')]
            account_holder = account_holder_row.iloc[0, 1] if not account_holder_row.empty else 'N/A'

            product_name_row = self.customer_details_df[self.customer_details_df[0].str.contains('Product name')]
            product_name = product_name_row.iloc[0, 1] if not product_name_row.empty else 'N/A'

            # Display specific values in labels
            self.account_number_label.config(text=f"{account_number}")
            self.account_holder_label.config(text=f"Account Holder: {account_holder}")
            self.product_name_label.config(text=f"Product name: {product_name}")

    def extract_and_save_csv(self):
        if hasattr(self, 'pdf_file_path'):
            # Add a visual indicator
            self.operations_label.config(text="Processing... Please wait.")
            self.root.update_idletasks()

            tables = camelot.read_pdf(self.pdf_file_path, flavor='stream', pages='all')

            # Extract Transactions (remaining rows)
            self.transactions_df = pd.concat([table.df for table in tables[17:]], ignore_index=True)
            self.transactions_df.columns = ['Date', 'Description', 'Payments', 'Deposits', 'Balance']  # Set headers

            self.transactions_df = self.clean_transactions_df(self.transactions_df)

            self.save_csv(self.transactions_df)

            # Remove the visual indicator
            self.operations_label.config(text="")
            messagebox.showinfo("Success", "Data saved to CSV successfully!")
        else:
            print("Please choose a PDF file first.")

    def clean_transactions_df(self, df):
        # Remove rows with specific values in the 'Date' and 'Balance' columns
        df = df[~df['Date'].isin(['Date', 'Transaction details'])]
        df = df[~df['Balance'].str.startswith('Available')]

        # Identify rows with text in the 'Description' column
        mask = df['Description'].str.strip() != ''

        # Concatenate 'Description' values with the text from the row below at the end
        df['Description'] = df['Description'].shift(-1).where(mask, '') + ' ' + df['Description'].where(mask, '')

        # Drop the rows where 'Date' is empty (no corresponding 'Date' value)
        df = df[df['Date'] != '']

        return df

    def save_csv(self, df):
        # Save the DataFrame to a CSV file and prompt the user for a save location
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if save_path:
            df.to_csv(save_path, index=False)
            print(f"DataFrame saved to: {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFExtractorApp(root)
    root.mainloop()
