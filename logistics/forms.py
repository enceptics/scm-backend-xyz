from django import forms
from .models import PackageInfo, LogisticsStatus

class PackageInfoForm(forms.ModelForm):
    class Meta:
        model = PackageInfo
        fields = '__all__'

class LogisticsStatusForm(forms.ModelForm):
    class Meta:
        model = LogisticsStatus
        fields = '__all__'
