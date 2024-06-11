import tabula

def extract_table_data(pdf_path, page_number):
    try:
        # Extract tables from the specified page of the PDF
        tables = tabula.read_pdf(pdf_path, pages=page_number, multiple_tables=True)
        
        # Assuming the table containing LC data is the first table on the page
        if tables:
            lc_table = tables[0]  # Get the first table
            # Assuming the table has columns named 'Item', 'Quantity', and 'Date'
            lc_data = lc_table[['Item', 'Quantity', 'Date']]  # Extract specific columns
            return lc_data
        else:
            return None
    except Exception as e:
        print(f"Error extracting table data: {e}")
        return None
