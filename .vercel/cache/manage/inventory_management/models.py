from django.apps import apps
import logging

from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from custom_registration.models import CustomUser
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .choices import BREED_CHOICES,PART_CHOICES, STATUS_CHOICES
from transaction.models import BreaderTrade
from django.db.models import Sum  # Import Sum here
from slaughter_house.models import SlaughterhouseRecord
from django.db import models, transaction
from django.core.exceptions import ObjectDoesNotExist
from custom_registration.models import Seller

logger = logging.getLogger(__name__)

class BreedCut(models.Model):   
    breed = models.CharField(max_length=255, blank=True, null=True)
    part_name = models.CharField(max_length=255, blank=True, null=True)
    sale_type = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    weight = models.CharField(max_length=10, null=True, blank=True)  
    reference = models.ForeignKey(BreaderTrade, on_delete=models.CASCADE, null=True, blank=True)
    quantity_left = models.PositiveIntegerField(default=0, editable=False)
    sale_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.breed} - {self.part_name} - {self.quantity}"

    # def get_distinct_sales(self):
    #     return self.sales.all().distinct()

    
class InventoryBreed(models.Model):

    breed = models.CharField(max_length=255, default='goats', blank=True, null=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='in_yard')

    def __str__(self):
        return f"InventoryBreed - Breed: {self.breed}, Total Breed Supply: {self.total_breed_supply}"

from django.db import models
from django.db.models import F
from django.utils import timezone

class InventoryBreedSales(models.Model):
    SALE_CHOICES = [
        ('export', 'Export'),
        ('local_sale_cut', 'Local Sale Cut'),
    ]
    
    breed = models.CharField(max_length=255, blank=True, null=True)
    part_name = models.CharField(max_length=255, blank=True, null=True)
    sale_type = models.CharField(max_length=255, choices=SALE_CHOICES)
    quantity = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, null=True, blank=True)
    reference = models.CharField(max_length=20, null=True, blank=True)  # Add reference field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated when saving the instance
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.breed} - {self.part_name} - {self.quantity} - {self.get_sale_type_display()}"
