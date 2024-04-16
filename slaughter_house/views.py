from django.shortcuts import render
from slaughter_house.models import SlaughterhouseRecord
from rest_framework import viewsets
from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.decorators import action
from django.http import JsonResponse
from slaughter_house.serializers import SlaughterhouseRecordSerializer
from inventory_management.models import BreedCut
from transaction.models import BreaderTrade
import logging
from django.views.decorators.csrf import csrf_exempt
from .serializers import ComparisonResultSerializer
from rest_framework.response import Response
from logistics.models import ControlCenter
from django.http import Http404
from rest_framework import viewsets, permissions
from django.db import models  # Add this import

logger = logging.getLogger(__name__)


class SlaughterhouseRecordViewSet(viewsets.ModelViewSet):

    queryset = SlaughterhouseRecord.objects.all().order_by('-updated_at')
    serializer_class = SlaughterhouseRecordSerializer

@csrf_exempt
def compare_weight_loss(request):
    if request.method == 'GET':
        # Retrieve all BreaderTrade records
        breader_trades = BreaderTrade.objects.all()
        
        # Perform comparison logic
        comparison_results = []

        for trade in breader_trades:
            breed = trade.breed
            trade_weight = trade.goat_weight
            total_cut_weight = 0
            
            # Calculate the total weight cut for the breed
            breed_cuts = BreedCut.objects.filter(breed=breed)
            for cut in breed_cuts:
                total_cut_weight += cut.quantity * cut.weight

            # Get the associated control center for the trade
            control_center = trade.control_center

            # Calculate breeds supplied
            breeds_supplied = trade.breeds_supplied
            
            # Subtract slaughtered quantity from the total breed supply in the control center
            if control_center:
                slaughtered_quantity = control_center.slaughterhouserecord_set.filter(breed=breed).aggregate(total_slaughtered=Sum('quantity'))['total_slaughtered']
                if slaughtered_quantity is not None:
                    # Ensure breeds_supplied does not become negative
                    breeds_supplied = max(0, breeds_supplied - slaughtered_quantity)
            
            # Calculate the weight loss percentage
            if trade_weight > 0:  # Check if trade_weight is not 0 to avoid division by zero
                weight_loss_percentage = ((trade_weight - total_cut_weight) / trade_weight) * 100
            else:
                weight_loss_percentage = 0

            # Classify weight loss
            if weight_loss_percentage < 5:
                classification = 'Normal'
            elif weight_loss_percentage < 10:
                classification = 'A little more'
            else:
                classification = 'Too much'

            # Create comparison result object
            comparison_result = {
                'id': trade.id,
                'reference': trade.reference,
                'breed': breed,
                'trade_weight': trade_weight,
                'total_cut_weight': total_cut_weight,
                'breeds_supplied': breeds_supplied,
                'weight_loss_percentage': weight_loss_percentage,
                'classification': classification
            }

            comparison_results.append(comparison_result)

        return JsonResponse(comparison_results, safe=False)
    else:
        return JsonResponse({'error': 'Only GET requests are supported for this endpoint'}, status=405)
        

class SupplyVsDemandStatisticsViewSet(viewsets.ViewSet):
    def list(self, request):
        try:
            # Assuming you have a way to get the currently logged-in seller's ID
            seller_id = request.user.id
            
            # Get total bred quantities per breed for the specified seller
            bred_quantities = BreaderTrade.objects.filter(seller_id=seller_id).values('breed').annotate(total_bred=Sum('breeds_supplied'))

            # No need to calculate slaughtered quantities as per your requirement
            
            # Prepare supply vs demand data
            supply_vs_demand_data = [
                {
                    'breed': bred_quantity['breed'],
                    'total_bred': bred_quantity['total_bred'],
                    'total_slaughtered': 0,  # Set slaughtered quantity to 0
                }
                for bred_quantity in bred_quantities
            ]

            return Response({'supply_vs_demand_data': supply_vs_demand_data})

        except Exception as e:
            return Response({'error': str(e)}, status=500)

def supply_vs_demand_statistics(request):
    try:
        # Get total bred quantities per breed for all sellers
        bred_quantities = BreaderTrade.objects.values('breed').annotate(total_bred=Sum('breeds_supplied'))

        # No need to calculate slaughtered quantities as per your requirement
        
        # Prepare supply vs demand data
        supply_vs_demand_data = [
            {
                'breed': bred_quantity['breed'],
                'total_bred': bred_quantity['total_bred'],
                'total_slaughtered': 0,  # Set slaughtered quantity to 0
            }
            for bred_quantity in bred_quantities
        ]

        print(supply_vs_demand_data)  # Add this line for debugging

        # Render the template with the data
        return render(request, 'supply_demand_statistics.html', {'supply_vs_demand_data': supply_vs_demand_data})

    except Exception as e:
        # Handle exceptions appropriately
        return render(request, 'error.html', {'error_message': str(e)})