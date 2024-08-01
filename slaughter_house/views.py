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

# @csrf_exempt
# def compare_weight_loss(request):
#     if request.method == 'GET':
#         # Retrieve all BreaderTrade records
#         breader_trades = BreaderTrade.objects.all()
        
#         # Perform comparison logic
#         comparison_results = []

#         for trade in breader_trades:
#             # Extract relevant trade information
#             breed = trade.breed
#             trade_weight = trade.weight
#             total_cut_weight = 0
            
#             # Calculate the total weight cut for the breed
#             breed_cuts = BreedCut.objects.filter(breed=breed)
#             for cut in breed_cuts:
#                 total_cut_weight += cut.quantity * cut.weight

#             # Get the associated control center for the trade
#             control_center = trade.control_center

#             # Calculate breeds supplied
#             breeds_supplied = trade.breeds_supplied
            
#             # Subtract slaughtered quantity from the total breed supply in the control center
#             if control_center:
#                 slaughtered_quantity = control_center.slaughterhouserecord_set.filter(breed=breed).aggregate(total_slaughtered=Sum('quantity'))['total_slaughtered']
#                 if slaughtered_quantity is not None:
#                     # Ensure breeds_supplied does not become negative
#                     breeds_supplied = max(0, breeds_supplied - slaughtered_quantity)
            
#             # Calculate the weight loss percentage
#             if trade_weight > 0:  # Check if trade_weight is not 0 to avoid division by zero
#                 weight_loss_percentage = ((trade_weight - total_cut_weight) / trade_weight) * 100
#             else:
#                 weight_loss_percentage = 0

#             # Classify weight loss
#             if weight_loss_percentage < 5:
#                 classification = 'Normal'
#             elif weight_loss_percentage < 10:
#                 classification = 'A little more'
#             else:
#                 classification = 'Too much'

#             # Create comparison result object
#             comparison_result = {
#                 'id': trade.id,
#                 'reference': trade.reference,
#                 'breed': breed,
#                 'trade_weight': trade_weight,
#                 'total_cut_weight': total_cut_weight,
#                 'breeds_supplied': breeds_supplied,
#                 'weight_loss_percentage': weight_loss_percentage,
#                 'classification': classification
#             }

#             comparison_results.append(comparison_result)

#         return render(request, 'inventory_information.html', {'comparison_results': comparison_results})
#     else:
#         return JsonResponse({'error': 'Only GET requests are supported for this endpoint'}, status=405)

from django.core.paginator import Paginator

@csrf_exempt
def inventory_information(request):
    # Check if the user is a seller or superuser
    if request.user.role != 'seller' and not request.user.is_superuser:
        return redirect('unauthorized')

    # Fetch control centers associated with the current seller
    control_centers = ControlCenter.objects.filter(seller=request.user)
    
    # Initialize dictionary to store inventory information
    inventory_info = {}
    cumulative_total_remaining = 0

    # Iterate over control centers associated with the seller
    for control_center in control_centers:
        breeds_info = {}
        
        # Fetch breeds associated with the control center
        breeds = BreaderTrade.objects.filter(control_center=control_center).values_list('breed', flat=True).distinct().order_by('-created_at')
        
        for breed in breeds:
            # Calculate breed-related metrics
            total_supplied = BreaderTrade.objects.filter(control_center=control_center, breed=breed).aggregate(total_supplied=Sum('breeds_supplied'))['total_supplied'] or 0
            total_weight = BreaderTrade.objects.filter(control_center=control_center, breed=breed).aggregate(total_weight=Sum('weight'))['total_weight'] or 0
            total_slaughtered = SlaughterhouseRecord.objects.filter(control_center=control_center, breed=breed).aggregate(total_slaughtered=Sum('quantity'))['total_slaughtered'] or 0
            
            slaughter_records = SlaughterhouseRecord.objects.filter(control_center=control_center, breed=breed)
            confirmed_records_count = slaughter_records.filter(confirmed_by__isnull=False, last_confirmation_by__isnull=False).count()
            net_breed_supply = total_supplied - total_slaughtered

            # Add breed information to the dictionary
            breeds_info[breed] = {
                'total_supplied': total_supplied,
                'total_weight': total_weight,
                'total_slaughtered': total_slaughtered,
                'total_remaining': max(net_breed_supply, 0)
            }

            # Increment cumulative total remaining
            cumulative_total_remaining += max(net_breed_supply, 0)

        # Add control center information to the main dictionary
        inventory_info[control_center] = breeds_info

    # Retrieve all BreaderTrade records
    breader_trades = BreaderTrade.objects.all()
    
    # Perform comparison logic
    comparison_results = []

    for trade in breader_trades:
        # Extract relevant trade information
        breed = trade.breed
        trade_weight = trade.weight
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

    # Paginate comparison results
    paginator = Paginator(comparison_results, 3)  # Show 4 comparison results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'inventory_info': inventory_info,
        'cumulative_total_remaining': cumulative_total_remaining,
        'comparison_results': page_obj  # Pass the paginated results to the template
    }

    return render(request, 'inventory_information.html', context)


        

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

