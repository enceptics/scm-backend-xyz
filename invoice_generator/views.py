# invoice_generator/views.py
from rest_framework import viewsets
from .models import Invoice, Buyer, PurchaseOrder, LetterOfCreditSellerToTrader
from .serializers import InvoiceSerializer, BuyerSerializer
from rest_framework import mixins
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from .models import Invoice, Buyer, LetterOfCredit, LetterOfCreditSellerToTrader, PurchaseOrder, ProformaInvoiceFromTraderToSeller, Quotation, DocumentToSeller
from logistics.models import LogisticsStatus
from .serializers import InvoiceSerializer, BuyerSerializer, LetterOfCreditSerializer, LetterOfCreditSellerToTraderSerializer, PurchaseOrderSerializer, ProformaInvoiceFromTraderToSellerSerializer, QuotationSerializer, DocumentToSellerSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from custom_registration.models import CustomUser, Seller 
from rest_framework.decorators import action
from .notifications import send_lc_to_the_bank_and_po_to_breeder
from django.core.mail import send_mail
from django.conf import settings

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.generic import View

from django.utils.html import strip_tags

from django.core.mail import send_mail
from django.template.loader import render_to_string

# DOCUMENT SCANNER

from django.http import JsonResponse
from PyPDF2 import PdfFileReader

def scan_pdf(request):
    if request.method == 'POST' and request.FILES['pdf_file']:
        pdf_file = request.FILES['pdf_file']
        try:
            text = extract_text_from_pdf(pdf_file)
            return JsonResponse({'text': text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'POST request with PDF file required'}, status=400)

def extract_text_from_pdf(pdf_file):
    text = ''
    with pdf_file.open() as file:
        reader = PdfFileReader(file)
        num_pages = reader.numPages
        for page_number in range(num_pages):
            page = reader.getPage(page_number)
            text += page.extractText()
    return text


class PurchaseOrderViewSet(viewsets.ModelViewSet):

    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Send email notification to all traders associated with the abattoir
         # Send email notification to the sender
        if serializer.validated_data.get('confirmed', False):
            subject = 'Purchase Order Confirmation '
            sender_email = 'pascalouma54@gmail.com'  # Assuming seller has an email field
            receiver_email = instance.trader_name.breeder.email  # Assuming trader_name is a ForeignKey to a model with an email field

            # Render email template
            email_context = {'purchase_order': instance}
            email_body = render_to_string('po_and_breeder_trade_confirmation_email_template.html', email_context)

            # Send email
            plain_email_body = strip_tags(email_body)  # Strip HTML tags for the plain message
            send_mail(subject, plain_email_body, settings.DEFAULT_FROM_EMAIL, [sender_email, receiver_email], html_message=email_body)

        return Response(serializer.data)

class LetterOfCreditSellerToTraderViewSet(viewsets.ModelViewSet):
    queryset = LetterOfCreditSellerToTrader.objects.all()
    serializer_class = LetterOfCreditSellerToTraderSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

         # Send email notification to the sender
        if serializer.validated_data.get('confirmed', False):
            subject = 'Letter of credit'
            sender_email = 'pascalouma54@gmail.com'  # Assuming seller has an email field
            receiver_email = instance.trader_name.user.email  # Assuming trader_name is a ForeignKey to a model with an email field

            # Render email template
            email_context = {'purchase_order': instance}
            email_body = render_to_string('po_and_breeder_trade_confirmation_email_template.html', email_context)

            # Send email
            plain_email_body = strip_tags(email_body)  # Strip HTML tags for the plain message
            send_mail(subject, plain_email_body, settings.DEFAULT_FROM_EMAIL, [sender_email, receiver_email], html_message=email_body)

        return Response(serializer.data)


