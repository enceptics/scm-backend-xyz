# forms.py

from django import forms
from .models import BreaderTrade

class SlaughterForm(forms.Form):
    
    breeds_to_slaughter = forms.ModelMultipleChoiceField(queryset=BreaderTrade.objects.all(), widget=forms.CheckboxSelectMultiple)

from django.contrib.auth import get_user_model

User = get_user_model()

class BreaderTradeForm(forms.ModelForm):
    class Meta:
        model = BreaderTrade
        fields = ['control_center', 'seller', 'breeds_supplied', 'vaccinated']
        widgets = {
            'seller': forms.HiddenInput(),  # Make the seller field hidden
        }

class ReceptionForm(forms.ModelForm):
    class Meta:
        model = BreaderTrade
        fields = ['weight', 'good_condition', 'destroyed_condition', 'poor_condition']
        widgets = {
            'weight': forms.TextInput(attrs={'placeholder': 'Enter the weight received'}),
            'good_condition': forms.TextInput(attrs={'placeholder': 'Enter the number of good condition items'}),
            'destroyed_condition': forms.TextInput(attrs={'placeholder': 'Enter the number of destroyed/dead items'}),
            'poor_condition': forms.TextInput(attrs={'placeholder': 'Enter the number of poor condition items'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        weight = cleaned_data.get('weight')
        good_condition = cleaned_data.get('good_condition')
        destroyed_condition = cleaned_data.get('destroyed_condition')
        poor_condition = cleaned_data.get('poor_condition')
        breeds_supplied = self.instance.breeds_supplied

        # Ensure the total of confirmed values does not exceed supplied amount
        total_confirmed = (weight) + (good_condition ) + (destroyed_condition ) + (poor_condition )
        if total_confirmed > breeds_supplied:
            raise forms.ValidationError("The total confirmed amounts cannot exceed the supplied amount.")