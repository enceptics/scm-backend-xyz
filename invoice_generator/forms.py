# forms.py
from django import forms
from .models import Quotation, LetterOfCredit, Invoice

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['seller', 'buyer', 'product', 'confirm', 'quantity', 'delivery_time', 'unit_price', 'message', 'market', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the status field as required
        self.fields['status'].required = True


class LetterOfCreditForm(forms.ModelForm):
    class Meta:
        model = LetterOfCredit
        fields = ['buyer', 'seller', 'lc_document']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form fields here if needed

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'