from django.shortcuts import render
from django.db.models import Sum
from collections import defaultdict

def supply_vs_demand_statistics(request):
    try:
        # Retrieve the logged-in seller
        seller = request.user

        # Get the control center associated with the seller
        control_center = seller.controlcenter_set.first()

        # Filter BreaderTrade objects by the control center of the seller
        bred_quantities = BreaderTrade.objects.filter(control_center=control_center).values('breed').annotate(total_bred=Sum('breeds_supplied'))

        # Aggregate quantities for each breed from BreaderTrade records
        breed_totals = defaultdict(int)
        for bred_quantity in bred_quantities:
            breed = bred_quantity['breed']
            total_bred = bred_quantity['total_bred']
            breed_totals[breed] += total_bred
        
        # Fetch demand data from SlaughterhouseRecord
        slaughterhouse_records = SlaughterhouseRecord.objects.filter(control_center=control_center)
        demand_data = defaultdict(int)
        for record in slaughterhouse_records:
            breed = record.breed
            quantity = record.quantity
            demand_data[breed] += quantity

        # Prepare supply vs demand data
        supply_vs_demand_data = [
            {
                'breed': breed,
                'total_bred': breed_totals.get(breed, 0),
                'total_slaughtered': demand_data.get(breed, 0),
            }
            for breed in set(breed_totals.keys()) | set(demand_data.keys())  # Combine keys from both dictionaries
        ]

        # Render the template with the data
        return render(request, 'seller_dashboard.html', {'supply_vs_demand_data': supply_vs_demand_data})

    except Exception as e:
        # Handle exceptions appropriately
        return render(request, 'error.html', {'error_message': str(e)})


# Templates 
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import SlaughterhouseRecord

@login_required
def inventory_records_list(request):
    allowed_roles = ['seller', 'slaughterhouse_manager', 'collateral_manager', 'inventory_manager']

    if request.user.role not in allowed_roles and not request.user.is_superuser:
        return redirect('unauthorized')
       
    records = SlaughterhouseRecord.objects.all().order_by('-created_at')
    context = {'records': records}
    return render(request, 'stock_shift.html', context)


from django.contrib import messages

@login_required
def confirm_slaughterhouse_record(request, record_id):
    allowed_roles = ['seller', 'inventory_manager', 'collateral_manager']

    if request.user.role not in allowed_roles and not request.user.is_superuser:
        return redirect('unauthorized')

    # Get the slaughterhouse record
    record = get_object_or_404(SlaughterhouseRecord.objects.order_by('-created_at'), pk=record_id)

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
from transaction.forms import WeightRecordForm

from django.contrib import messages
from custom_registration.models import Seller

from django.contrib.auth.decorators import login_required