class ProformaInvoiceFromTraderToSellerViewSet(viewsets.ModelViewSet):
    queryset = ProformaInvoiceFromTraderToSeller.objects.all()
    serializer_class = ProformaInvoiceFromTraderToSellerSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

         # Send email notification to the sender
        if serializer.validated_data.get('confirmed', False):
            subject = 'Purchase Order Confirmation'
            sender_email = 'pascalouma54@gmail.com'  # Assuming seller has an email field
            receiver_email = instance.trader_name.user.email  # Assuming trader_name is a ForeignKey to a model with an email field

            # Render email template
            email_context = {'purchase_order': instance}
            email_body = render_to_string('po_and_breeder_trade_confirmation_email_template.html', email_context)

            # Send email
            plain_email_body = strip_tags(email_body)  # Strip HTML tags for the plain message
            send_mail(subject, plain_email_body, settings.DEFAULT_FROM_EMAIL, [sender_email, receiver_email], html_message=email_body)

        return Response(serializer.data)

class BuyerAllViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer

class BuyerViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.all().order_by('-created_at')
    serializer_class = BuyerSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Modify the request data to associate the buyer with the user
        request.data['user'] = request.user.id  # Assuming user is authenticated
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        # Retrieve the corresponding Seller instance based on the user
        buyer = get_object_or_404(CustomUser, id=self.request.user.id)

        # Filter sellers based on the retrieved Seller instance
        return Buyer.objects.filter(buyer=buyer)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-invoice_date')
    serializer_class = InvoiceSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print(f"User: {self.request.user}")

        # Retrieve the corresponding Buyer instance based on the user
        buyer = get_object_or_404(Buyer, buyer=self.request.user)

        # Filter invoices based on the retrieved Buyer instance
        return Invoice.objects.filter(buyer=buyer)

    def perform_create(self, serializer):
        try:
            # Check if a buyer is associated with the invoice
            buyer_data = serializer.validated_data.get('buyer', None)

            if buyer_data:
                # If a buyer is provided, create or retrieve the buyer
                buyer, created = Invoice.objects.get_or_create(**buyer_data)

                # Update the serializer's buyer field with the CustomUser instance
                serializer.validated_data['buyer'] = buyer  # Use the newly created or retrieved buyer

            # Calculate the total price before saving the object
            serializer.validated_data['total_price'] = (
                serializer.validated_data['quantity'] * serializer.validated_data['unit_price']
            )
            serializer.save()

        except Exception as e:
            print(f"Error in perform_create: {e}")
            raise

class InvoiceAllViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-invoice_date')
    serializer_class = InvoiceSerializer

# Buyer and quotation

class QuotationAllViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.all().order_by('-created_at')
    serializer_class = QuotationSerializer


class QuotationViewSet(viewsets.ModelViewSet):
    queryset = Quotation.objects.all().order_by('-created_at')
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        # Retrieve the corresponding Buyer instance based on the user
        buyer = get_object_or_404(Buyer, buyer=self.request.user)

        # Filter invoices based on the retrieved Buyer instance
        return Quotation.objects.filter(buyer=buyer)
        
    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.confirm:
            seller_email = 'intellima.tech@gmail.com'  # Fixed sender's email address
            subject = 'Quotation Confirmation'
            
            # Buyer's name
            buyer_name = f"{instance.buyer.buyer.first_name} {instance.buyer.buyer.last_name}" if instance.buyer.buyer else 'Unknown Buyer'
            buyer_email = instance.buyer.buyer.email
            # Seller's name
            seller_name = f"{instance.seller.seller.first_name} {instance.seller.seller.last_name}" if instance.seller else 'Unknown Seller'
            
            # Email context
            context = {'buyer_name': buyer_name, 'seller_name': seller_name}
            html_message = render_to_string('quotation_confirmation_email.html', context)
            plain_message = strip_tags(html_message)

            # Send email to the buyer from the fixed sender's email address
            from_email = seller_email
            buyer_email = buyer_email  # Replace with actual buyer's email
            recipient_list = [buyer_email]
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            
            # Update a field in the buyer's model (e.g., has_confirmed_quotation)
            instance.buyer.has_confirmed_quotation = True
            instance.buyer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

