from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Abattoir, Breader, BreaderTrade, AbattoirPaymentToBreader, Inventory
from custom_registration.models import Seller
from .serializers import AbattoirSerializer, BreaderSerializer, BreaderTradeSerializer, AbattoirPaymentToBreaderSerializer, InventorySerializer
import logging
from slaughter_house.models import SlaughterhouseRecord
from .models import AbattoirPaymentToBreader
from rest_framework.decorators import action
from django.http import JsonResponse
from rest_framework.views import APIView
from django.db.models import Sum
from custom_registration.models import BankTeller, CustomerService
from django.template.loader import render_to_string  
from django.utils.html import strip_tags
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from django.utils.html import strip_tags
from logistics.views import ControlCenter
from django.shortcuts import render, redirect
from invoice_generator.models import LetterOfCredit

class AbattoirViewSet(viewsets.ModelViewSet):
    queryset = Abattoir.objects.all()
    serializer_class = AbattoirSerializer

class BreaderViewSet(viewsets.ModelViewSet):
    queryset = Breader.objects.all()
    serializer_class = BreaderSerializer

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    
logger = logging.getLogger(__name__)

class UserSuppliedBreedsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BreaderTrade.objects.all().order_by('-created_at')
    serializer_class = BreaderTradeSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     # Filter the queryset to show only breeds supplied by the logged-in user
    #     return BreaderTrade.objects.filter(breeder=self.request.user)