@login_required
def slaughterhouse_dashboard(request):
    # Filter trades where reception is confirmed and weight is recorded
    trades = BreaderTrade.objects.filter(reception_confirmed=True, weight__isnull=False)
    
    # Aggregate Data
    total_items_received = trades.aggregate(total_items_received=Sum('breeds_supplied'))['total_items_received']
    total_reception_confirmed = trades.aggregate(total_reception_confirmed=Count('id'))['total_reception_confirmed']
    total_received_weight = trades.aggregate(total_received_weight=Sum('received_weight'))['total_received_weight']
    total_good_condition = trades.aggregate(total_good_condition=Sum('good_condition'))['total_good_condition']
    total_destroyed_condition = trades.aggregate(total_destroyed_condition=Sum('destroyed_condition'))['total_destroyed_condition']
    total_poor_condition = trades.aggregate(total_poor_condition=Sum('poor_condition'))['total_poor_condition']
    
    context = {
        'trades': trades,
        'total_items_received': total_items_received or 0,
        'total_reception_confirmed': total_reception_confirmed or 0,
        'total_received_weight': total_received_weight or 0,
        'total_good_condition': total_good_condition or 0,
        'total_destroyed_condition': total_destroyed_condition or 0,
        'total_poor_condition': total_poor_condition or 0,
        'form': WeightRecordForm()  # Include the form for the modal
    }
    
    return render(request, 'slaughterhouse_dashboard.html', context)

from django.db import transaction


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction


@login_required
def slaughter_house_create(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)

    if request.method == 'POST':
        form = SlaughterhouseRecordForm(request.POST)
        if form.is_valid():
            # Get the form values
            weight = form.cleaned_data.get('weight')
            breeds_supplied = form.cleaned_data.get('breeds_supplied')

            # Initialize trade values to 0 if None
            trade_breeds_supplied = trade.breeds_supplied or 0
            trade_weight = trade.weight or 0

            # Check if the amounts to be deducted are valid
            if breeds_supplied > trade_breeds_supplied:
                messages.error(request, 'Breeds supplied exceeds the available amount.')
                return redirect('slaughter_house_create', trade_id=trade_id)

            if weight > trade_weight:
                messages.error(request, 'Weight exceeds the available weight.')
                return redirect('slaughter_house_create', trade_id=trade_id)

            # Perform the deduction
            with transaction.atomic():
                trade.breeds_supplied -= breeds_supplied
                trade.weight -= weight
                trade.save()
                messages.success(request, 'You have successfully removed an item to be slaughtered.')
                return redirect('slaughterhouse_dashboard')
        else:
            messages.error(request, 'Failed to create record. Please check the form.')
    else:
        form = SlaughterhouseRecordForm()

    return render(request, 'slaughterhouse.html', {'form': form, 'trade': trade})


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

# Weiht loss 
from django.db.models import Sum
from django.shortcuts import render

from django.shortcuts import render
from inventory_management.models import InventoryBreedSales
from inventory_management.models import BreedCut

from decimal import Decimal

from django.http import JsonResponse

from django.shortcuts import render
from decimal import Decimal
from django.core.paginator import Paginator

@login_required
def weight_comparison_view(request):
    comparison_results = []

    breader_trades = BreaderTrade.objects.all()

    for trade in breader_trades:
        reference = trade.reference
        breed = trade.breed
        trade_weight = trade.weight
        total_cut_weight = Decimal(0)  # Initialize total cut weight

        breed_cuts = InventoryBreedSales.objects.filter(reference=reference, breed=breed)
        for breed_cut in breed_cuts:
            # Convert breed_cut.weight and breed_cut.quantity to Decimal
            weight = Decimal(breed_cut.weight)
            quantity = Decimal(breed_cut.quantity)
            total_cut_weight += weight * quantity

        weight_loss_percentage = 0
        if trade_weight:
            weight_loss_percentage = ((total_cut_weight - trade_weight) / trade_weight) * 100

        classification = "Normal"
        if weight_loss_percentage > 5:
            classification = "Above Average"
        elif weight_loss_percentage < -5:
            classification = "Below Average"

        comparison_results.append({
            'reference': reference,
            'breed': breed,
            'trade_weight': trade_weight,
            'total_cut_weight': total_cut_weight,
            'weight_loss_percentage': weight_loss_percentage,
            'classification': classification
        })

    return render(request, 'inventory_information.html', {'comparison_results': comparison_results})
