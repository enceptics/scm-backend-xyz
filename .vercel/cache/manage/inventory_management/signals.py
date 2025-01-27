from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=BreaderTrade)
@receiver(post_save, sender=SlaughterhouseRecord)
def update_control_center_on_save(sender, instance, **kwargs):
    if instance.control_center:
        instance.control_center.update_net_breed_supply()

@receiver(post_delete, sender=BreaderTrade)
@receiver(post_delete, sender=SlaughterhouseRecord)
def update_control_center_on_delete(sender, instance, **kwargs):
    if instance.control_center:
        instance.control_center.update_net_breed_supply()