class BreaderTradeViewSet(viewsets.ModelViewSet):
    queryset = BreaderTrade.objects.all().order_by('-transaction_date')
    serializer_class = BreaderTradeSerializer
    # permission_classes = [IsAuthenticated]

    # def get_queryset(self):

    #         # Retrieve the corresponding Buyer instance based on the user
    #         buyer = get_object_or_404(Seller, seller=self.request.user)

    #         # Filter invoices based on the retrieved Buyer instance
    #         return BreaderTrade.objects.filter(seller=seller)


    def create(self, request, *args, **kwargs):
        try:
            # Get the authenticated breeder (assuming breeder is the trader)
            breeder = request.user

            # Assign the current breeder as the breeder for the newly created trade
            request.data['breeder'] = breeder.id

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            # Log the exception
            logger.error(f"Error in creating BreaderTrade: {str(e)}")
            # Print the error to the console during development
            print(f"Error in creating BreaderTrade: {str(e)}")
            # Return a response indicating the error
            return Response({"error": "An error occurred while creating BreaderTrade."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def breader_info(self, request, pk=None):
        """
        Retrieve detailed information about a specific BreaderTrade.

        Example URL: /api/breader-trade/{pk}/breader-info/
        """
        try:
            breeder_trade = self.get_object()
            breeder_data = BreaderSerializer(breeder_trade.breeder).data
            return Response(breeder_data)
        except Exception as e:
            # Log the exception
            logger.error(f"Error in retrieving Breader information: {str(e)}")
            # Print the error to the console during development
            print(f"Error in retrieving Breader information: {str(e)}")
            # Return a response indicating the error
            return Response({"error": "An error occurred while retrieving Breader information."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def total_quantity(self, request):
        total_quantity_by_breed = BreaderTrade.objects.values('breed').annotate(total_quantity=Sum('breads_supplied'))
        return Response({'total_quantity_by_breed': total_quantity_by_breed})
        print(total_quantity_by_breed)

# ------------Breadder trade single user------

class BreaderTradeSingleSellerViewSet(viewsets.ModelViewSet):
    queryset = BreaderTrade.objects.all().order_by('-created_at')
    serializer_class = BreaderTradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def get_queryset(self):
    #     # Check the value of self.request.user
    #     print("Authenticated User:", self.request.user)

    #     # Filter BreaderTrades based on the currently authenticated user as seller
    #     queryset = BreaderTrade.objects.filter(seller=self.request.user)

    #     # Print the number of BreaderTrade objects returned
    #     print("Number of BreaderTrades:", queryset.count())

    #     # Return the queryset
    #     return queryset

    def get_queryset(self):
        # Retrieve the control center associated with the authenticated user
        control_center = get_object_or_404(ControlCenter, seller=self.request.user)
        # Filter BreaderTrades based on the seller associated with the control center
        queryset = BreaderTrade.objects.filter(control_center=control_center)
        return queryset
    
    def perform_create(self, serializer):
        # Retrieve the control center associated with the authenticated user
        control_center = get_object_or_404(ControlCenter, seller=self.request.user)
        # Retrieve the breeder from the request user (assuming the breeder is the authenticated user)
        breeder = self.request.user
        # Retrieve the seller associated with the control center
        seller = control_center.seller
        # Set the control center, breeder, and seller fields of BreaderTrade
        serializer.save(control_center=control_center, breeder=breeder, seller=seller)
        
# ------------Breadder trade single user------

class BreaderTradeAllSingleSellerViewSet(viewsets.ModelViewSet):
    queryset = BreaderTrade.objects.all().order_by('-created_at')
    serializer_class = BreaderTradeSerializer

# ------------Breadder trade single user------

class BreaderTradeSingleUserViewSet(viewsets.ModelViewSet):
    queryset = BreaderTrade.objects.all().order_by('-created_at')
    serializer_class = BreaderTradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Get the current user
        current_user = request.user

        # Check if the current user has any supplies
        user_supplies = BreaderTrade.objects.filter(breeder=current_user)

        if user_supplies.exists():
            # If the user has supplies, serialize and return them
            serializer = self.get_serializer(user_supplies, many=True)
            return Response(serializer.data)
        else:
            # If the user has not supplied any breeds, return a message
            return Response({"message": "You have not supplied any breeds."})
    
    def perform_create(self, serializer):
        # Set the breeder field of BreaderTrade to the currently authenticated user
        serializer.save(breeder=self.request.user)

    @action(detail=True, methods=['get'])
    def breader_info(self, request, pk=None):
        """
        Retrieve detailed information about a specific BreaderTrade.

        Example URL: /api/breader-trade/{pk}/breader-info/
        """
        try:
            breeder_trade = self.get_object()
            breeder_data = BreaderSerializer(breeder_trade.breeder).data
            return Response(breeder_data)
        except Exception as e:
            # Log the exception
            logger.error(f"Error in retrieving Breader information: {str(e)}")
            # Print the error to the console during development
            print(f"Error in retrieving Breader information: {str(e)}")
            # Return a response indicating the error
            return Response({"error": "An error occurred while retrieving Breader information."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def total_quantity(self, request):
        total_quantity_by_breed = BreaderTrade.objects.values('breed').annotate(total_quantity=Sum('breads_supplied'))
        return Response({'total_quantity_by_breed': total_quantity_by_breed})
        print(total_quantity_by_breed)

# ------------End Breadder trade single user------



class BreaderCountView(APIView):
    def get(self, request, format=None):
        breader_count = Breader.objects.count()
        return Response({'breader_count': breader_count}, status=status.HTTP_200_OK)

# class AbattoirPaymentToBreaderViewSet(viewsets.ModelViewSet):
#     queryset = AbattoirPaymentToBreader.objects.all()
#     serializer_class = AbattoirPaymentToBreaderSerializer


# --------------------ABATTOIR PAYMENT TO BREEDER---------
# Payment

class AbattoirPaymentToBreaderViewSet(viewsets.ModelViewSet):
    queryset = AbattoirPaymentToBreader.objects.all()
    serializer_class = AbattoirPaymentToBreaderSerializer

    def create(self, request, *args, **kwargs):
        # Extract the 'breeder_trade_id' from the request data
        breeder_trade_id = request.data.get('breeder_trade_id')

        # Validate the payment data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the payment instance
        payment_instance = serializer.save()

        # If breeder_trade_id is provided, associate the payment with the BreaderTrade
        if breeder_trade_id:
            breeder_trade_instance = BreaderTrade.objects.get(pk=breeder_trade_id)
            payment_instance.breeder_trade = breeder_trade_instance
            payment_instance.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list_payments(self, request, *args, **kwargs):
        # Retrieve all payments
        payments = self.get_queryset()
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

    def process_payment(self):
        # Example: Update payment status to 'Paid'
        self.status = 'payment_initiated'
        self.save()

        # Add additional payment processing logic here
        # For example, interact with a payment gateway, log payment details, etc.

        # Return True if the payment was successful
        return True

    @action(detail=True, methods=['post'])
    def process_payment_and_notify_breeder(self, request, *args, **kwargs):
        instance = self.get_object()

        # Additional logic related to payment details can be performed here
        # For example, check payment status, update related models, log information, etc.
                                                                          
        # Assume the Breeder model has a 'name' field
        breeder_first_name = instance.breeder_trade.breeder.first_name
        breeder_last_name = instance.breeder_trade.breeder.last_name
        breeder_name = f"{breeder_first_name} {breeder_last_name}"

        # Perform the payment processing (replace with your actual payment processing logic)
        success = instance.process_payment()

        if success:
            # Send email to breeder about payment and breeder trade status
            subject = f"Payment and Breeder Trade Code - {instance.payment_code}"

            # Add breeder's name to the context
            context = {
                'payment': instance,
                'success_message': 'You will receive the payment once the processing is complete.',
                'breeder_name': breeder_name,
                'price': instance.breeder_trade.price,
                'payment_initiation_date': instance.payment_initiation_date,
            }

            message = render_to_string('payment_and_breeder_trade_status_email_template.html', context)
            plain_message = strip_tags(message)
            from_email = 'pascalouma54@gmail.com'
            to_email = [instance.breeder_trade.breeder.email]

            send_mail(subject, plain_message, from_email, to_email, html_message=message)

            # Serialize the payment data and return the response
            serializer = self.get_serializer(instance)

            # Additional logic to send emails to BankTeller and CustomerService
            # Replace the following lines with your actual email sending logic

            # Send email to BankTeller
            # Send email to BankTeller
            # Send email to BankTeller
            bank_teller_emails = BankTeller.objects.values_list('user__email', flat=True)
            bank_teller_subject = 'Bank Teller Notification'

            # Add payment code to the context
            bank_teller_context = {
                'payment': instance,
                'success_message': 'Payment has been initiated. Please review the details.',
                'payment_code': instance.payment_code,
            }

            # Use bank teller email template
            bank_teller_message = render_to_string('bank_teller_status_email_template.html', bank_teller_context)

            send_mail(bank_teller_subject, strip_tags(bank_teller_message), from_email, bank_teller_emails, html_message=bank_teller_message)

            # Send email to CustomerService
            customer_service_emails = CustomerService.objects.values_list('user__email', flat=True)
            customer_service_subject = 'Customer Service Notification'

            # Add relevant context for Customer Service
            customer_service_context = {
                'payment': instance,
                'success_message': 'A new payment has been initiated for breeder. Please review the details.',
                'additional_info': 'You may need to take further action based on the payment details.',
            }

            # Use customer service email template
            customer_service_message = render_to_string('customer_service_status_email_template.html', customer_service_context)

            send_mail(customer_service_subject, strip_tags(customer_service_message), from_email, customer_service_emails, html_message=customer_service_message)

            return Response(serializer.data)
        else:

            # Handle payment failure, return an appropriate response
            return Response({'error': 'Payment processing failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Search breeder details by code

    @action(detail=False, methods=['GET'])
    def search_payment_by_code(self, request, *args, **kwargs):
        payment_code = request.query_params.get('payment_code')
        if not payment_code:
            return Response({'error': 'Payment code parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Query the database for the payment with the given payment_code
            payment = AbattoirPaymentToBreader.objects.get(payment_code=payment_code)
            
            # Check if the payment is related to a BreaderTrade
            if payment.breeder_trade:
                serializer = AbattoirPaymentToBreaderSerializer(payment)
                return Response(serializer.data)
            else:
                return Response({'error': 'Payment not found or not related to any BreaderTrade'}, status=status.HTTP_404_NOT_FOUND)
        except AbattoirPaymentToBreader.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
# END PAYMENT

# TEMPLATES
from .forms import BreaderTradeForm, WeightRecordForm
from django.contrib.auth.decorators import login_required
from django.db import transaction

def get_seller(request):
    control_center_id = request.GET.get('control_center_id')
    if control_center_id:
        try:
            control_center = ControlCenter.objects.get(id=control_center_id)
            return JsonResponse({'seller_id': control_center.seller.id})
        except ControlCenter.DoesNotExist:
            return JsonResponse({'seller_id': None})
    return JsonResponse({'seller_id': None})

@login_required

def create_breader_trade(request, lc_id):
    lc = get_object_or_404(LetterOfCredit, id=lc_id)
    if request.method == 'POST':
        form = BreaderTradeForm(request.POST)
        if form.is_valid():
            requested_quantity = form.cleaned_data['breeds_supplied']

            # Prevent submission if quantity is 0 or less
            if requested_quantity <= 0:
                error_message = "The quantity supplied must be greater than 0. Please enter a valid quantity."
                return render(request, 'create_breader_trade.html', {
                    'form': form,
                    'error_message': error_message,
                    'available_quantity': lc.quantity
                })

            # Check if requested quantity exceeds available quantity
            if requested_quantity > lc.quantity:
                error_message = (
                    f"The quantity you are attempting to supply ({requested_quantity}) exceeds "
                    f"the quantity we want ({lc.quantity}). Please adjust the quantity."
                )
                return render(request, 'create_breader_trade.html', {
                    'form': form,
                    'error_message': error_message,
                    'available_quantity': lc.quantity
                })

            # Proceed with saving the form if quantity is valid
            with transaction.atomic():
                breader_trade = form.save(commit=False)
                breader_trade.breeder = request.user
                breader_trade.letter_of_credit = lc
                breader_trade.breed = lc.item
                breader_trade.seller = breader_trade.control_center.seller  # Automatically set the seller
                breader_trade.save()
                lc.update_quantity(breader_trade.breeds_supplied)
                breader_trade.control_center.update_net_breed_supply()

            return redirect('success_url')

        return render(request, 'create_breader_trade.html', {
            'form': form,
            'error_messages': form.errors.as_data(),
            'available_quantity': lc.quantity
        })
    
    form = BreaderTradeForm()
    return render(request, 'create_breader_trade.html', {
        'form': form,
        'available_quantity': lc.quantity
    })
    
# Reception
from .forms import ReceptionForm
@login_required
def list_breader_trades(request):
    trades = BreaderTrade.objects.filter(control_center__isnull=False).order_by('-id')
    # Calculate aggregate values
    total_received_weight = trades.aggregate(total_weight=Sum('weight'))['total_weight'] or 0
    total_good_condition = trades.aggregate(total_good=Sum('good_condition'))['total_good'] or 0
    total_destroyed_condition = trades.aggregate(total_destroyed=Sum('destroyed_condition'))['total_destroyed'] or 0
    total_poor_condition = trades.aggregate(total_poor=Sum('poor_condition'))['total_poor'] or 0
    
    context = {
        'trades': trades,
        'total_received_weight': total_received_weight,
        'total_good_condition': total_good_condition,
        'total_destroyed_condition': total_destroyed_condition,
        'total_poor_condition': total_poor_condition,
    }
    
    return render(request, 'list_breader_trades.html', context)

@login_required
def confirm_reception(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)
    if request.method == 'POST':
        form = ReceptionForm(request.POST, instance=trade)
        if form.is_valid():
            reception = form.save(commit=False)
            reception.reception_confirmed = True
            reception.save()
            return redirect('list_breader_trades')  # Redirect to a success page
    else:
        form = ReceptionForm(instance=trade)
    
    return render(request, 'confirm_reception.html', {'form': form, 'trade': trade})

@login_required
def record_item_weight(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)
    
    if request.method == 'POST':
        form = WeightRecordForm(request.POST, instance=trade)
        if form.is_valid():
            reception = form.save(commit=False)
            
            if reception.weight:  # Check if weight is populated
                reception.reception_confirmed = True
            else:
                reception.reception_confirmed = False
            
            reception.save()
            return redirect('slaughterhouse_dashboard')  # Redirect to the dashboard
    else:
        form = WeightRecordForm(instance=trade)
    
    return render(request, 'record_weight.html', {'form': form, 'trade': trade})

@login_required
def trade_detail(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)
    return render(request, 'trade_detail.html', {'trade': trade})
    
@login_required

def success_url(request):
    return render(request, 'trade_success.html')

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
@login_required

def supply_history(request):
    # Filter supply history items by current breeder
    current_breeder = request.user
    supply_history = BreaderTrade.objects.filter(breeder=current_breeder).order_by('-created_at')

    # Paginate the supply history items
    paginator = Paginator(supply_history, 20)  # Show 5 items per page
    page_number = request.GET.get('page')
    try:
        supplies = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        supplies = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        supplies = paginator.page(paginator.num_pages)

    # Pass the paginated supplies to the template
    return render(request, 'supply_history.html', {'supplies': supplies})

@login_required
def seller_breeder_trade(request):
    # Retrieve breeder trades for the current seller's control center
    current_seller = request.user
    control_center = current_seller.controlcenter_set.first()
    breeder_trades = BreaderTrade.objects.filter(control_center=control_center)

    # Paginate the breeder trades
    paginator = Paginator(breeder_trades, 20)  # Show 5 items per page
    page_number = request.GET.get('page')
    try:
        breeder_trades = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        breeder_trades = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        breeder_trades = paginator.page(paginator.num_pages)

    # Pass the paginated breeder trades to the template
    return render(request, 'seller_supply_history.html', {'breeder_trades': breeder_trades})
    
# Supply vs demand
from django.http import JsonResponse

from django.shortcuts import render
from django.http import JsonResponse
@login_required

def supply_vs_demand_statistics(request):
    # Query BreaderTrade and SlaughterhouseRecord models to fetch data
    breeder_trades = BreaderTrade.objects.all()
    slaughter_records = SlaughterhouseRecord.objects.all()

    # Calculate supply data for each breed
    breed_supply_data = {}
    for trade in breeder_trades:
        breed = trade.breed
        breed_supply_data[breed] = breed_supply_data.get(breed, 0) + trade.breeds_supplied

    # Calculate slaughtered data for each breed
    breed_slaughter_data = {}
    for record in slaughter_records:
        breed = record.breed
        breed_slaughter_data[breed] = breed_slaughter_data.get(breed, 0) + record.quantity

    # Format the data as JSON
    supply_data = {
        'breeds': list(breed_supply_data.keys()),
        'supply_values': list(breed_supply_data.values()),
        'slaughter_values': [breed_slaughter_data.get(breed, 0) for breed in breed_supply_data.keys()]
    }

    # Pass the supply data to the template
    return render(request, 'seller_dashboard.html', {'supply_data': supply_data})

@login_required

def breed_supply_vs_demand_statistics(request):
    # Query BreaderTrade and SlaughterhouseRecord models to fetch data
    breeder_trades = BreaderTrade.objects.all()
    slaughter_records = SlaughterhouseRecord.objects.all()

    # Perform calculations to determine supply vs demand
    total_breeder_trades = sum(trade.breeds_supplied for trade in breeder_trades)
    total_slaughter_records = sum(record.quantity for record in slaughter_records)

    # Format the data as JSON
    supply_data = {
        'labels': ['Total Breeder Trades', 'Total Slaughter Records'],
        'values': [total_breeder_trades, total_slaughter_records],
    }

    # Pass the supply data to the template context
    context = {
        'supply_data': json.dumps(supply_data)  # Convert Python dictionary to JSON string
    }

    return render(request, 'home.html', context)
