# forms.py

from django import forms
from .models import BreaderTrade

class SlaughterForm(forms.Form):
    breeds_to_slaughter = forms.ModelMultipleChoiceField(queryset=BreaderTrade.objects.all(), widget=forms.CheckboxSelectMultiple)

from django.contrib.auth import get_user_model

User = get_user_model()

class BreaderTradeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BreaderTradeForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['breeder'].initial = user

    class Meta:
        model = BreaderTrade
        fields = '__all__'