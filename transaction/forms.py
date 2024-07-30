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
        fields = ['control_center', 'breed', 'breeds_supplied', 'weight', 'vaccinated']