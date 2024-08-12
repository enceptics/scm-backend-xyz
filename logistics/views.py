# logistics/views.py
from rest_framework import viewsets
from .models import LogisticsStatus, Order, ShipmentProgress, ArrivedOrder, PackageInfo, CollateralManager,ControlCenter
from .serializers import (LogisticsStatusSerializer,
    OrderSerializer, 
    ShipmentProgressSerializer, 
    ArrivedOrderSerializer, 
    PackageInfoSerializer,
    CollateralManagerSerializer,
    ControlCenterSerializer
    )
from rest_framework.response import Response
from invoice_generator.models import Buyer
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from rest_framework import status

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import action
from rest_framework.response import Response

class PackageInfoViewset(viewsets.ModelViewSet):

    queryset = PackageInfo.objects.all()
    serializer_class = PackageInfoSerializer


class LogisticsStatusViewSet(viewsets.ModelViewSet):
    queryset = LogisticsStatus.objects.all().order_by('-timestamp')
    serializer_class = LogisticsStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(f"Logistics buyer: {self.request.user}")
        buyer = get_object_or_404(Buyer, buyer=self.request.user)
        return LogisticsStatus.objects.filter(buyer=buyer)

    def retrieve(self, request, *args, **kwargs):
        invoice_id = self.kwargs.get('invoice_id')
        instance = get_object_or_404(LogisticsStatus, id=invoice_id)
        print(f"Retrieving logistics status for invoice id: {instance}")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Check if the new status is 'shipped'
        if 'status' in request.data and request.data['status'] == 'shipped':
            # Set the status_updated field to True
            instance.status_updated = True

        serializer.save()

        # Reset status_updated to False after processing the update
        instance.status_updated = False
        instance.save()

        return Response(serializer.data)
        