class LetterOfCreditAllViewSet(viewsets.ModelViewSet):
    queryset = LetterOfCredit.objects.all().order_by('-issue_date')
    serializer_class = LetterOfCreditSerializer
    # lookup_field = 'pk'  # Ensure this line is present

class DocumentToSellerViewSet(viewsets.ModelViewSet):
    queryset = DocumentToSeller.objects.all()
    serializer_class = DocumentToSellerSerializer

class LetterOfCreditViewSet(viewsets.ModelViewSet):
    queryset = LetterOfCredit.objects.all().order_by('-issue_date')
    serializer_class = LetterOfCreditSerializer
    permission_classes = [IsAuthenticated]
    # lookup_field = 'pk'  # Ensure this line is present

    def get_queryset(self):
        print(f"User: {self.request.user}")

        # Retrieve the corresponding Buyer instance based on the user
        buyer = get_object_or_404(Buyer, buyer=self.request.user)

        # Filter invoices based on the retrieved Buyer instance
        return LetterOfCredit.objects.filter(buyer=buyer)

    def send_email_notification(self, recipient_email, subject, message):
        send_mail(
            subject,
            message,
            'pascalouma54@gmail.com',  # 
            [recipient_email],
            fail_silently=False,
        )

    @action(detail=False, methods=['post'])
    def upload_lc_document(self, request, *args, **kwargs):
        try:
            # Retrieve the currently logged-in user
            buyer = self.request.user  # Change this line

            buyer = request.buyer
            print(f"User: {buyer}")

            # Create the Letter of Credit
            letter_of_credit = LetterOfCredit.objects.create(buyer=buyer, status='received')
            
            # Handle LC document upload
            lc_document = request.FILES.get('lc_document')
            letter_of_credit.lc_document = lc_document
            letter_of_credit.save()

            # Notify the buyer and bank about the successful upload
            self.send_lc_upload_notification(letter_of_credit)

            return Response({'message': 'Letter of Credit document uploaded successfully.'}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error uploading letter of credit document: {e}")
            return Response({'error': 'Error uploading letter of credit document'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def send_lc_upload_notification(self, letter_of_credit):
        if letter_of_credit.buyer:
            buyer_email = letter_of_credit.buyer.username.email

            # Send email to the buyer
            buyer_subject = 'Letter of Credit Document Uploaded - Processing'
            buyer_message = render_to_string('email_templates/lc_upload_notification_buyer.html', {'letter_of_credit': letter_of_credit})
            self.send_email_notification(buyer_email, buyer_subject, buyer_message)

        # You can also send an email to the bank if needed
        if letter_of_credit.bank_email:
            bank_subject = 'Letter of Credit Document Uploaded - Processing'
            bank_message = render_to_string('email_templates/lc_upload_notification_bank.html', {'letter_of_credit': letter_of_credit})
            self.send_email_notification(letter_of_credit.bank_email, bank_subject, bank_message)

    @action(detail=True, methods=['post'])
    def notify_lc_received(self, request, pk=None):
        letter_of_credit = self.get_object()

        # Check if the letter of credit has an associated invoice
        if letter_of_credit.invoice:
            invoice = letter_of_credit.invoice

            # Check if the invoice has a buyer associated with it
            if invoice.buyer:
                buyer_email = invoice.buyer.username.email

                # Send email to the buyer
                buyer_subject = 'Letter of Credit Received - Processing'
                buyer_message = render_to_string('email_templates/lc_received_notification_buyer.html', {'invoice': invoice})
                self.send_email_notification(buyer_email, buyer_subject, buyer_message)

            # You can also send an email to the bank if needed
            if invoice.bank_email:
                bank_subject = 'Letter of Credit Received - Processing'
                bank_message = render_to_string('email_templates/lc_received_notification_bank.html', {'invoice': invoice})
                self.send_email_notification(invoice.bank_email, bank_subject, bank_message)

        return Response({'message': 'Email notifications sent successfully.'}, status=status.HTTP_200_OK)

def download_invoice_document(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    file_path = invoice.invoice_document.path  # Assuming invoice_document is the FileField    with open(file_path, 'rb') as file:
    response = HttpResponse(file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={invoice.invoice_document.name}'
    return response
        
def download_lc_document(request, lc_id):
    lc = get_object_or_404(LetterOfCredit, id=lc_id)
    file_path = lc.lc_document.path  # Assuming lc_document is the FileField    with open(file_path, 'rb') as file:
    response = HttpResponse(file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={lc.lc_document.name}'
    return response


# TEMPLATES

# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Quotation
from .forms import QuotationForm, LetterOfCreditForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib.auth.decorators import login_required

@login_required
def quotation_list(request):
    """View to display a list of quotations for the currently logged-in user."""
    # Retrieve the currently logged-in user
    user = request.user

    try:
        # Attempt to get the associated Seller instance for the logged-in user
        seller = user.seller_set.get()
        # Filter quotations based on the seller
        quotations = Quotation.objects.filter(seller=seller).order_by('-created_at')    
    except Seller.DoesNotExist:
        # If the user is not associated with a Seller instance, set quotations to an empty queryset
        quotations = Quotation.objects.none()

    # Paginate the filtered quotations queryset
    paginator = Paginator(quotations, 10)  # Show 10 quotations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'quotation_list.html', {'page_obj': page_obj})
        
def quotation_detail(request, quotation_id):
    """View to display details of a specific quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    return render(request, 'quotation_detail.html', {'quotation': quotation})

@login_required
def buyer_quotation_list(request):
    """View to display a list of quotations intended for the buyer."""
    # Retrieve the Buyer instance corresponding to the logged-in user
    try:
        buyer = Buyer.objects.get(buyer=request.user)  # Assuming the field name is 'user' in Buyer model
    except Buyer.DoesNotExist:
        # Handle the case where the buyer does not exist
        # You may want to redirect the user or display an error message
        buyer = None

    if buyer:
        # Filter quotations based on the buyer's information
        quotations = Quotation.objects.filter(buyer=buyer).order_by('-created_at')

        # Render the template with filtered quotations
        return render(request, 'buyer_quotation_list.html', {'quotations': quotations})
    else:
        # Handle the case where the buyer does not exist
        # You may want to redirect the user or display an error message
        return render(request, 'buyer_quotation_list.html', {'quotations': None})

@login_required
def confirm_quotation(request, quotation_id):
    """View to confirm a quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)

    if not quotation.confirm:
        quotation.confirm = True
        quotation.save()
        messages.success(request, 'Quotation confirmed successfully.')
    else:
        messages.error(request, 'Quotation is already confirmed.')

    return redirect('quotation_confirmed')

def quotation_confirmed(request):
    """Success template for quotation confirmation."""
    return render(request, 'confirm_quotation.html')

@login_required
def reject_quotation(request, quotation_id):
    """View to reject an existing quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    if request.method == 'POST':
        explanation = request.POST.get('explanation', '')
        quotation.explanation = explanation  # Save the explanation to the quotation
        quotation.rejected = True  # Set the rejected field to True
        quotation.save()  # Save the changes to the database
        messages.success(request, 'Quotation rejected successfully.')
        return redirect('reject_quotation')  # Redirect to the quotation list page
    else:
        return render(request, 'reject_quotation.html', {'quotation': quotation})

def reject_quotation(request):
    """Success template for quotation confirmation."""
    return render(request, 'reject_quotation.html')

from django.contrib import messages

from django.core.files.storage import FileSystemStorage
import os

@login_required
def create_quotation(request):
    """View to create a new quotation."""
    if request.method == 'POST':
        form = QuotationForm(request.POST, request.FILES)
        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.seller = Seller.objects.get(seller=request.user)
            quotation.save()

            # Save the uploaded PDF file to a specific directory
            pdf_file = request.FILES.get('pdf_file')
            if pdf_file:
                # Construct the file path where the PDF file will be saved
                file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_quotations', f'quotation_{quotation.id}.pdf')
                # Save the file to the file system
                fs = FileSystemStorage()
                fs.save(file_path, pdf_file)

            # Redirect to the success template upon successful creation
            return redirect('quotation_created')
        else:
            # If the form is not valid, display error messages
            messages.error(request, 'Failed to create quotation. Please check the form.')
    else:
        # Initialize the form with the seller field set to the seller associated with the logged-in user
        seller = Seller.objects.get(seller=request.user)
        form = QuotationForm(initial={'seller': seller})
    
    return render(request, 'create_quotation.html', {'form': form})

def quotation_created(request):
    """Success template for quotation creation."""
    return render(request, 'quotation_success.html')

def update_quotation(request, quotation_id):
    """View to update an existing quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    if request.method == 'POST':
        # Process form data
        # Example: Update quotation object based on form data
        # quotation.seller = request.POST['seller']
        # quotation.save()
        return JsonResponse({'success': True})
    else:
        return render(request, 'update_quotation.html', {'quotation': quotation})

def delete_quotation(request, quotation_id):
    """View to delete an existing quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    quotation.delete()
    return JsonResponse({'success': True})

# LC
@login_required
def letter_of_credit_create(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        form = LetterOfCreditForm(request.POST, request.FILES)
        
        # Handling validation error for non-PDF documents
        if 'lc_document' in request.FILES and not request.FILES['lc_document'].name.endswith('.pdf'):
            form.add_error('lc_document', 'Only PDF documents are allowed.')
            
        if form.is_valid():
            form.save()
            # Redirect to a success URL or a specific view
            return redirect('lc_creation_success')  # Assuming 'lc_successfully_created' is a URL pattern name
        # If the form is not valid, re-render the form with validation errors
    else:
        form = LetterOfCreditForm()
    
    return render(request, 'letter_of_credit_create.html', {'form': form})

def lc_creation_success(request):
    return render(request, 'lc_successfully_created.html')
    
@login_required
def all_letter_of_credit_list(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')

    letters_of_credit = LetterOfCredit.objects.all().order_by('-issue_date')
    context = {
        'letters_of_credit': letters_of_credit,
    }
    return render(request, 'all_letter_of_credit_list.html', context)

@login_required
def seller_letter_of_credit_list(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
    try:
        seller = Seller.objects.get(seller=request.user)
    except Seller.DoesNotExist:
        seller = None

    if seller:
        letters = LetterOfCredit.objects.filter(seller=seller).order_by('-issue_date')
        return render(request, 'seller_letter_of_credit_list.html', {'letters': letters})
    else:
        return render(request, 'error.html', {'message': 'You are not authorized to view this page.'})

@login_required
def buyer_letter_of_credit_list(request):
    try:
        buyer = Buyer.objects.get(buyer=request.user)
    except Buyer.DoesNotExist:
        buyer = None

    if buyer:
        letters = LetterOfCredit.objects.filter(buyer=buyer).order_by('-issue_date')
        return render(request, 'buyer_letter_of_credit_list.html', {'letters': letters})
    else:
        return render(request, 'error.html', {'message': 'You are not authorized to view this page.'})

from django.http import JsonResponse

def update_letter_of_credit_status(request, pk):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        rejection_reason = request.POST.get('reason')  # get rejection reason from POST data
        collection_market = request.POST.get('collection_market')  # Get the collection market from POST data

        if new_status:
            try:
                # Retrieve the LetterOfCredit object using the provided pk
                letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
                
                # Update the status
                letter_of_credit.status = new_status
                
                # If status is rejected, save the rejection reason
                if new_status == 'rejected':
                    letter_of_credit.rejection_reason = rejection_reason
                elif new_status == 'approved':
                    letter_of_credit.collection_market = collection_market  # Save the collection market

                letter_of_credit.save()
                
                # Pass the letter_of_credit object to the context
                context = {'letter': letter_of_credit}
                
                # Render success HTML template with the context
                return render(request, 'lc_success.html', context)
            except LetterOfCredit.DoesNotExist:
                # If the LetterOfCredit object does not exist, render an error HTML template
                return render(request, 'lc_error.html')
        else:
            # If the 'status' field is missing in the POST data, return an error response
            return HttpResponse('Missing status field in POST data', status=400)
    else:
        # If the request method is not POST, return an error response
        return HttpResponse('Only POST requests are allowed', status=405)
        
def letter_of_credit_detail(request, pk):
    letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
    return render(request, 'letter_of_credit_detail.html', {'letter_of_credit': letter_of_credit})

# Extract Pdf content

import re
import PyPDF2
from PyPDF2 import PdfReader
from .forms import LetterOfCreditForm
from .models import LetterOfCredit
import PyPDF2

@login_required
def letter_of_credit_create(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
    
    if request.method == 'POST':
        form = LetterOfCreditForm(request.POST, request.FILES)
        
        # Handling validation error for non-PDF documents
        if 'lc_document' in request.FILES and not request.FILES['lc_document'].name.endswith('.pdf'):
            form.add_error('lc_document', 'Only PDF documents are allowed.')
            
        if form.is_valid():
            form.save()
            # Redirect to a success URL or a specific view
            return redirect('lc_creation_success')  # Assuming 'lc_successfully_created' is a URL pattern name
    else:
        form = LetterOfCreditForm()
    
    return render(request, 'letter_of_credit_create.html', {'form': form})

def lc_creation_success(request):
    return render(request, 'lc_successfully_created.html')
    
@login_required
def all_letter_of_credit_list(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')

    letters_of_credit = LetterOfCredit.objects.all().order_by('-issue_date')
    context = {
        'letters_of_credit': letters_of_credit,
    }
    return render(request, 'all_letter_of_credit_list.html', context)

@login_required
def seller_letter_of_credit_list(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
    try:
        seller = Seller.objects.get(seller=request.user)
    except Seller.DoesNotExist:
        seller = None

    if seller:
        letters = LetterOfCredit.objects.filter(seller=seller).order_by('-issue_date')
        return render(request, 'seller_letter_of_credit_list.html', {'letters': letters})
    else:
        return render(request, 'error.html', {'message': 'You are not authorized to view this page.'})

@login_required
def buyer_letter_of_credit_list(request):
    try:
        buyer = Buyer.objects.get(buyer=request.user)
    except Buyer.DoesNotExist:
        buyer = None

    if buyer:
        letters = LetterOfCredit.objects.filter(buyer=buyer).order_by('-issue_date')
        return render(request, 'buyer_letter_of_credit_list.html', {'letters': letters})
    else:
        return render(request, 'error.html', {'message': 'You are not authorized to view this page.'})

@login_required
def update_letter_of_credit_status(request, pk):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        rejection_reason = request.POST.get('reason')  # get rejection reason from POST data
        collection_market = request.POST.get('collection_market')  # Get the collection market from POST data

        if new_status:
            try:
                # Retrieve the LetterOfCredit object using the provided pk
                letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
                
                # Update the status
                letter_of_credit.status = new_status
                
                # If status is rejected, save the rejection reason
                if new_status == 'rejected':
                    letter_of_credit.rejection_reason = rejection_reason
                elif new_status == 'approved':
                    letter_of_credit.collection_market = collection_market  # Save the collection market

                letter_of_credit.save()
                
                # Pass the letter_of_credit object to the context
                context = {'letter': letter_of_credit}
                
                # Render success HTML template with the context
                return render(request, 'lc_success.html', context)
            except LetterOfCredit.DoesNotExist:
                # If the LetterOfCredit object does not exist, render an error HTML template
                return render(request, 'lc_error.html')
        else:
            # If the 'status' field is missing in the POST data, return an error response
            return HttpResponse('Missing status field in POST data', status=400)
    else:
        # If the request method is not POST, return an error response
        return HttpResponse('Only POST requests are allowed', status=405)
        
@login_required
def letter_of_credit_detail(request, pk):
    letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
    return render(request, 'letter_of_credit_detail.html', {'letter_of_credit': letter_of_credit})

@login_required
def extracted_data_list(request):
    allowed_roles = ['superuser', 'seller', 'breeder']
    if not request.user.is_superuser and request.user.role not in allowed_roles:
        return redirect('unauthorized')
    
    approved_lc_documents = LetterOfCredit.objects.filter(status='approved').order_by('-issue_date')
    extracted_data_list = []
    for lc_document in approved_lc_documents:
        extracted_data = extract_lc_data(lc_document.lc_document.path)
        extracted_data_list.append(extracted_data)
    return render(request, 'document_viewer/document_detail.html', {'extracted_data_list': extracted_data_list})

def lc_document_extracted_content_detail(request, lc_document_id):
    lc_document = LetterOfCredit.objects.get(pk=lc_document_id)
    extracted_data = extract_lc_data(lc_document.lc_document.path)
    return render(request, 'document_viewer/active_orders.html', {'lc_document': lc_document, 'extracted_data': extracted_data})

def extract_lc_data(pdf_path):
    extracted_data = {
        'buyer_name': 'Unknown',
        'buyer_email': 'Unknown',
        'buyer_address': 'Unknown',
        'buyer_country': 'Unknown',
        'seller_name': 'Unknown',
        'seller_email': 'Unknown',
        'seller_address': 'Unknown',
        'seller_country': 'Unknown',
        'product': 'Unknown',
        'unit_price': 'Unknown',
        'created_on': 'Unknown',
        'quantity': 'Unknown',  # Add quantity field
    }

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            text = reader.pages[page_num].extract_text()

            # Extracting buyer's information
            buyer_match = re.search(r'Full Name:\s*(.*?)\s*Email:\s*(.*?)\s*Address:\s*(.*?)\s*Country:\s*(.*?)', text, re.DOTALL)
            if buyer_match:
                extracted_data['buyer_name'] = buyer_match.group(1).strip()
                extracted_data['buyer_email'] = buyer_match.group(2).strip()
                extracted_data['buyer_address'] = buyer_match.group(3).strip()
                extracted_data['buyer_country'] = buyer_match.group(4).strip()

            # Extracting seller's information
            seller_match = re.search(r'Full Name:\s*(.*?)\s*Email:\s*(.*?)\s*Address:\s*(.*?)\s*Country:\s*(.*?)', text, re.DOTALL)
            if seller_match:
                extracted_data['seller_name'] = seller_match.group(1).strip()
                extracted_data['seller_email'] = seller_match.group(2).strip()
                extracted_data['seller_address'] = seller_match.group(3).strip()
                extracted_data['seller_country'] = seller_match.group(4).strip()

            # Extracting product information
            product_match = re.search(r'Product:\s*(.*?)\s*Unit Price:\s*(.*?)\s*Created on:\s*(.*?)\s*Delivered by:\s*(.*?)\s*No:\s*(.*?)\s*Message:', text, re.DOTALL)
            if product_match:
                extracted_data['product'] = product_match.group(1).strip()
                extracted_data['unit_price'] = product_match.group(2).strip()
                extracted_data['created_on'] = product_match.group(3).strip()
                extracted_data['quantity'] = product_match.group(4).strip()

    return extracted_data
