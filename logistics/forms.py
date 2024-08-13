from django import forms
from .models import PackageInfo, LogisticsStatus
from transaction.models import BreaderTrade

class PackageInfoForm(forms.ModelForm):
    class Meta:
        model = PackageInfo
        fields = ['package_name', 'package_description', 'package_charge', 'weight', 'height', 'length']

class LogisticsStatusForm(forms.ModelForm):
    class Meta:
        model = LogisticsStatus
        fields = ['buyer', 'seller', 'shipping_mode', 'logistics_company', 'associated_control_center', 'status', 'bill_of_lading']

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        self.package_info = kwargs.pop('package_info', None)
        super(LogisticsStatusForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(LogisticsStatusForm, self).save(commit=False)
        if self.invoice:
            instance.invoice = self.invoice
        if self.package_info:
            instance.package_info = self.package_info
        if commit:
            instance.save()
        return instance

# UPDATEDEXPORT FORM FOR SELECTING MULTIPLE
from django import forms

class ExportPartsForm(forms.Form):
    breed = forms.CharField(max_length=255)
    parts = forms.ModelMultipleChoiceField(
        queryset=BreaderTrade.objects.filter(sale_type='export').exclude(part_name__isnull=True).exclude(part_name=''),
        widget=forms.CheckboxSelectMultiple,
    )
