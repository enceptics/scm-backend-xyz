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
from django.contrib.auth.decorators import login_required

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

from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models.functions import Cast
from django.db.models import Sum, DecimalField, F
from custom_registration.models import Seller

@login_required
def inventory_information(request):
    user_role = request.user.role
    seller = Seller.objects.get(seller=request.user)  # Assuming you have a Seller model related to the user
    inventory_info = {}
    cumulative_total_remaining = Decimal('0.0')
    # Fetch control centers for the logged-in seller
    control_centers = ControlCenter.objects.filter(seller=request.user)


    # Fetch control centers based on user role
    if user_role == 'seller':
        control_centers = ControlCenter.objects.filter(seller=request.user)
    elif user_role == 'bank':
        control_centers = ControlCenter.objects.all()
    elif user_role == 'collateral_manager':
        control_centers = ControlCenter.objects.filter(collateral_manager=request.user)
    else:
        return redirect('unauthorized')

  # Iterate over control centers to gather breed information
    for control_center in control_centers:
        breeds_info = {}
        breeds = BreaderTrade.objects.filter(control_center=control_center).values_list('breed', flat=True).distinct().order_by('-created_at')

        for breed in breeds:
            total_supplied = BreaderTrade.objects.filter(control_center=control_center, breed=breed).aggregate(
                total_supplied=Sum('breeds_supplied')
            )['total_supplied'] or Decimal('0.0')
            
            total_weight = BreedCut.objects.filter(breed=breed).aggregate(
                total_weight=Sum(
                    Cast('quantity', output_field=DecimalField()) * Cast('weight', output_field=DecimalField())
                )
            )['total_weight'] or Decimal('0.0')

            total_slaughtered = SlaughterhouseRecord.objects.filter(control_center=control_center, breed=breed).aggregate(
                total_slaughtered=Sum('quantity')
            )['total_slaughtered'] or Decimal('0.0')

            net_breed_supply = total_supplied - total_slaughtered

            breeds_info[breed] = {
                'total_supplied': total_supplied,
                'total_weight': total_weight,
                'total_slaughtered': total_slaughtered,
                'total_remaining': max(net_breed_supply, 0)
            }
            cumulative_total_remaining += max(net_breed_supply, 0)

        inventory_info[control_center] = breeds_info

    # Fetch relevant BreaderTrade records
    breader_trades = BreaderTrade.objects.all() if user_role == 'bank' else BreaderTrade.objects.filter(control_center__in=control_centers)
    comparison_results = []

    for trade in breader_trades:
        breed = trade.breed
        initial_weight = trade.weight or Decimal('0.0')
        part_weight = trade.part_weight or Decimal('0.0')

        # Calculate remaining supply in control center
        control_center = trade.control_center
        breeds_supplied = trade.breeds_supplied

        if control_center:
            slaughtered_quantity = control_center.slaughterhouserecord_set.filter(breed=breed).aggregate(
                total_slaughtered=Sum('quantity')
            )['total_slaughtered'] or Decimal('0.0')
            breeds_supplied = max(0, breeds_supplied - slaughtered_quantity)

        # Calculate weight loss percentage
        weight_loss_percentage = round(((initial_weight - part_weight) / initial_weight) * 100, 1) if initial_weight > 0 else 0

        # Classify weight loss
        if weight_loss_percentage < 5:
            classification = 'Normal'
        elif weight_loss_percentage < 10:
            classification = 'A little more'
        else:
            classification = 'Too much'

        comparison_results.append({
            'id': trade.id,
            'reference': trade.reference,
            'breed': breed,
            'initial_weight': initial_weight,
            'part_weight': part_weight,
            'breeds_supplied': breeds_supplied,
            'weight_loss_percentage': weight_loss_percentage,
            'classification': classification
        })
        print('comparison', comparison_results)

    # Pagination of comparison results
    paginator = Paginator(comparison_results, 10)  # Show 10 comparison results per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Prepare context and render the template
    context = {
        'inventory_info': inventory_info,
        'cumulative_total_remaining': cumulative_total_remaining,
        'comparison_results': page_obj
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
from django.shortcuts import redirect, get_object_or_404
from .models import SlaughterhouseRecord

@login_required
def inventory_records_list(request):
    allowed_roles = ['seller', 'slaughterhouse_manager','inventory_manager']

    if request.user.role not in allowed_roles and not request.user.is_superuser:
        return redirect('unauthorized')
       
    records = BreaderTrade.objects.filter().order_by('-created_at')
    context = {'records': records}
    return render(request, 'stock_shift.html', context)


from django.contrib import messages

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
        form = SlaughterhouseRecordForm(request.POST, trade=trade)
        if form.is_valid():
            if trade.create_slaughter_record(form):
                messages.success(request, 'Record created successfully. Awaiting confirmation from both parties.')
                return redirect('slaughterhouse_dashboard')
            else:
                messages.error(request, 'Failed to create record. Please try again.')
        else:
            messages.error(request, 'Failed to create record. Please check the form.')
    else:
        form = SlaughterhouseRecordForm(trade=trade)

    return render(request, 'slaughterhouse.html', {'form': form, 'trade': trade})


@login_required
def confirm_slaughter_record(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)

    if request.method == 'POST':
        # Handle the confirmation based on user role
        if request.user.role == 'seller' and not trade.first_confirmed_by:
            trade.confirm_as_seller(request.user)
            messages.success(request, 'Confirmed as Seller.')
        elif request.user.role == 'inventory_manager' and trade.first_confirmed_by and not trade.last_confirmation_by:
            trade.confirm_as_inventory_manager(request.user)
            messages.success(request, 'Confirmed as Inventory Manager and record updated.')
            # Mark as completed if both confirmations are done
            if trade.first_confirmed_by and trade.last_confirmation_by:
                trade.set_completed()
        else:
            messages.error(request, 'Invalid confirmation attempt.')

        return redirect('slaughterhouse_dashboard')

    messages.error(request, 'Invalid request method.')
    return redirect('slaughterhouse_dashboard')


# Templates
from inventory_management.forms import InventoryBreedSalesForm
from inventory_management.models import InventoryBreedSales
from django.db.models import Count

# add to warehouse
def create_finished_products(request, pk):
    if request.method == 'POST':
        form = InventoryBreedSalesForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            # Add the parts to the inventory
            instance.add_part_to_inventory(instance.part_weight, instance.part_quantity)
            instance.save()
            return redirect('some_success_url')
    else:
        form = InventoryBreedSalesForm()

    return render(request, 'template_name.html', {'form': form})

from decimal import Decimal

@login_required
def create_inventory_breed_sale(request, trade_id):
    trade = get_object_or_404(BreaderTrade, id=trade_id)

    if request.method == 'POST':
        form = InventoryBreedSalesForm(request.POST)
        if form.is_valid():
            new_trade = form.save(commit=False)
            new_trade.breed = trade.breed
            new_trade.breeder = trade.breeder
            new_trade.seller = trade.seller
            new_trade.control_center = trade.control_center
            new_trade.breeds_supplied = trade.breeds_supplied
            new_trade.initial_weight = trade.initial_weight
            new_trade.reference = trade.reference
            new_trade.created_by = request.user

            # Ensure values are valid and handle None
            part_quantity = new_trade.part_quantity or 0
            part_weight = new_trade.part_weight or Decimal('0.0')

            # Check for existing record with the same breed and part_name
            existing_trade = BreaderTrade.objects.filter(
                breed=new_trade.breed,
                part_name=new_trade.part_name,
                sale_type=new_trade.sale_type
            ).first()

            if existing_trade:
                # Update existing record by adding new values
                existing_trade.add_part_to_inventory(part_weight, part_quantity)
            else:
                # Create new record
                new_trade.save()

            # Check the sale type and redirect accordingly
            if new_trade.sale_type == 'export':
                messages.success(request, "Export items successfully added to the chilled warehouse")

                return redirect('slaughterhouse_dashboard')
            elif new_trade.sale_type == 'local_sale_cut':
                messages.success(request, "Local sale items successfully added to the chilled warehouse")

                return redirect('slaughterhouse_dashboard')

    else:
        form = InventoryBreedSalesForm(initial={'breed': trade.breed})

    return render(request, 'create_inventory_breed_sale.html', {'form': form})

    

from django.db.models import Sum

from django.db.models import Max
@login_required
def list_exports(request):
    # Assuming there's a foreign key 'user' in BreaderTrade model
    breed_part_exports = BreaderTrade.objects.filter(
        sale_type='export',
        seller=request.user  # Filter by the currently logged-in user
    ).values('breed', 'part_name').annotate(
        total_quantity=Sum('part_quantity'),
        total_weight=Sum('part_weight'),
        last_updated=Max('updated_at')
    )
    return render(request, 'list_exports.html', {'breed_part_exports': breed_part_exports})

@login_required
def list_local_sale_cuts(request):
    # Assuming there's a foreign key 'user' in BreaderTrade model
    breed_part_local_sales = BreaderTrade.objects.filter(
        sale_type='local_sale_cut',
        seller=request.user  # Filter by the currently logged-in user
    ).values('breed', 'part_name').annotate(
        total_quantity=Sum('part_quantity'),
        total_weight=Sum('part_weight'),
        last_updated=Max('updated_at')
    )
    return render(request, 'list_local_sale_cuts.html', {'breed_part_local_sales': breed_part_local_sales})



