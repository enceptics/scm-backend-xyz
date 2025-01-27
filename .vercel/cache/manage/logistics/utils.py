# # logistics/utils.py

# from transaction.models import BreaderTrade

# def get_total_breeds_supplied(control_center):
#     total = BreaderTrade.objects.filter(control_center=control_center).aggregate(total=models.Sum('breeds_supplied'))
#     return total['total'] if total['total'] else 0
