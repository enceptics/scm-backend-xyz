from django import forms
from .models import PackageInfo, LogisticsStatus, ControlCenter
from transaction.models import BreaderTrade
from custom_registration.models import Seller
from invoice_generator.models import Buyer


class PackageInfoForm(forms.ModelForm):
    class Meta:
        model = PackageInfo
        fields = ['package_name', 'package_description', 'weight', 'height', 'length']

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

from django import forms
from django.db.models import Sum
from django import forms

class ExportPartsForm(forms.Form):
    parts = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label="Select Parts for Export",
    )
    control_center = forms.ModelChoiceField(
        queryset=ControlCenter.objects.all(),
        label="Control Center",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    logistics_company = forms.CharField(
        max_length=255,
        label="Logistics Company",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter logistics company name'})
    )
    shipping_mode = forms.ChoiceField(
        choices=[
            ('air', 'Air'),
            ('sea', 'Sea'),
            ('road', 'Road'),
            ('rail', 'Rail')
        ],
        label="Shipping Mode",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    buyer = forms.ModelChoiceField(queryset=Buyer.objects.all(), required=True)
    seller = forms.ModelChoiceField(queryset=Seller.objects.all(), required=True)
    bill_of_lading = forms.FileField(
        label="Bill of Lading",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    package_info = forms.ModelChoiceField(
        queryset=PackageInfo.objects.all(),
        label="Package Information",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aggregate data by part_name
        aggregated_data = (
            BreaderTrade.objects.filter(sale_type='export')
            .exclude(part_name__isnull=True)
            .exclude(part_name='')
            .values('part_name')
            .annotate(
                total_weight=Sum('part_weight'),
                total_quantity=Sum('part_quantity')
            )
            .filter(total_weight__gt=0, total_quantity__gt=0)  # Only include non-zero quantities and weights
        )

        # Create choices dynamically
        choices = []
        for part in aggregated_data:
            part_name = part['part_name']
            total_weight = part['total_weight']
            total_quantity = part['total_quantity']
            label = f"{part_name} ({total_quantity} items, {total_weight} kg)"
            choices.append((part_name, label))

        self.fields['parts'].choices = choices

from django import forms
from .models import LogisticsStatus

class UpdateStatusForm(forms.ModelForm):
    class Meta:
        model = LogisticsStatus
        fields = ['status']

class LogisticsStatusForm(forms.ModelForm):
    class Meta:
        model = PackageInfo
        fields = ['package_name', 'package_description', 'weight', 'height', 'length']


