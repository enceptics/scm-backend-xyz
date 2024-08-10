# forms.py
from django import forms
from logistics.models import ControlCenter

from .models import InventoryBreedSales
from transaction.models import BreaderTrade


class InventoryBreedSalesForm(forms.ModelForm):
    breed = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = BreaderTrade
        fields = ['breed', 'part_name', 'sale_type', 'part_quantity', 'part_weight']

class ControlCenterForm(forms.ModelForm):
    class Meta:
        model = ControlCenter
        fields = ['name', 'location', 'address', 'contact'] 
