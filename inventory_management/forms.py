# forms.py
from django import forms
from logistics.models import ControlCenter

class ControlCenterForm(forms.ModelForm):
    class Meta:
        model = ControlCenter
        fields = ['name', 'location', 'address', 'contact']  # Add other fields as needed
