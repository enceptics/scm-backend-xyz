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
    breeder = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='sellers')
    control_center = models.ForeignKey(ControlCenter, on_delete=models.CASCADE, null=True, blank=True)
    transaction_date = models.DateField(auto_now_add=True)
    breed = models.CharField(max_length=255)
    breeds_supplied = models.PositiveIntegerField(default=0)
    goat_weight = models.PositiveIntegerField(default=0)
    vaccinated = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    reference = models.CharField(max_length=20, unique=True, editable=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.control_center:
            # Increment the net breed supply by adding the newly supplied breeds
            control_center = ControlCenter.objects.get(pk=self.control_center.pk)
            control_center.net_breed_supply += self.breeds_supplied
            control_center.save()

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
        return f"{self.breeder.first_name} {self.breeder.last_name} supplied {self.breeds_supplied} {self.breed}'s to {self.control_center} on {self.created_at}"

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


