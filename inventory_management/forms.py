# forms.py
from django import forms
from logistics.models import ControlCenter

from .models import InventoryBreedSales

class InventoryBreedSalesForm(forms.ModelForm):
    class Meta:
        model = InventoryBreedSales
        fields = ['breed', 'part_name', 'sale_type', 'quantity', 'weight', 'seller', 'reference']

class ControlCenterForm(forms.ModelForm):
    class Meta:
        model = ControlCenter
        fields = ['name', 'location', 'address', 'contact']  # Add other fields as needed
