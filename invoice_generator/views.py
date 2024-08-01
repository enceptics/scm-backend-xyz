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

from transaction.models import BreaderTrade

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

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

@login_required
def confirm_quotation(request, quotation_id):
    """View to confirm a quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)

    if not quotation.confirm:
        quotation.confirm = True
        quotation.save()

        # Send email notification for approval
        subject = 'Quotation Approved'
        sender_email = settings.DEFAULT_FROM_EMAIL
        receiver_email = quotation.seller.seller.email  # Assuming seller has an email field

        # Render email template
        email_context = {'buyer_name': quotation.buyer.buyer.first_name + " " + quotation.buyer.buyer.last_name,
                         'seller_name': quotation.seller.seller.first_name + " " + quotation.seller.seller.last_name}
        email_body = render_to_string('quotation_confirmation_email.html', email_context)

        # Send email
        plain_email_body = strip_tags(email_body)
        send_mail(subject, plain_email_body, sender_email, [receiver_email], html_message=email_body)

        messages.success(request, 'Quotation confirmed successfully.')
    else:
        messages.error(request, 'Quotation is already confirmed.')

    return redirect('quotation_confirmed')

@login_required
def reject_quotation(request, quotation_id):
    """View to reject an existing quotation."""
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    if request.method == 'POST':
        explanation = request.POST.get('explanation', '')
        quotation.explanation = explanation  # Save the explanation to the quotation
        quotation.rejected = True  # Set the rejected field to True
        quotation.save()  # Save the changes to the database

        # Send email notification for rejection
        subject = 'Quotation Rejected'
        sender_email = settings.DEFAULT_FROM_EMAIL
        receiver_email = quotation.seller.seller.email  # Assuming seller has an email field

        # Render email template
        email_context = {'buyer_name': quotation.buyer.buyer.first_name + " " + quotation.buyer.buyer.last_name,
                         'seller_name': quotation.seller.seller.first_name + " " + quotation.seller.seller.last_name,
                         'explanation': explanation}
        email_body = render_to_string('quotation_rejection_email.html', email_context)

        # Send email
        plain_email_body = strip_tags(email_body)
        send_mail(subject, plain_email_body, sender_email, [receiver_email], html_message=email_body)

        messages.success(request, 'Quotation rejected successfully.')
        return redirect('quotation_reject')  # Redirect to the desired URL after rejection
    else:
        return render(request, 'reject_quotation.html', {'quotation': quotation})

def quotation_reject(request):
    """Success template for quotation confirmation."""
    return render(request, 'reject_quotation.html')

from django.contrib import messages
from io import BytesIO  # Add this import at the beginning of your views.py file

from django.core.files.storage import FileSystemStorage
import os

from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
import os
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.contrib import messages

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import os

@login_required
def create_quotation(request):
    """View to create a new quotation."""
    if request.method == 'POST':
        form = QuotationForm(request.POST, request.FILES)
        if form.is_valid():
            quotation = form.save(commit=False)
            seller = Seller.objects.get(seller=request.user)
            quotation.seller = seller
            quotation.save()

            # Define buyer name and seller name
            buyer_name = quotation.buyer.buyer.first_name
            seller_name = quotation.seller.seller.first_name

            # Generate HTML content for the PDF
            html_content = render_to_string('quotation_pdf_template.html', {'quotation': quotation})

            # Generate PDF from the HTML content
            pdf_file = generate_pdf(html_content)

            # Save the PDF file to a specific directory
            file_path = os.path.join(settings.MEDIA_ROOT, 'pdf_quotations', f'quotation_{quotation.id}.pdf')
            with open(file_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Send email to the buyer with PDF attachment
            buyer_email_subject = 'New Quotation Received'
            buyer_email_message = render_to_string('buyer_quotation_email.html', {'quotation': quotation, 'buyer_name': buyer_name})
            buyer_email_text_content = strip_tags(buyer_email_message)
            buyer_email = EmailMultiAlternatives(buyer_email_subject, buyer_email_text_content, settings.DEFAULT_FROM_EMAIL, [quotation.buyer.buyer.email])
            buyer_email.attach_alternative(buyer_email_message, "text/html")
            buyer_email.attach_file(file_path)
            buyer_email.send()

            # Send email to the seller with PDF attachment
            seller_email_subject = 'Quotation Sent Successfully'
            seller_email_message = render_to_string('seller_quotation_email.html', {'quotation': quotation, 'seller_name': seller_name})
            seller_email_text_content = strip_tags(seller_email_message)
            seller_email = EmailMultiAlternatives(seller_email_subject, seller_email_text_content, settings.DEFAULT_FROM_EMAIL, [seller.seller.email])
            seller_email.attach_alternative(seller_email_message, "text/html")
            seller_email.attach_file(file_path)
            seller_email.send()

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

def generate_pdf(html_content):
    """Function to generate PDF from HTML content."""
    # Create a PDF document
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    
    if not pdf.err:
        # Return the generated PDF content
        return result.getvalue()
    else:
        # Handle error while generating PDF
        raise Exception("Error generating PDF: %s" % pdf.err)



def quotation_created(request):
    """Success template for quotation creation."""
    return render(request, 'quotation_success.html')


def quotation_confirmed(request):
    """Success template for quotation confirmation."""
    return render(request, 'confirm_quotation.html')

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
    
    letters = LetterOfCredit.objects.all().order_by('-issue_date')
    return render(request, 'all_letter_of_credit_list.html', {'letters': letters})

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

@login_required
def update_letter_of_credit_status(request, pk):
    if request.method == 'POST':
        new_status = request.POST.get('status')
        rejection_reason = request.POST.get('reason', '')
        collection_market = request.POST.get('collection_market', '')
        collection_date = request.POST.get('collection_date', '')

        if new_status:
            try:
                letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
                letter_of_credit.status = new_status

                extracted_data = {}  # Initialize extracted_data to store extracted values

                if new_status == 'rejected':
                    letter_of_credit.rejection_reason = rejection_reason

                    # Send email notification for rejection
                    subject = 'Letter of Credit Rejection'
                    sender_email = settings.DEFAULT_FROM_EMAIL
                    receiver_email = letter_of_credit.buyer.buyer.email

                    buyer_name = letter_of_credit.buyer.buyer.first_name + " " + letter_of_credit.buyer.buyer.last_name
                    seller_name = letter_of_credit.seller.seller.first_name + " " + letter_of_credit.seller.seller.last_name

                    email_context = {
                        'buyer_name': buyer_name,
                        'seller_name': seller_name,
                        'rejection_reason': rejection_reason,
                    }
                    email_body = render_to_string('lc_rejection_email_template.html', email_context)
                    plain_email_body = strip_tags(email_body)
                    send_mail(subject, plain_email_body, sender_email, [receiver_email], html_message=email_body)

                elif new_status == 'approved':
                    letter_of_credit.collection_market = collection_market
                    letter_of_credit.collection_date = collection_date

                    # Extract data from the PDF
                    pdf_path = letter_of_credit.lc_document.path
                    extracted_data = extract_lc_data(pdf_path)

                    letter_of_credit.item = extracted_data.get('item', 'Unknown')
                    letter_of_credit.weight = extracted_data.get('weight', 0.0)
                    letter_of_credit.quantity = extracted_data.get('quantity', 0)
                    letter_of_credit.delivery_date = extracted_data.get('delivery_date', None)


                    # Send email notification for approval
                    subject = 'Letter of Credit Approval'
                    sender_email = settings.DEFAULT_FROM_EMAIL
                    receiver_email = letter_of_credit.seller.seller.email

                    buyer_name = letter_of_credit.buyer.buyer.first_name + " " + letter_of_credit.buyer.buyer.last_name
                    seller_name = letter_of_credit.seller.seller.first_name + " " + letter_of_credit.seller.seller.last_name

                    email_context = {
                        'buyer_name': buyer_name,
                        'seller_name': seller_name,
                    }
                    email_body = render_to_string('lc_approval_email_template.html', email_context)
                    plain_email_body = strip_tags(email_body)
                    send_mail(subject, plain_email_body, sender_email, [receiver_email], html_message=email_body)

                letter_of_credit.save()

                # Prepare context for the template
                context = {
                    'letter': letter_of_credit,
                    'extracted_data': extracted_data,
                    'new_data': True  # Set this based on your actual logic if needed
                }

                return render(request, 'lc_success.html', context)
            except LetterOfCredit.DoesNotExist:
                return render(request, 'lc_error.html', {'message': 'Letter of Credit not found'})
        else:
            return HttpResponse('Missing status field in POST data', status=400)
    else:
        return HttpResponse('Only POST requests are allowed', status=405)

def letter_of_credit_detail(request, pk):
    letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
    return render(request, 'letter_of_credit_detail.html', {'letter_of_credit': letter_of_credit})

# Extract Pdf content

import re
import PyPDF2
from PyPDF2 import PdfReader
from django.utils.dateparse import parse_date
from .forms import LetterOfCreditForm
from .models import LetterOfCredit
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

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
            return redirect('lc_creation_success')  # Assuming 'lc_creation_success' is a URL pattern name
    else:
        form = LetterOfCreditForm()
    
    return render(request, 'letter_of_credit_create.html', {'form': form})

@login_required
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
def letter_of_credit_detail(request, pk):
    letter_of_credit = get_object_or_404(LetterOfCredit, pk=pk)
    return render(request, 'letter_of_credit_detail.html', {'letter_of_credit': letter_of_credit})

# Convert weight to quantity
def convert_weight_to_quantity(item, weight):
    conversion_rates = {
        'Goat Meat': 25,  # kg per goat
        'Cow Meat': 500,  # kg per cow
        'Sheep Meat': 30,  # kg per sheep
        'Chicken Meat': 2,  # kg per chicken
        'Avocado': 0.2,  # kg per avocado (example rate, adjust as needed)
    }
    if item in conversion_rates:
        return weight / conversion_rates[item]
    return 0

@login_required
def extracted_data_list(request):
    allowed_roles = ['superuser', 'seller', 'breeder']
    if not request.user.is_superuser and request.user.role not in allowed_roles:
        return redirect('unauthorized')

    approved_lc_documents = LetterOfCredit.objects.filter(status='approved').order_by('-issue_date')

    open_orders = []
    closed_orders = []

    for lc_document in approved_lc_documents:
        extracted_data = {
            'id': lc_document.id,
            'item': lc_document.item,
            'collection_market': lc_document.collection_market,
            'collection_date': lc_document.collection_date,
            'weight': lc_document.weight,
            'quantity': lc_document.quantity,
            'delivery_date': lc_document.delivery_date,
            'status': lc_document.status,
        }
        if lc_document.quantity > 0:
            open_orders.append(extracted_data)
        else:
            closed_orders.append(extracted_data)

    return render(request, 'document_viewer/document_detail.html', {
        'open_orders': open_orders,
        'closed_orders': closed_orders
    })

@login_required
def lc_document_extracted_content_detail(request, lc_document_id):
    lc_document = LetterOfCredit.objects.get(pk=lc_document_id)
    extracted_data = extract_lc_data(lc_document.lc_document.path)
    return render(request, 'document_viewer/active_orders.html', {'lc_document': lc_document, 'extracted_data': extracted_data})

import pdfplumber
import re
from django.utils.dateparse import parse_date
from .models import LetterOfCredit

def extract_lc_data(pdf_path):
    extracted_data = {
        'item': 'Unknown',
        'weight': 'Unknown',
        'delivery_date': 'Unknown',
        'quantity': 'Unknown',
    }

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            # Extracting item information
            item_match = re.search(r'Product:\s*(.*?)\s*Weight:', text)
            if item_match:
                extracted_data['item'] = item_match.group(1).strip()

            # Extracting weight information
            weight_match = re.search(r'Weight:\s*(\d+(\.\d+)?)\s*kg', text)
            if weight_match:
                extracted_data['weight'] = weight_match.group(1).strip()

            # Extracting delivery date information
            date_match = re.search(r'Delivery Date:\s*(\d{4}-\d{2}-\d{2})', text)
            if date_match:
                extracted_data['delivery_date'] = date_match.group(1).strip()

    # Convert weight to float

    try:
        weight_value = re.match(r'(\d+(\.\d+)?)', extracted_data['weight'])
        if weight_value:
            extracted_data['weight'] = float(weight_value.group(1))
        else:
            extracted_data['weight'] = 0.0
    except ValueError:
        extracted_data['weight'] = 0.0

    # Convert weight to quantity
    try:
        extracted_data['quantity'] = int(convert_weight_to_quantity(extracted_data['item'], extracted_data['weight']))
    except Exception as e:
        extracted_data['quantity'] = 0

    return extracted_data