from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404

from .models import CustomUser, UserProfile, Payment, BankTeller, CustomerService, Seller
from logistics.models import CollateralManager
from transaction.models import Breader
from invoice_generator.models import Buyer

from rest_framework import status

from .serializers import CustomUserSerializer, LogoutSerializer, CustomTokenObtainPairSerializer, UserProfileSerializer, CustomerServiceSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, SellerSerializer

from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.views import LogoutView
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import RoleSerializer, PaymentSerializer
from django.template.loader import render_to_string  # Add this import
from django.utils.html import strip_tags
from django.core.mail import send_mail
from transaction.models import BreaderTrade

from .models import PasswordReset
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from transaction.models import Breader
from .models import InventoryManager

# Templates
from django.shortcuts import render

from .forms import CustomUserRegistrationForm, CustomPasswordResetForm, CustomLoginForm  # Import the CustomUserRegistrationForm

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.contrib.auth import get_user_model
from django.contrib.auth import logout

from django.contrib.auth.views import PasswordResetCompleteView
from django.views.generic import TemplateView

from django.conf import settings

protocol = settings.PROTOCOL
domain = settings.DOMAIN

User = get_user_model()

class CustomPasswordResetView(PasswordResetView):
    def save(self, domain_override=None, subject_template_name='auth/password_reset_subject.txt', email_template_name='auth/password_reset_email.html', use_https=False, token_generator=default_token_generator, from_email=None, request=None, html_email_template_name=None, extra_email_context=None):
        # Generate the password reset token and uid
        email = self.cleaned_data["email"]
        domain = domain_override if domain_override is not None else settings.DOMAIN
        site_name = settings.SITE_NAME
        protocol = 'https' if use_https else 'http'
        context = {
            'email': email,
            'domain': domain,
            'site_name': site_name,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'user': user,
            'token': token_generator.make_token(user),
            'protocol': protocol,
        }
        # Render the email content
        subject = render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email_message = render_to_string(email_template_name, context)
        send_mail(subject, email_message, from_email, [email], fail_silently=False)
        return email
        
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('password_reset_complete')  # Corrected URL name
    template_name = 'auth/password_reset_confirm.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'auth/password_reset_complete.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetDoneView(TemplateView):
    template_name = 'auth/password_reset_done.html'  # Specify the template name


