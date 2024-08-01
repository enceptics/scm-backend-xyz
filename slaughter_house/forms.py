# forms.py
from transaction.models import BreaderTrade
from slaughter_house.models import SlaughterhouseRecord

from django import forms

class SlaughterForm(forms.Form):
    breeds_to_slaughter = forms.ModelMultipleChoiceField(queryset=BreaderTrade.objects.all(), widget=forms.CheckboxSelectMultiple)

class FinishedProductForm(forms.ModelForm):
    class Meta:
        model = SlaughterhouseRecord
        fields = '__all__'  

from django import forms
from .models import BreaderTrade

class SlaughterhouseRecordForm(forms.ModelForm):
    class Meta:
        model = BreaderTrade
        fields = ['weight', 'breeds_supplied']



