from django.db import models
from django.contrib.auth.models import User
from .choices import PART_CHOICES, BREED_CHOICES, SALE_CHOICES, STATUS_CHOICES, SALE_CHOICES
from django.db.models.signals import post_save
from django.dispatch import receiver
# from inventory_management.models import InventoryBreed, InventoryBreedSales
from transaction.models import BreaderTrade
from logistics.models import ControlCenter
from django.db.models import Sum, F, Value
from custom_registration.models import CustomUser

class SlaughterhouseRecord(models.Model):

    SLAUGHTER_STATUS_CHOICES = [
            ('deducted', 'Deducted'),
    ]

    breed = models.CharField(max_length=255, null=True, blank=True)
    slaughter_date = models.DateField(auto_now_add=True)
    quantity = models.PositiveIntegerField()
    last_confirmation_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    confirmed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name = 'confirmed_slaughterhouse_records')
    control_center = models.ForeignKey(ControlCenter, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, choices=SLAUGHTER_STATUS_CHOICES, default='slaughtered')
    weight = models.PositiveIntegerField(null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='confirmed_records', null=True, blank=True)

    def __str__(self):
        return f"Slaughterhouse Record - Date: {self.slaughter_date}, Quantity: {self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.control_center:
            # Deduct the slaughtered quantity from the net breed supply
            control_center = ControlCenter.objects.get(pk=self.control_center.pk)
            control_center.net_breed_supply -= self.quantity
            control_center.save()

class Confirmation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    record = models.ForeignKey(SlaughterhouseRecord, on_delete=models.CASCADE)


            