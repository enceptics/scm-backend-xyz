from django import forms
from .models import PackageInfo, LogisticsStatus

class PackageInfoForm(forms.ModelForm):
    class Meta:
        model = PackageInfo
        fields = '__all__'

class LogisticsStatusForm(forms.ModelForm):
    class Meta:
        model = LogisticsStatus
        fields = ['buyer', 'seller', 'shipping_mode', 'logistics_company', 'associated_control_center', 'bill_of_lading']