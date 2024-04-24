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


# Templates 
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import SlaughterhouseRecord

@login_required
def inventory_records_list(request):
    allowed_roles = ['seller', 'slaughterhouse_manager']

    if request.user.role not in allowed_roles and not request.user.is_superuser:
        return redirect('unauthorized')
       
    records = SlaughterhouseRecord.objects.all().order_by('-created_at')
    context = {'records': records}
    return render(request, 'stock_shift.html', context)


from django.contrib import messages

@login_required
def confirm_slaughterhouse_record(request, record_id):
    allowed_roles = ['seller', 'slaughterhouse_manager']

    if request.user.role not in allowed_roles and not request.user.is_superuser:
        return redirect('unauthorized')
       
    # Get the slaughterhouse record
    record = get_object_or_404(SlaughterhouseRecord, pk=record_id)

    # Check if the current user has already confirmed either last_confirmation_by or confirmed_by
    if request.user == record.last_confirmation_by or request.user == record.confirmed_by:
        # If the user has already confirmed one of them, show error message
        messages.error(request, "You have already confirmed part of this item.")
        return redirect('inventory_records_list')

    # If the user hasn't confirmed anything yet, proceed with confirmation
    if not record.last_confirmation_by:
        record.last_confirmation_by = request.user
    elif not record.confirmed_by:
        record.confirmed_by = request.user

    # Save the record
    record.save()

    # Add confirmation successful message
    messages.success(request, "You have successfully partly confirmed the removal of this item from the inventory.")

    # Redirect to the inventory records list
    return redirect('inventory_records_list')


@login_required
def item_confirmation_success_view(request):
    return render(request, 'item_confirmation_success.html')

@login_required
def item_confirmation_error_view(request):
    return render(request, 'item_confirmation_error.html')

# Templates
from .forms import FinishedProductForm, SlaughterhouseRecordForm
from django.contrib import messages
from custom_registration.models import Seller

@login_required
def slaughter_house_create(request):
    """View to create a new quotation."""
    if request.method == 'POST':
        form = SlaughterhouseRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            # Retrieve the seller associated with the logged-in user
            seller = Seller.objects.get(seller=request.user)
            record.seller = seller
            record.save()
            # Redirect to the success template upon successful creation
            return redirect('record_creation_success')
        else:
            # If the form is not valid, display error messages
            messages.error(request, 'Failed to create record. Please check the form.')
    else:
        # Initialize the form with the seller field set to the seller associated with the logged-in user
        seller = Seller.objects.get(seller=request.user)
        form = SlaughterhouseRecordForm(initial={'seller': seller})
    
    return render(request, 'slaughterhouse.html', {'form': form})

def record_creation_success(request):
    return render(request, 'slaughterhouse_record_created_successfully.html')

# Templates
from inventory_management.forms import InventoryBreedSalesForm
from inventory_management.models import InventoryBreedSales
from django.db.models import Count

@login_required
def create_inventory_breed_sale(request):
    if request.method == 'POST':
        form = InventoryBreedSalesForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)  # Save form data without committing to database yet
            instance.created_by = request.user  # Assign the current user as the creator
            instance.save()  # Now save the instance with the updated fields
            
            # Check the sale type and redirect accordingly
            if instance.sale_type == 'export':
                return redirect('list_exports')
            elif instance.sale_type == 'local_sale_cut':
                return redirect('list_local_sale_cuts')
    else:
        form = InventoryBreedSalesForm()
    return render(request, 'create_inventory_breed_sale.html', {'form': form})

from django.db.models import Sum

from django.db.models import Max

@login_required
def list_exports(request):
    # Group by breed and part name and annotate with total quantity, total weight, and last updated date
    breed_part_exports = InventoryBreedSales.objects.filter(sale_type='export').values('breed', 'part_name').annotate(
        total_quantity=Sum('quantity'),
        total_weight=Sum('weight'),
        last_updated=Max('updated_at')  # Assuming you have an updated_at field in your model
    ) # Add distinct() and adjust order_by as needed
    return render(request, 'list_exports.html', {'breed_part_exports': breed_part_exports})
    
@login_required
def list_local_sale_cuts(request):
    # Group by breed and part name and annotate with total quantity, total weight, and last updated date
    breed_part_local_sales = InventoryBreedSales.objects.filter(sale_type='local_sale_cut').values('breed', 'part_name').annotate(
        total_quantity=Sum('quantity'),
        total_weight=Sum('weight'),
        last_updated=Max('updated_at')  # Assuming you have an updated_at field in your model
    )
    return render(request, 'list_local_sale_cuts.html', {'breed_part_local_sales': breed_part_local_sales})
