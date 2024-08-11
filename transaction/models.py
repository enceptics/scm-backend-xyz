from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from custom_registration.models import CustomUser, Seller
from logistics.models import ControlCenter
from datetime import datetime
import uuid
import random
import string
from logistics.models import ControlCenter
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import F, Func
from invoice_generator.models import LetterOfCredit

class Breader(models.Model):    
    breeder = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):

        return f'{self.breeder.first_name} {self.breeder.last_name} '

class Abattoir(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    breeders = models.ManyToManyField(Breader, related_name='abattoirs_registered', blank=True)
    # bank = models.ForeignKey(Bank, on_delete=models.CASCADE, default=1)

    def __str__(self):

        return f'{self.user.first_name} {self.user.last_name} '

class BreaderTrade(models.Model):

    SALE_CHOICES = [
        ('export', 'Export'),
        ('local_sale_cut', 'Local Sale Cut'),
    ]

    breeder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='sellers')
    control_center = models.ForeignKey(ControlCenter, on_delete=models.CASCADE, null=True, blank=True)
    transaction_date = models.DateField(auto_now_add=True)
    breed = models.CharField(max_length=255)
    breeds_supplied = models.PositiveIntegerField(default=0)
    weight = models.PositiveIntegerField(null=True, blank=True)
    vaccinated = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, null=True, blank=True)
    reference = models.CharField(max_length=20, unique=False)
    letter_of_credit = models.ForeignKey(LetterOfCredit, on_delete=models.CASCADE, null=True, blank=True)

    received_weight = models.PositiveIntegerField( null=True, blank=True)
    good_condition = models.PositiveIntegerField( null=True, blank=True)
    destroyed_condition = models.PositiveIntegerField( null=True, blank=True)
    poor_condition = models.PositiveIntegerField( null=True, blank=True)
    reception_confirmed = models.BooleanField(default=False)
    payment_status = models.BooleanField(default=False)

    # Record parts
    part_name = models.CharField(max_length=255, blank=True, null=True)
    sale_type = models.CharField(max_length=255, choices=SALE_CHOICES, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    part_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated when saving the instance

    # Confirm inventory item removal
    last_confirmation_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'last_confirmed_slaughterhouse_records')
    first_confirmed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'first_confirmed_slaughterhouse_records')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='confirmed_inventory_removal_records', null=True, blank=True)
    requested_quanity = models.PositiveIntegerField(blank=True, null=True)
    record_created = models.BooleanField(default=False)
    # Fields for temporary deduction values
    temp_breeds_supplied = models.PositiveIntegerField(default=0)
    temp_weight = models.PositiveIntegerField(default=0)
    
    def create_slaughter_record(self, form):
        if self.first_confirmed_by or self.last_confirmation_by:
            raise ValueError("Record already confirmed by both parties.")
        
        # Set temporary values based on the form
        self.temp_breeds_supplied = form.cleaned_data.get('breeds_supplied', 0)
        self.temp_weight = form.cleaned_data.get('weight', 0)
        self.record_created = True
        self.save()
        return True

    def confirm_as_seller(self, user):
        self.first_confirmed_by = user
        self.save()

    def confirm_as_inventory_manager(self, user):
        self.last_confirmation_by = user
        if self.first_confirmed_by and self.last_confirmation_by:
            self.deduct_weight_and_number()
        self.save()

    def deduct_weight_and_number(self):
        if self.record_created and self.first_confirmed_by and self.last_confirmation_by:
            # Deduct weight and breeds_supplied from actual inventory
            self.breeds_supplied -= self.temp_breeds_supplied
            self.weight -= self.temp_weight
            # Reset temporary values
            self.temp_breeds_supplied = 0
            self.temp_weight = 0
            self.record_created = False  # Reset after deductions
            self.first_confirmed_by = None  # Reset after deductions
            self.last_confirmation_by = None  # Reset after deductions

            self.save()


    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"{timezone.now().strftime('%y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)
        
        if self.control_center:
            self.control_center.update_net_breed_supply()

        if self.letter_of_credit:
            self.letter_of_credit.update_quantity(self.breeds_supplied)
            self.breed = self.letter_of_credit.item
            super().save(update_fields=['breed'])


    @classmethod
    def get_supply_data(cls):
        supply_data = {}
        breeds = cls.objects.values_list('breed', flat=True).distinct()
        for breed in breeds:
            total_supply = cls.objects.filter(breed=breed).aggregate(Sum('breeds_supplied'))['breeds_supplied__sum']
            supply_data[breed] = total_supply or 0
        return supply_data

    def get_seller_full_name(self):
        if self.seller:
            return f'{self.seller.first_name} {self.seller.last_name}'
        else:
            return "No email for this user"

    def get_breeder_email(self):
        if self.breeder:
            return f'{self.breeder.email}'
        else:
            return "No email for this user"

    def get_breeder_phone_number(self):
        if self.breeder:
            return f'{self.breeder.phone_number}'
        else:
            return "No phone number for this user"

    def get_breeder_id_number(self):
        if self.breeder:
            return f'{self.breeder.id_number}'
        else:
            return "No id number for this user"

    def get_breeder_bank_account_number(self):
        if self.breeder:
            return f'{self.breeder.bank_account_number}'
        else:
            return "No bank acc. number for this user"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.reference:
            # Generate a unique reference if it doesn't exist
            self.reference = f"{timezone.now().strftime('%y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} supplied {self.breeds_supplied} to {self.control_center} on {self.created_at}"

class Inventory(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    trade = models.ManyToManyField(BreaderTrade)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class AbattoirPaymentToBreader(models.Model):
    SENT_TO_BANK = 'payment_initiated'
    DISBURSED = 'disbursed'
    PAID = 'paid'

    STATUS_CHOICES = [
        (SENT_TO_BANK, 'Sent to Bank for Payment Processing'),
        (DISBURSED, 'Disbursed'),
        (PAID, 'Paid'),
    ]

    payments_id = models.AutoField(primary_key=True)
    breeder_trade = models.ForeignKey(BreaderTrade, on_delete=models.CASCADE)
    # abattoir_payment = models.ForeignKey(BreaderTrade, on_delete=models.CASCADE)

    # amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_code = models.CharField(max_length=50, unique=True, editable=False)
    payment_initiation_date = models.DateTimeField(auto_now_add=True)
    # status = models.CharField(choices=STATUS_CHOICES, default=SENT_TO_BANK, max_length=100)

    payment_date = models.DateTimeField(auto_now_add=True)

    def process_payment(self):
        # Example: Update payment status to 'Paid'
        self.status = self.SENT_TO_BANK
        self.save()

        # Add additional payment processing logic here
        # For example, interact with a payment gateway, log payment details, etc.

        # Return True if the payment was successful
        return True

    def generate_payment_code(self):
        timestamp_str = datetime.now().strftime('%y%m%d%H%M%S')
        random_chars = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        return f"{timestamp_str}{random_chars}"

    def save(self, *args, **kwargs):
        if not self.payment_code:
            self.payment_code = self.generate_payment_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment to {self.breeder_trade.breeder} for {self.breeder_trade}"


