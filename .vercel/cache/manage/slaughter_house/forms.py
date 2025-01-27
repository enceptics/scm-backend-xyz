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
        fields = ['breeds_supplied', 'weight']

    def __init__(self, *args, **kwargs):
        self.trade = kwargs.pop('trade', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        breeds_supplied = cleaned_data.get('breeds_supplied')
        weight = cleaned_data.get('weight')

        if self.trade:
            if breeds_supplied and breeds_supplied > self.trade.breeds_supplied:
                self.add_error('breeds_supplied', 'Breeds supplied exceeds available quantity.')
            if weight and weight > self.trade.weight:
                self.add_error('weight', 'Weight exceeds available quantity.')

        return cleaned_data

