import os
import django
from django.conf import settings
from invoice_generator.views import extract_lc_data  # Adjust import path as necessary

# Path to the test PDF
pdf_path = os.path.expanduser('~/projects/hrm/test_pdfs/test_lc.pdf')

# Run the extraction function
extracted_data = extract_lc_data(pdf_path)

# Print the extracted data to verify correctness
print("Extracted Data:")
print(extracted_data)