class LogisticsStatusAllViewSet(viewsets.ModelViewSet):
    queryset = LogisticsStatus.objects.all().order_by('-timestamp')
    serializer_class = LogisticsStatusSerializer

    def retrieve(self, request, *args, **kwargs):
        invoice_id = self.kwargs.get('invoice_id')
        instance = get_object_or_404(LogisticsStatus, id=invoice_id)
        print(f"Retrieving logistics status for invoice id: {instance}")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Check if the new status is 'shipped'
        if 'status' in request.data and request.data['status'] == 'shipped':
            # Set the status_updated field to True
            instance.status_updated = True

        serializer.save()

        # Reset status_updated to False after processing the update
        instance.status_updated = False
        instance.save()

        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_logistics_and_notify_parties(self, request, *args, **kwargs):
        instance = self.get_object()

        # Additional logic related to logistics update can be performed here
        # For example, check the current status, update related models, log information, etc.

        # Assume the buyer model has a 'name' field
        buyer_name = instance.buyer.name

        # Perform the logistics update (replace with your actual update logic)
        success = instance.update_logistics()

        if success:
            # Send email to buyer about the logistics update
            subject = f"Logistics Update - Order No: {instance.invoice_number}"

            # Add buyer's name to the context
            context = {
                'logistics_status': instance,
                'success_message': 'Logistics status has been updated successfully.',
                'buyer_name': buyer_name,
                'current_status': instance.status,
            }

            message = render_to_string('logistics_update_email_template.html', context)
            plain_message = strip_tags(message)
            from_email = 'pascalouma@gmail.com'  # Replace with your email address
            to_email = [instance.buyer.email]

            send_mail(subject, plain_message, from_email, to_email, html_message=message)

            # Serialize the logistics data and return the response
            serializer = self.get_serializer(instance)

            # Additional logic to send emails to other parties
            # Replace the following lines with your actual email sending logic

            # Send email to AdditionalParty
            additional_party_emails = AdditionalParty.objects.values_list('user__email', flat=True)
            additional_party_subject = 'Additional Party Notification'

            # Add relevant context for AdditionalParty
            additional_party_context = {
                'logistics_status': instance,
                'success_message': 'Logistics status has been updated. Please review the details.',
            }

            # Use AdditionalParty email template
            additional_party_message = render_to_string('buyer_order_arrived.html', additional_party_context)

            send_mail(additional_party_subject, strip_tags(additional_party_message), from_email, additional_party_emails, html_message=additional_party_message)

            return Response(serializer.data)
        else:
            # Handle logistics update failure, return an appropriate response
            return Response({'error': 'Logistics update failed'}, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-date_created')
    serializer_class = OrderSerializer

class ShipmentProgressViewSet(viewsets.ModelViewSet):
    queryset = ShipmentProgress.objects.all().order_by('-timestamp')
    serializer_class = ShipmentProgressSerializer

class ArrivedOrderViewSet(viewsets.ModelViewSet):
    queryset = ArrivedOrder.objects.all().order_by('-timestamp')
    serializer_class = ArrivedOrderSerializer

class ControlCenterViewSet(viewsets.ModelViewSet):
    queryset = ControlCenter.objects.all().order_by('-created_at')
    serializer_class = ControlCenterSerializer

class CollateralManagerViewSet(viewsets.ModelViewSet):
    queryset = CollateralManager.objects.all().order_by('-created_at')
    serializer_class = CollateralManagerSerializer

# Templates
from .forms import PackageInfoForm, LogisticsStatusForm

def package_info_create(request):
    if request.method == 'POST':
        form = PackageInfoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('package_info_list')
    else:
        form = PackageInfoForm()
    return render(request, 'package_info_create.html', {'form': form})

def package_info_list(request):
    package_infos = PackageInfo.objects.all()
    return render(request, 'package_info_list.html', {'package_infos': package_infos})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import LogisticsStatusForm
from .models import LogisticsStatus

@login_required
def create_logistics_status(request):
    if request.method == 'POST':
        form = LogisticsStatusForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if form.is_valid():
            form.save()
            return redirect('logistics_status_list')
    else:
        form = LogisticsStatusForm()
    return render(request, 'create_logistics.html', {'form': form})
    
@login_required
def logistics_status_list(request):
    logistics_statuses = LogisticsStatus.objects.all().order_by('-timestamp')
    return render(request, 'logistics_list.html', {'logistics_statuses': logistics_statuses})

@login_required
def create_logistics_package(request):
    if request.method == 'POST':
        form = LogisticsStatusForm(request.POST, request.FILES)  # Include request.FILES for file uploads
        if form.is_valid():
            form.save()
            return redirect('logistics_status_list')
    else:
        form = LogisticsStatusForm()
    return render(request, 'create_logistics.html', {'form': form})

from django.shortcuts import render, redirect
from invoice_generator.forms import InvoiceForm
from inventory_management.models import InventoryBreedSales
from django.forms import formset_factory

from django.db.models import F

@login_required
def create_multiple_models_for_logistics(request):
    LogisticsStatusFormSet = formset_factory(LogisticsStatusForm, extra=1)
    PackageInfoFormSet = formset_factory(PackageInfoForm, extra=1)
    InvoiceFormSet = formset_factory(InvoiceForm, extra=1)

    if request.method == 'POST':
        logistics_formset = LogisticsStatusFormSet(request.POST, request.FILES, prefix='logistics')
        package_formset = PackageInfoFormSet(request.POST, prefix='package')
        invoice_formset = InvoiceFormSet(request.POST, prefix='invoice')

        if logistics_formset.is_valid() and package_formset.is_valid() and invoice_formset.is_valid():
            for form in logistics_formset:
                logistics_instance = form.save(commit=False)
                package_form = package_formset[logistics_formset.forms.index(form)]
                invoice_form = invoice_formset[logistics_formset.forms.index(form)]

                package_instance = package_form.save()
                invoice_instance = invoice_form.save()

                logistics_instance.package_info = package_instance
                logistics_instance.invoice = invoice_instance
                logistics_instance.save()

                # Deduct from InventoryBreedSales
                breed = invoice_instance.breed
                part_name = invoice_instance.part_name
                quantity = invoice_instance.quantity
                weight = invoice_instance.weight

                inventory_sales = InventoryBreedSales.objects.filter(
                    breed=breed,
                    part_name=part_name
                )
                for inventory_sale in inventory_sales:
                    if inventory_sale.quantity >= quantity:
                        inventory_sale.quantity = F('quantity') - quantity
                        inventory_sale.weight = F('weight') - weight
                        inventory_sale.save(update_fields=['quantity', 'weight'])
                        break  # Exit the loop once deducted from one inventory sale

            return render(request, 'logistics_creation_success.html')

    else:
        logistics_formset = LogisticsStatusFormSet(prefix='logistics')
        package_formset = PackageInfoFormSet(prefix='package')
        invoice_formset = InvoiceFormSet(prefix='invoice')

    return render(request, 'combined_logistics_creation.html', {'logistics_formset': logistics_formset,
                                                                'package_formset': package_formset,
                                                                'invoice_formset': invoice_formset})

@login_required
def list_logistics_package(request):
    logistics_statuses = LogisticsStatus.objects.all().order_by('-timestamp')
    return render(request, 'logistics_list.html', {'logistics_statuses': logistics_statuses})

# Bank Bil of lading

@login_required
def bank_list_bill_of_lading(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
        
    bols = LogisticsStatus.objects.all().order_by('-timestamp')
    return render(request, 'bill_of_lading.html', {'bols': bols})

@login_required
def seller_list_bill_of_lading(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
        
    bols = LogisticsStatus.objects.all().order_by('-timestamp')
    return render(request, 'bill_of_lading.html', {'bols': bols})


@login_required
def seller_list_bill_of_lading(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
        
    bols = LogisticsStatus.objects.all().order_by('-timestamp')
    return render(request, 'bill_of_lading.html', {'bols': bols})

from django.http import HttpResponse
from django.http import FileResponse

@login_required
def seller_view_bill_of_lading(request, pk):
    # Ensure the user has permission to download the bill of lading
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
    
    # Retrieve the LogisticsStatus instance
    logistics_status = get_object_or_404(LogisticsStatus, pk=pk)
    
    # Check if the bill of lading file exists
    if not logistics_status.bill_of_lading:
        return HttpResponse("Bill of lading file not found.", status=404)
    
    # Serve the bill of lading file for download
    file_path = logistics_status.bill_of_lading.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{logistics_status.bill_of_lading.name}"'
        return response

@login_required
def download_bill_of_lading(request, pk):
    # Ensure the user has permission to view the bill of lading
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
    
    # Retrieve the LogisticsStatus instance
    logistics_status = get_object_or_404(LogisticsStatus, pk=pk)
    
    # Check if the bill of lading file exists
    if not logistics_status.bill_of_lading:
        return HttpResponse("Bill of lading file not found.", status=404)
    
    # Serve the bill of lading file for viewing
    file_path = logistics_status.bill_of_lading.path
    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        return HttpResponse("Bill of lading file not found.", status=404)

# seller
@login_required
def seller_download_bill_of_lading(request, pk):
    # Retrieve the LogisticsStatus instance associated with the current user
    logistics_status = get_object_or_404(LogisticsStatus, pk=pk, seller=request.user)
    
    # Check if the bill of lading file exists
    if not logistics_status.bill_of_lading:
        return HttpResponse("Bill of lading file not found.", status=404)
    
    # Serve the bill of lading file for viewing
    file_path = logistics_status.bill_of_lading.path
    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        return HttpResponse("Bill of lading file not found.", status=404)


# # Read BOL

# @login_required
# def bank_download_bill_of_lading(request, pk):
#     # Ensure the user has permission to download the bill of lading
#     if request.user.role != 'bank' and not request.user.is_superuser:
#         return redirect('unauthorized')
    
#     # Retrieve the LogisticsStatus instance
#     logistics_status = get_object_or_404(LogisticsStatus, pk=pk)
    
#     # Check if the bill of lading file exists
#     if not logistics_status.bill_of_lading:
#         return HttpResponse("Bill of lading file not found.", status=404)
    
#     # Serve the bill of lading file for download
#     file_path = logistics_status.bill_of_lading.path
#     with open(file_path, 'rb') as file:
#         response = HttpResponse(file.read(), content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="{logistics_status.bill_of_lading.name}"'
#         return response