class GetUserRole(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            # Get the user's role from the CustomUser model
            user_role = request.user.role
            return Response({"role": user_role})
        else:
            return Response({"role": "anonymous"}, status=status.HTTP_401_UNAUTHORIZED)

class RoleListView(APIView):
    def get(self, request, *args, **kwargs):
        # Replace this with your logic to fetch roles from the database or any other source
        roles = ['buyer', 'no_role', 'warehouse_personnel']

        serializer = RoleSerializer(data={'roleChoices': roles})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Extract the role data from the request
        role_data = request.data.get('roleChoices', {})

        # Perform validation and update logic
        # This is a placeholder, replace it with your actual logic to update roles in the database
        # You may need to iterate through the roles and update the corresponding user's role in the database
        updated_roles = role_data.get('roleChoices', [])
        
class CustomTokenRefreshView(TokenRefreshView):
    # Customize if needed
    '''
    this automatically refreshes the token
    '''
    pass

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer  # Replace with your custom serializer


class CustomUserRegistrationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Assign a role to the user based on user_type
            user_type = request.data.get('user_type')
            if user_type == 'buyer':
                user.role = 'buyer'
                Buyer.objects.create(buyer=user)
            elif user_type == 'breeder':
                user.role = 'breeder'
                Breader.objects.create(breeder=user)
            elif user_type == 'seller':
                user.role = 'admin'
                Seller.objects.create(seller=user)
            elif user_type == 'collateral_manager':
                user.role = 'collateral_manager'
                CollateralManager.objects.create(name=user)
            elif user_type == 'bank':
                user.role = 'bank'
                BankTeller.objects.create(bank_name=user)
            else:
                # Handle invalid user types here
                pass

            user.save()

            # Refresh token after saving the user instance
            refresh = RefreshToken.for_user(user)

            tokens = {'refresh': str(refresh), 'access': str(refresh.access_token)}
            return Response({'user': {'id': user.id, 'username': user.username}, 'tokens': tokens}, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
        
class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return Response({"detail": "No account found with this email"}, status=status.HTTP_400_BAD_REQUEST)

            # Create a password reset token and send it via email
            token = default_token_generator.make_token(user)
            reset_instance = PasswordReset.objects.create(user=user, token=token)

            # Obtain uidb64 from the user instance
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))


            # Construct reset link
            reset_url = reverse_lazy('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

            # Compose email message
            subject = 'Password Reset Request'
            context = {
                'password_reset_url': reset_url,
            }

            message = render_to_string('password_reset_email.html', context)
            plain_message = strip_tags(message)
            from_email = 'pascalouma54@gmail.com'  # Replace with your email
            to_email = [user.email]

            send_mail(subject, plain_message, from_email, to_email, html_message=message)

            return Response({"detail": "Check your email for password reset link "}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomPasswordResetConfirmationView(APIView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
            reset_instance = PasswordReset.objects.get(user=user, token=token)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist, PasswordReset.DoesNotExist):
            return Response({"detail": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']

            # Set the new password and delete the reset instance
            user.set_password(new_password)
            user.save()
            reset_instance.delete()

            return Response({"detail": "Password reset successful"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class UserProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # Retrieve the UserProfile instance associated with the authenticated user
        return self.request.user.userprofile

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({'detail': 'User profile deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

# List all profiles

class UserProfilesListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()  # Assuming you have a UserProfile model

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

class CustomUserLoginViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # Validate username and password
        if not username or not password:
            return Response({'error': 'Both username and password are required.'}, status=400)

        try:
            # Authenticate the user
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid credentials.'}, status=400)

        # Check the password
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials.'}, status=400)

        # # If authentication is successful, generate tokens
        
        # If authentication is successful, generate tokens
        refresh = RefreshToken.for_user(user)
        access = AccessToken.for_user(user)

        tokens = {
            'refresh': str(refresh),
            'access': str(access),
        }

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'bank_account_number': user.bank_account_number,
            'email': user.email,
            'community': user.community,  
            'county': user.county, 
            'head_of_family':user.head_of_family,
            'county': user.county,
            'groups': user.groups,
            'role': user.role,  
        }

        return Response({'user': {'id': user.id, 'username': user.username}, 'tokens': tokens}, status=200)

class CustomLogoutViewSet(viewsets.ViewSet):
    
    def create(self, request, *args, **kwargs):
        # Perform any additional actions you need before logging out
        # For example, invalidate the user's token if you're using token-based authentication

        # Logout the user
        response = LogoutView.as_view()(request, *args, **kwargs)

        # Return a JSON response using the LogoutSerializer
        serializer = LogoutSerializer(data={'detail': 'Successfully logged out.'})
        serializer.is_valid()
        return Response(serializer.data, status=status.HTTP_200_OK)

# Payment

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract the 'id' from the request data
        breeder_trade_id = request.data.get('id')

        try:
            # Get the corresponding BreaderTrade instance
            breeder_trade = BreaderTrade.objects.get(pk=breeder_trade_id)
        except BreaderTrade.DoesNotExist:
            # Handle the case where the BreaderTrade instance doesn't exist
            return Response({'error': 'BreaderTrade instance does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the payment and associate it with the BreaderTrade instance
        payment = serializer.save(breeder_trade=breeder_trade)

        # Additional logic related to payment creation can be performed here
        # For example, generate payment code, send confirmation email, etc.

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
                'success_message': 'A new payment has been initiated. Please review the details.',
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

    @action(detail=False, methods=['get'])
    def search_payment_by_code(self, request, *args, **kwargs):
        payment_code = request.query_params.get('payment_code')
        if not payment_code:
            return Response({'error': 'Payment code parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Query the database for the payment with the given payment_code
        payment = get_object_or_404(Payment, payment_code=payment_code)
        # Serialize the payment data and return the response
        serializer = self.get_serializer(payment)
        return Response(serializer.data)

class CustomerServiceViewSet(viewsets.ModelViewSet):
    queryset = CustomerService.objects.all()
    serializer_class = CustomerServiceSerializer

# seller
class SellerAllViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.all().order_by('-created_at')
    serializer_class = SellerSerializer
    
class SellerViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Retrieve the corresponding Seller instance based on the user
        seller = get_object_or_404(CustomUser, id=self.request.user.id)

        # Filter sellers based on the retrieved Seller instance
        return Seller.objects.filter(seller=seller)

    @action(detail=False, methods=['post'])
    def send_quotation_and_message_to_buyer(self, request):
        required_fields = ['buyer_id', 'message', 'product', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in request.data:
                return Response({'error': f'Missing {field} in request data'}, status=status.HTTP_400_BAD_REQUEST)

        buyer_id = request.data.get('buyer_id')
        message = request.data.get('message')
        product = request.data.get('product')
        quantity = request.data.get('quantity')
        unit_price = request.data.get('unit_price')

        buyer = get_object_or_404(CustomUser, id=buyer_id, role='BUYER')

        quotation_data = {
            'buyer': buyer_id,  
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price
        }
        quotation_serializer = QuotationSerializer(data=quotation_data)
        if quotation_serializer.is_valid():
            quotation = quotation_serializer.save()
        else:
            return Response(quotation_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': f'Message and quotation sent to buyer {buyer_id}: {message}', 'quotation_id': quotation.id}, status=status.HTTP_200_OK)
        
    # def get_queryset(self):
    #         # Get the currently logged-in user
    #         user = self.request.user

    #         # Retrieve the associated breeder instance for the logged-in user
    #         breeder = get_object_or_404(Breader, user=user)

    #         # Filter sellers based on the relationship with the logged-in breeder
    #         queryset = Seller.objects.filter(breeder=breeder)

    #         return queryset

# TEMPLATES

def home(request):
    # Add any context data you want to pass to the template
    context = {
        'title': 'Home Page',
        'content': 'Welcome to our website!',
    }
    # Render the 'home.html' template with the provided context
    return render(request, 'home.html', context)

from django.contrib.auth.forms import UserCreationForm
from .forms import BuyerRegistrationForm, BreederRegistrationForm, SellerRegistrationForm, BankRegistrationForm, CollateralManagerRegistrationForm, InventoryManagerRegistrationForm
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model


# def send_password_reset_email(user):
#     UserModel = get_user_model()
#     uid = urlsafe_base64_encode(force_bytes(user.pk))
#     token = default_token_generator.make_token(user)
#     reset_url = f"{settings.BASE_URL}/set-password/{uid}/{token}/"  # Assuming you have a set-password endpoint

#     subject = 'Set Your Password'
#     message = f'Please click the following link to set your password: {reset_url}'
#     sender_email = settings.DEFAULT_FROM_EMAIL
#     receiver_email = user.email

#     # Send email
#     send_mail(subject, message, sender_email, [receiver_email])

# Repeat the same pattern for other registration views (register_breeder, register_seller, register_bank, register_collateral_manager)

# from transaction.models import Breeder


UserModel = get_user_model()

from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

def send_password_reset_email(uidb64, token, email):
    # Encode the user ID to bytes
    uid = force_bytes(uidb64)

    # Construct the reset password URL
    reset_url = f"{settings.BASE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})}"

    # Construct the email message
    subject = 'Set Your Password'
    message = f'Please click the following link to set your password: {reset_url}'
    sender_email = settings.DEFAULT_FROM_EMAIL

    # Send the email
    send_mail(subject, message, sender_email, [email])

def register_buyer(request):
    if request.method == 'POST':
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.BUYER
            user.save()
            # Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
           # Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)


            buyer = Buyer.objects.create(buyer=user)  # Assign the user to the buyer field

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            return redirect('register_success')
    else:
        form = BuyerRegistrationForm()
    return render(request, 'auth/buyer_registration.html', {'form': form})

def register_seller(request):
    if request.method == 'POST':
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.SELLER
            user.save()

            # Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            # Create a new Seller instance and associate the user with it
            seller = Seller.objects.create(seller=user)  # Assign the user to the seller_id field
            return redirect('register_success')
    else:
        form = SellerRegistrationForm()
    return render(request, 'auth/seller_registration.html', {'form': form})

def register_breeder(request):
    if request.method == 'POST':
        form = BreederRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.BREEDER
            user.save()

            # Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            # Create a new Seller instance and associate the user with it
            # breeder = Breeder.objects.create(breeder=user)  # Assign the user to the seller_id field
            return redirect('register_success')
    else:
        form = BreederRegistrationForm()
    return render(request, 'auth/breeder_registration.html', {'form': form})

def register_bank(request):
    if request.method == 'POST':
        form = BankRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.BANK
            user.save()

# Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            return redirect('register_success')
    else:
        form = BankRegistrationForm()
    return render(request, 'auth/bank_registration.html', {'form': form})

def register_collateral_manager(request):
    if request.method == 'POST':
        form = CollateralManagerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.COLLATERAL_MANAGER
            user.save()
            name = CollateralManager.objects.create(name=user)  # Assign the user to the seller_id field

# Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            return redirect('register_success')
    else:
        form = CollateralManagerRegistrationForm()
    return render(request, 'auth/collateral_manager_registration.html', {'form': form})

def register_inventory_manager(request):
    if request.method == 'POST':
        form = InventoryManagerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = CustomUser.INVENTORY_MANAGER
            user.save()
            name = InventoryManager.objects.create(name=user)  # Assign the user to the seller_id field

# Generate uidb64 and token for password reset email
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Send password reset email
            send_password_reset_email(uidb64, token, user.email)

            return redirect('register_success')
    else:
        form = InventoryManagerRegistrationForm()
    return render(request, 'auth/inventory_manager_registration.html', {'form': form})

def register_success(request):
    """View to redirect to registration success page."""
    return render(request, 'auth/register_success.html')


    # Registration
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
import random

def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    send_mail(
        'Verification Code',
        f'Your verification code is: {code}',
        [email],
        fail_silently=False,
    )

from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect

def register_user(request):
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data.get('user_type')
            user_email = form.cleaned_data.get('email')
            # Create user instance based on user type
            if user_type == 'seller':
                user = Seller.objects.create_user(email=user_email, **form.cleaned_data)
                user.is_seller = True
            elif user_type == 'breeder':
                user = Breeder.objects.create_user(email=user_email, **form.cleaned_data)
                user.is_breeder = True
            elif user_type == 'buyer':
                user = Buyer.objects.create_user(email=user_email, **form.cleaned_data)
                user.is_buyer = True
            
            # Send email with unique link to set password
            subject = 'Set Your Password'
            message = f'Please click the following link to set your password: {settings.BASE_URL}/set-password/{user_email}'
            sender_email = settings.DEFAULT_FROM_EMAIL
            receiver_email = user_email

            # Send email
            send_mail(subject, message, sender_email, [receiver_email])

            # Redirect to respective dashboard after registration
            return redirect('superuser')  # Replace 'superuser' with actual dashboard URL

    else:
        form = CustomUserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)  # Pass request.POST to initialize the form with user input
        if form.is_valid():  # Check if the form is valid
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Determine user's role and redirect accordingly
                if user.role == CustomUser.ADMIN:
                    return redirect('/admin/')  # Redirect admin users to admin page
                elif user.role == CustomUser.BREEDER:
                    return redirect('/dashboard/breeder/')  # Redirect breeders to breeder dashboard
              
                elif user.role == CustomUser.BUYER:
                    return redirect('/buyer/quotations/')  # Redirect buyers to buyer dashboard
                elif user.role == CustomUser.BANK:
                    return redirect('/dashboard/bank/')  # Redirect buyers to buyer dashboard
                elif user.role == CustomUser.SELLER:
                    return redirect('/dashboard/seller/')  # Redirect sellers to seller dashboard
                elif user.role == CustomUser.WAREHOUSE_PERSONNEL:
                    return redirect('/warehouse_personnel_dashboard/')  # Redirect warehouse personnel to warehouse personnel dashboard
                elif user.role == CustomUser.INVENTORY_MANAGER:
                    return redirect('/dashboard/inventory_manager/')  # Redirect inventory managers to inventory manager dashboard
                elif user.role == CustomUser.SLAUGHTERHOUSE_MANAGER:
                    return redirect('/dashboard/slaughterhouse_manager/')  # Redirect slaughterhouse managers to slaughterhouse manager dashboard
                elif user.role == CustomUser.COLLATERAL_MANAGER:
                    try:
                        collateral_manager = CollateralManager.objects.get(name=user)
                        return redirect('collateral_manager_dashboard', collateral_manager_id=collateral_manager.id)
                    except CollateralManager.DoesNotExist:
                        # Handle the case where the user is not associated with a collateral manager
                        return redirect('/')  # Redirect to a generic dashboard
                else:
                    # Handle other roles or scenarios
                    return redirect('/')  # Redirect to a generic dashboard
            else:
                # Add a non-field error to the form indicating invalid username or password
                form.add_error(None, 'Invalid username or password.')
                return render(request, 'auth/login.html', {'form': form})
    else:
        form = CustomLoginForm()  # If it's a GET request, initialize an empty form

    return render(request, 'auth/login.html', {'form': form})  # Pass the form to the template for rendering

def logout_view(request):
    logout(request)
    # Redirect to a specific page after logout, if needed
    return redirect('home')  # Replace 'home' with the name of your homepage URL pattern

def superuser(request):
    if  not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'superuser.html')

def seller_dashboard(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'seller_dashboard.html')

def inventory_manager_dashboard(request):
    # if request.user.role != 'inventory_manager' and not request.user.is_superuser:
    #     return redirect('unauthorized')
    return render(request, 'stock_shift.html')

def buyer_dashboard(request):
    if control_centers_dashboard.user.role != 'buyer' and not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'buyer_dashboard.html')

def breeder_dashboard(request):
    if request.user.role != 'breeder' and not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'breeder_dashboard.html')

def bank_dashboard(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'bank_dashboard.html')

def export_management_dashboard(request):
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')
    return render(request, 'export_management.html')

def stock_shift_dashboard(request):
    # Add logic to retrieve data for the seller dashboard
    # For example, retrieve orders, sales, or any other relevant information
    
    context = {
        # Add context data for the seller dashboard template
        'title': 'Stock shift Dashboard',
        'content': 'Welcome !',
    }
    
    return render(request, 'stock_shift.html', context)

def unauthorized(request):
    return render(request, 'unauthorized.html')


# FOR TEMPLATES

def sellers_list(request):
    sellers = Seller.objects.all().order_by('-created_at')
    num_sellers = sellers.count()  # Calculate the number of sellers
    return render(request, 'sellers_list.html', {'sellers': sellers, 'num_sellers': num_sellers})

def breeders_list(request):
    breeders = Breeder.objects.all().order_by('-created_at')
    num_breeders = breeders.count()  # Calculate the number of sellers
    return render(request, 'breeders_list.html', {'breeders': sellers, 'num_breeders': num_breeders})

def breeders_details(request, seller_id):
    breeder = get_object_or_404(Breeder, id=breeder_id)
    return render(request, 'breders_profile.html', {'breeder': breeder})

def buyers_list(request):
    buyers = Buyer.objects.all()
    num_buyers = buyers.count()  # Calculate the number of buyers
    return render(request, 'buyers_list.html', {'buyers': buyers, 'num_buyers': num_buyers})

def collateral_managers_list(request):
    collateral_managers = CollateralManager.objects.all()
    num_collateral_managers = collateral_managers.count()  # Calculate the number of collateral managers
    return render(request, 'collateral_managers_list.html', {'collateral_managers': collateral_managers, 'num_collateral_managers': num_collateral_managers})

def seller_details(request, seller_id):
    seller = get_object_or_404(Seller, id=seller_id)
    return render(request, 'sellers_profile.html', {'seller': seller})

def collateral_manager_details(request, collateral_manager_id):
    collateral_manager = get_object_or_404(CollateralManager, id=collateral_manager_id)
    return render(request, 'collateral_managers_profile.html', {'collateral_manager': collateral_manager})

def buyer_details(request, buyer_id):
    buyer = get_object_or_404(Buyer, id=buyer_id)
    return render(request, 'buyers_profile.html', {'buyer': buyer})

from .forms import CollateralManagerForm
from logistics.models import ControlCenter, CollateralManager

def control_centers_dashboard(request):
    if request.user.role != 'bank' and not request.user.is_superuser:
        return redirect('unauthorized')
        
    control_centers = ControlCenter.objects.all()
    collateral_managers = CollateralManager.objects.all()  # Retrieve all collateral managers
    return render(request, 'control_centers.html', {'control_centers': control_centers, 'collateral_managers': collateral_managers})

from django.http import Http404
from django.db.models import Sum
from slaughter_house.models import SlaughterhouseRecord

def collateral_manager_dashboard(request, collateral_manager_id):
    # Fetch control centers associated with the collateral manager
    control_centers = ControlCenter.objects.filter(assigned_collateral_agent__id=collateral_manager_id)

    # Prepare inventory information for each control center
    inventory_info = {}
    for center in control_centers:
        breeds_info = {}
        breeds = BreaderTrade.objects.filter(control_center=center).values_list('breed', flat=True).distinct().order_by('-created_at')
        for breed in breeds:
            total_supplied = BreaderTrade.objects.filter(control_center=center, breed=breed).aggregate(total_supplied=Sum('breeds_supplied'))['total_supplied'] or 0
            total_weight = BreaderTrade.objects.filter(control_center=center, breed=breed).aggregate(total_weight=Sum('goat_weight'))['total_weight'] or 0
            total_slaughtered = SlaughterhouseRecord.objects.filter(control_center=center, breed=breed).aggregate(total_slaughtered=Sum('quantity'))['total_slaughtered'] or 0
            net_breed_supply = total_supplied - total_slaughtered
            breeds_info[breed] = {
                'total_supplied': total_supplied,
                'total_weight': total_weight,
                'total_slaughtered': total_slaughtered,
                'total_remaining': max(net_breed_supply, 0)
            }
        inventory_info[center] = {
            'name': center.name,
            'seller_name': center.get_full_name(),
            'agent_name': center.get_agent_full_name(),
            'breeds_info': breeds_info
        }

    return render(request, 'collateral_manager_dashboard.html', {'inventory_info': inventory_info})
    
def assign_collateral_manager_success(request):
    control_centers = ControlCenter.objects.all()
    collateral_managers = CollateralManager.objects.all()
    
    if request.method == 'POST':
        center_id = request.POST.get('center_id')
        manager_id = request.POST.get('collateral_manager')
        reset
        center = get_object_or_404(ControlCenter, id=center_id)
        collateral_manager = get_object_or_404(CollateralManager, id=manager_id)
        reset
        center.assigned_collateral_agent = collateral_manager
        center.save()
        
        return redirect('assign_collateral_manager_success')
    
    else:
        form = CollateralManagerForm()
        
    return render(request, 'assign_collateral_manager.html', {'control_centers': control_centers, 'collateral_managers': collateral_managers, 'form': form})

# USER PROFILE 
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .forms import ProfileForm

@login_required
def view_profile(request):
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    return render(request, 'profile/view_profile.html', {'profile': profile})

def edit_profile_picture(request, user_id):
    profile = get_object_or_404(UserProfile, user_id=user_id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('view_profile')  # Redirect to the view profile page
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile/edit_profile.html', {'form': form})
