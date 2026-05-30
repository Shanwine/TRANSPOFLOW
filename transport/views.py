from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum
from accounts.views import driver_required
from .models import (Vehicle, Driver, Trip, Passenger, DriverLocation,
                     Maintenance, PartsInventory, Booking, Notification, FuelLog,
                     TripSchedule, TIME_SLOT_CHOICES)
from .forms import (VehicleForm, DriverForm, TripForm, PassengerForm,
                    MaintenanceForm, PartsInventoryForm, CustomerBookingForm, FuelLogForm)
from .models import (Vehicle, Driver, Trip, Passenger, DriverLocation,
                     Maintenance, PartsInventory, Booking, Notification, FuelLog,
                     TripSchedule, TIME_SLOT_CHOICES, Attendance)
import json

# ─── HELPER: Notify all admins ───────────────────────────────────────────────

def notify_admins(title, message, notif_type='info'):
    for admin in User.objects.filter(is_staff=True):
        Notification.objects.create(
            user=admin, title=title, message=message, notif_type=notif_type,
        )


# ─── ADMIN DASHBOARD ────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    total_vehicles      = Vehicle.objects.count()
    active_vehicles     = Vehicle.objects.filter(status='active').count()
    inactive_vehicles   = Vehicle.objects.filter(status='inactive').count()
    maint_vehicles      = Vehicle.objects.filter(status='maintenance').count()
    total_drivers       = Driver.objects.count()
    active_drivers      = Driver.objects.filter(status='active').count()
    total_trips         = Trip.objects.count()
    ongoing_trips       = Trip.objects.filter(status='ongoing').count()
    completed_trips     = Trip.objects.filter(status='completed').count()
    recent_trips        = Trip.objects.all().order_by('-id')[:5]
    total_passengers    = Passenger.objects.count()
    total_bookings      = Booking.objects.count()
    pending_bookings    = Booking.objects.filter(status='pending').count()
    confirmed_bookings  = Booking.objects.filter(status='confirmed').count()
    completed_bookings  = Booking.objects.filter(status='completed').count()
    cancelled_bookings  = Booking.objects.filter(status='cancelled').count()
    recent_bookings     = Booking.objects.select_related('customer', 'trip').order_by('-booked_at')[:8]
    fuel_agg            = FuelLog.objects.aggregate(total_cost=Sum('total_cost'), total_liters=Sum('liters'))
    fuel_total_cost     = fuel_agg['total_cost']   or 0
    fuel_total_liters   = fuel_agg['total_liters'] or 0
    planned_maint       = Maintenance.objects.filter(status='planned').count()
    inprogress_maint    = Maintenance.objects.filter(status='inprogress').count()
    notifications       = Notification.objects.filter(user=request.user, is_read=False)[:5]

    completed_bookings_qs = Booking.objects.filter(status='completed')
    total_commission      = completed_bookings_qs.aggregate(t=Sum('commission_fee'))['t'] or 0
    total_fare_collected  = completed_bookings_qs.aggregate(t=Sum('total_fare'))['t'] or 0
    total_driver_earnings = completed_bookings_qs.aggregate(t=Sum('driver_earnings'))['t'] or 0
    today = timezone.now().date()
    today_attendances = Attendance.objects.filter(date=today).select_related('driver')
    present_drivers = today_attendances.filter(time_in__isnull=False)
    absent_drivers = Driver.objects.filter(status='active').exclude(
    id__in=present_drivers.values_list('driver__id', flat=True)
)

    pending_fare_approvals = Trip.objects.filter(
        suggested_fare__isnull=False, fare_approved=False
    ).count()
    

    context = {
        'total_vehicles': total_vehicles, 'active_vehicles': active_vehicles,
        'inactive_vehicles': inactive_vehicles, 'maint_vehicles': maint_vehicles,
        'total_drivers': total_drivers, 'active_drivers': active_drivers,
        'total_trips': total_trips, 'ongoing_trips': ongoing_trips,
        'completed_trips': completed_trips, 'recent_trips': recent_trips,
        'total_passengers': total_passengers,
        'total_bookings': total_bookings, 'pending_bookings': pending_bookings,
        'confirmed_bookings': confirmed_bookings, 'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings, 'recent_bookings': recent_bookings,
        'fuel_total_cost': fuel_total_cost, 'fuel_total_liters': fuel_total_liters,
        'planned_maint': planned_maint, 'inprogress_maint': inprogress_maint,
        'notifications': notifications,
        'total_commission': total_commission,
        'total_fare_collected': total_fare_collected,
        'total_driver_earnings': total_driver_earnings,
        'pending_fare_approvals': pending_fare_approvals,
        'today_attendances': today_attendances,
        'present_drivers': present_drivers,
        'absent_drivers': absent_drivers,
    }
    return render(request, 'transport/dashboard.html', context)


# ─── VEHICLE CRUD ────────────────────────────────────────────────────────────

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'transport/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_create(request):
    if request.method == 'POST':
        plate_number = request.POST.get('plate_number')
        if Vehicle.objects.filter(plate_number=plate_number).exists():
            messages.error(request, f'Plate number "{plate_number}" already exists!')
            return render(request, 'transport/vehicle_form.html')
        Vehicle.objects.create(
            name=request.POST.get('name'),
            plate_number=plate_number,
            type=request.POST.get('type'),
            capacity=request.POST.get('capacity'),
            status=request.POST.get('status'),
        )
        messages.success(request, 'Vehicle added successfully!')
        return redirect('vehicle_list')
    return render(request, 'transport/vehicle_form.html')

@login_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle updated successfully!')
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'transport/vehicle_form.html', {'form': form})

@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted successfully!')
        return redirect('vehicle_list')
    return render(request, 'transport/vehicle_confirm_delete.html', {'vehicle': vehicle})


# ─── DRIVER CRUD ─────────────────────────────────────────────────────────────

@login_required
def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'transport/driver_list.html', {'drivers': drivers})

@login_required
def driver_create(request):
    if request.method == 'POST':
        Driver.objects.create(
            name=request.POST.get('name'), mobile=request.POST.get('mobile'),
            age=request.POST.get('age'), license_no=request.POST.get('license_no'),
            license_expiry=request.POST.get('license_expiry'), experience=request.POST.get('experience'),
            date_of_joining=request.POST.get('date_of_joining'), reference=request.POST.get('reference'),
            address=request.POST.get('address'), status=request.POST.get('status'),
            photo=request.FILES.get('photo'),
        )
        messages.success(request, 'Driver added successfully!')
        return redirect('driver_list')
    return render(request, 'transport/driver_form.html')

@login_required
def driver_update(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, 'Driver updated successfully!')
            return redirect('driver_list')
    else:
        form = DriverForm(instance=driver)
    return render(request, 'transport/driver_form.html', {'form': form})

@login_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        driver.delete()
        messages.success(request, 'Driver deleted successfully!')
        return redirect('driver_list')
    return render(request, 'transport/driver_confirm_delete.html', {'driver': driver})


# ─── TRIP CRUD ───────────────────────────────────────────────────────────────

@login_required
def trip_list(request):
    trips = Trip.objects.all()
    return render(request, 'transport/trip_list.html', {'trips': trips})


@login_required
def trip_create(request):
    vehicle_types = {
        str(v.pk): v.type
        for v in Vehicle.objects.all()
    }

    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle')
        try:
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            vtype = vehicle.type  # 'bus', 'van', 'truck'(motor), 'car'
        except Vehicle.DoesNotExist:
            vehicle = None
            vtype = ''

        # Motor (truck) and Car: bypass form, direct create with TBD
        is_ride = vtype in ('truck', 'car')

        if is_ride:
            driver_id = request.POST.get('driver')
            driver = Driver.objects.filter(pk=driver_id).first() if driver_id else None
            Trip.objects.create(
                origin='TBD',
                destination='TBD',
                vehicle=vehicle,
                driver=driver,
                status=request.POST.get('status', 'pending'),
                rate_per_km=request.POST.get('rate_per_km') or 0,
                commission_rate=request.POST.get('commission_rate') or 10,
                fare_per_seat=0,
                distance_km=0,
            )
            messages.success(request, 'Trip created successfully!')
            return redirect('trip_list')
        else:
            # Bus/Van: use normal TripForm
            form = TripForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Trip created successfully!')
                return redirect('trip_list')
            # If form invalid, fall through to re-render with errors
    else:
        form = TripForm()

    return render(request, 'transport/trip_form.html', {
        'form': form,
        'vehicle_types_json': json.dumps(vehicle_types),
    })


@login_required
def trip_update(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    vehicle_types = {
        str(v.pk): v.type
        for v in Vehicle.objects.all()
    }
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, 'Trip updated successfully!')
            return redirect('trip_list')
    else:
        form = TripForm(instance=trip)
    return render(request, 'transport/trip_form.html', {
        'form': form,
        'vehicle_types_json': json.dumps(vehicle_types),
    })
@login_required
def trip_delete(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if request.method == 'POST':
        trip.delete()
        messages.success(request, 'Trip deleted successfully!')
        return redirect('trip_list')
    return render(request, 'transport/trip_confirm_delete.html', {'trip': trip})


# ─── PASSENGER CRUD ──────────────────────────────────────────────────────────

@login_required
def passenger_list(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    passengers = Passenger.objects.filter(trip=trip)
    return render(request, 'transport/passenger_list.html', {'passengers': passengers, 'trip': trip})

@login_required
def passenger_create(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if request.method == 'POST':
        form = PassengerForm(request.POST)
        if form.is_valid():
            passenger = form.save(commit=False)
            passenger.trip = trip
            passenger.save()
            messages.success(request, 'Passenger added successfully!')
            return redirect('passenger_list', trip_id=trip_id)
    else:
        form = PassengerForm()
    return render(request, 'transport/passenger_form.html', {'form': form, 'trip': trip})

@login_required
def passenger_update(request, pk):
    passenger = get_object_or_404(Passenger, pk=pk)
    trip = passenger.trip
    if request.method == 'POST':
        form = PassengerForm(request.POST, instance=passenger)
        if form.is_valid():
            form.save()
            messages.success(request, 'Passenger updated successfully!')
            return redirect('passenger_list', trip_id=trip.id)
    else:
        form = PassengerForm(instance=passenger)
    return render(request, 'transport/passenger_form.html', {'form': form, 'trip': trip})

@login_required
def passenger_delete(request, pk):
    passenger = get_object_or_404(Passenger, pk=pk)
    trip = passenger.trip
    if request.method == 'POST':
        passenger.delete()
        messages.success(request, 'Passenger deleted successfully!')
        return redirect('passenger_list', trip_id=trip.id)
    return render(request, 'transport/passenger_confirm_delete.html', {'passenger': passenger})


# ─── REPORTS / MAP ───────────────────────────────────────────────────────────

@login_required
def reports(request):
    import json
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')

    bookings_qs = Booking.objects.all()
    trips_qs    = Trip.objects.all()
    fuel_qs     = FuelLog.objects.all()

    if date_from:
        bookings_qs = bookings_qs.filter(booked_at__date__gte=date_from)
        trips_qs    = trips_qs.filter(departure_time__date__gte=date_from)
        fuel_qs     = fuel_qs.filter(date__gte=date_from)
    if date_to:
        bookings_qs = bookings_qs.filter(booked_at__date__lte=date_to)
        trips_qs    = trips_qs.filter(departure_time__date__lte=date_to)
        fuel_qs     = fuel_qs.filter(date__lte=date_to)

    completed_qs = bookings_qs.filter(status='completed')
    booking_summary = {
        'total':     bookings_qs.count(),
        'pending':   bookings_qs.filter(status='pending').count(),
        'confirmed': bookings_qs.filter(status='confirmed').count(),
        'completed': completed_qs.count(),
        'cancelled': bookings_qs.filter(status='cancelled').count(),
    }

    rev = completed_qs.aggregate(
        fare=Sum('total_fare'),
        commission=Sum('commission_fee'),
        driver_earn=Sum('driver_earnings'),
    )
    revenue_summary = {
        'total_fare':       rev['fare']        or 0,
        'total_commission': rev['commission']  or 0,
        'driver_earnings':  rev['driver_earn'] or 0,
    }

    trip_summary = {
        'total':     trips_qs.count(),
        'pending':   trips_qs.filter(status='pending').count(),
        'ongoing':   trips_qs.filter(status='ongoing').count(),
        'completed': trips_qs.filter(status='completed').count(),
    }

    fuel_agg = fuel_qs.aggregate(total_cost=Sum('total_cost'), total_liters=Sum('liters'))
    fuel_summary = {
        'total_cost':   fuel_agg['total_cost']   or 0,
        'total_liters': fuel_agg['total_liters'] or 0,
    }

    top_drivers = (
        completed_qs
        .values('trip__driver__name')
        .annotate(earnings=Sum('driver_earnings'), trips=Count('id'))
        .order_by('-earnings')[:5]
    )

    top_routes = (
        completed_qs
        .values('trip__origin', 'trip__destination')
        .annotate(count=Count('id'), revenue=Sum('total_fare'))
        .order_by('-count')[:5]
    )

    monthly = (
        Booking.objects.filter(status='completed')
        .annotate(month=TruncMonth('booked_at'))
        .values('month')
        .annotate(revenue=Sum('total_fare'), bookings=Count('id'))
        .order_by('month')
    )
    chart_labels   = [m['month'].strftime('%b %Y') for m in monthly]
    chart_revenue  = [float(m['revenue'] or 0) for m in monthly]
    chart_bookings = [m['bookings'] for m in monthly]

    status_labels = ['Pending', 'Confirmed', 'Completed', 'Cancelled']
    status_data   = [
        booking_summary['pending'],
        booking_summary['confirmed'],
        booking_summary['completed'],
        booking_summary['cancelled'],
    ]

    context = {
        'date_from':        date_from,
        'date_to':          date_to,
        'booking_summary':  booking_summary,
        'revenue_summary':  revenue_summary,
        'trip_summary':     trip_summary,
        'fuel_summary':     fuel_summary,
        'top_drivers':      top_drivers,
        'top_routes':       top_routes,
        'chart_labels':     json.dumps(chart_labels),
        'chart_revenue':    json.dumps(chart_revenue),
        'chart_bookings':   json.dumps(chart_bookings),
        'status_labels':    json.dumps(status_labels),
        'status_data':      json.dumps(status_data),
    }
    return render(request, 'transport/reports.html', context)


@login_required
def map_view(request):
    return render(request, 'transport/map.html')

@login_required
def update_driver_location(request):
    if request.method == 'POST':
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        DriverLocation.objects.update_or_create(driver=request.user, defaults={'latitude': lat, 'longitude': lng})
        return JsonResponse({'status': 'ok'})

def get_driver_location(request):
    driver_user_ids = Driver.objects.values_list('user_id', flat=True)
    locations = DriverLocation.objects.select_related('driver').filter(
        driver__id__in=driver_user_ids
    )
    data = []
    for loc in locations:
        try:
            driver_profile = Driver.objects.get(user=loc.driver)
            name = driver_profile.name
            status = driver_profile.status
        except Driver.DoesNotExist:
            name = loc.driver.username
            status = 'unknown'
        data.append({
            'lat': str(loc.latitude),
            'lng': str(loc.longitude),
            'driver': name,
            'status': status,
            'updated_at': loc.updated_at.strftime('%b %d, %I:%M %p'),
        })
    return JsonResponse({'drivers': data})


# ─── MAINTENANCE CRUD ────────────────────────────────────────────────────────

@login_required
def maintenance_list(request):
    maintenances = Maintenance.objects.all().order_by('-start_date')
    return render(request, 'transport/maintenance_list.html', {'maintenances': maintenances})

@login_required
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance added successfully!')
            return redirect('maintenance_list')
    else:
        form = MaintenanceForm()
    return render(request, 'transport/maintenance_form.html', {'form': form})

@login_required
def maintenance_update(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maintenance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance updated successfully!')
            return redirect('maintenance_list')
    else:
        form = MaintenanceForm(instance=maintenance)
    return render(request, 'transport/maintenance_form.html', {'form': form})

@login_required
def maintenance_delete(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    if request.method == 'POST':
        maintenance.delete()
        messages.success(request, 'Maintenance deleted successfully!')
        return redirect('maintenance_list')
    return render(request, 'transport/maintenance_confirm_delete.html', {'maintenance': maintenance})


# ─── PARTS INVENTORY CRUD ────────────────────────────────────────────────────

@login_required
def parts_list(request):
    parts = PartsInventory.objects.all().order_by('-created_at')
    return render(request, 'transport/parts_list.html', {'parts': parts})

@login_required
def parts_create(request):
    if request.method == 'POST':
        form = PartsInventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Part added successfully!')
            return redirect('parts_list')
    else:
        form = PartsInventoryForm()
    return render(request, 'transport/parts_form.html', {'form': form})

@login_required
def parts_update(request, pk):
    part = get_object_or_404(PartsInventory, pk=pk)
    if request.method == 'POST':
        form = PartsInventoryForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            messages.success(request, 'Part updated successfully!')
            return redirect('parts_list')
    else:
        form = PartsInventoryForm(instance=part)
    return render(request, 'transport/parts_form.html', {'form': form})

@login_required
def parts_delete(request, pk):
    part = get_object_or_404(PartsInventory, pk=pk)
    if request.method == 'POST':
        part.delete()
        messages.success(request, 'Part deleted successfully!')
        return redirect('parts_list')
    return render(request, 'transport/parts_confirm_delete.html', {'part': part})


# ─── CUSTOMER PANEL ──────────────────────────────────────────────────────────

@login_required
def customer_dashboard(request):
    my_bookings = Booking.objects.filter(customer=request.user)
    context = {
        'active_bookings':    my_bookings.filter(status='confirmed'),
        'pending_bookings':   my_bookings.filter(status='pending'),
        'completed_bookings': my_bookings.filter(status='completed'),
        'cancelled_bookings': my_bookings.filter(status='cancelled'),
        'recent_bookings':    my_bookings.order_by('-booked_at')[:5],
        'available_trips':    Trip.objects.filter(status='pending'),
        'notifications':      Notification.objects.filter(user=request.user, is_read=False)[:5],
        'total_bookings':     my_bookings.count(),
    }
    return render(request, 'transport/customer_dashboard.html', context)

@login_required
def customer_vehicle_list(request):
    vehicles = Vehicle.objects.filter(status='active', is_active=True)
    query = request.GET.get('q', '')
    vehicle_type = request.GET.get('type', '')
    if query:
        vehicles = vehicles.filter(Q(name__icontains=query) | Q(plate_number__icontains=query))
    if vehicle_type:
        vehicles = vehicles.filter(type=vehicle_type)
    return render(request, 'transport/customer_vehicles.html', {
        'vehicles': vehicles, 'query': query,
        'vehicle_type': vehicle_type, 'type_choices': Vehicle.TYPE_CHOICES,
    })

@login_required
def available_trips(request):
    trips = Trip.objects.filter(status='pending')
    query = request.GET.get('q', '')
    if query:
        trips = trips.filter(Q(origin__icontains=query) | Q(destination__icontains=query))
    return render(request, 'transport/available_trips.html', {'trips': trips, 'query': query})


@login_required
def book_trip(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    already_booked = Booking.objects.filter(customer=request.user, trip=trip).exclude(status='cancelled').exists()
    if already_booked:
        messages.warning(request, 'You have already booked this trip.')
        return redirect('my_bookings')

    if request.method == 'POST':
        form = CustomerBookingForm(request.POST)
        if form.is_valid():
            payment_method = request.POST.get('payment_method', '').strip()
            mobile_number  = request.POST.get('mobile_number', '').strip()
            card_number    = request.POST.get('card_number', '').replace(' ', '').strip()

            if not payment_method:
                messages.error(request, 'Please select a payment method.')
                return render(request, 'transport/book_trip.html', {'trip': trip, 'form': form})

            if payment_method in ('gcash', 'maya'):
                if not mobile_number or len(mobile_number) != 11 or not mobile_number.startswith('09'):
                    messages.error(request, 'Please enter a valid 11-digit mobile number starting with 09.')
                    return render(request, 'transport/book_trip.html', {'trip': trip, 'form': form})

            if payment_method == 'credit_card':
                card_holder = request.POST.get('card_holder', '').strip()
                card_expiry = request.POST.get('card_expiry', '').strip()
                card_cvv    = request.POST.get('card_cvv', '').strip()
                if len(card_number) < 16 or not card_holder or len(card_expiry) < 5 or len(card_cvv) < 3:
                    messages.error(request, 'Please fill in all card details correctly.')
                    return render(request, 'transport/book_trip.html', {'trip': trip, 'form': form})

            booking = form.save(commit=False)
            booking.customer       = request.user
            booking.trip           = trip
            booking.status         = 'pending'
            booking.payment_method = payment_method
            booking.mobile_number  = mobile_number if payment_method in ('gcash', 'maya') else ''
            booking.card_last4     = card_number[-4:] if payment_method == 'credit_card' and card_number else ''

            if payment_method == 'cash':
                booking.mobile_number = ''
                booking.card_last4    = ''

            booking.pickup_location = request.POST.get('pickup_location', '').strip()
            pickup_lat = request.POST.get('pickup_latitude', '').strip()
            pickup_lng = request.POST.get('pickup_longitude', '').strip()
            if pickup_lat and pickup_lng:
                try:
                    booking.pickup_latitude  = float(pickup_lat)
                    booking.pickup_longitude = float(pickup_lng)
                except ValueError:
                    pass

            booking.save()

            payment_labels = {
                'cash': 'Cash',
                'gcash': 'GCash',
                'maya': 'Maya (PayMaya)',
                'credit_card': 'Credit/Debit Card',
            }
            payment_label = payment_labels.get(payment_method, payment_method)

            Notification.objects.create(
                user=request.user, title='Booking Submitted',
                message=(
                    f'Your booking for {trip.origin} → {trip.destination} is pending. '
                    f'Total Fare: ₱{booking.total_fare}. Payment: {payment_label}.'
                ),
                notif_type='info',
            )

            pickup_info = booking.pickup_location or 'Not provided'
            notify_admins(
                title='📋 New Booking Received',
                message=(
                    f'{request.user.username} booked {trip.origin} → {trip.destination} '
                    f'({booking.seats} seat(s)). '
                    f'Fare: ₱{booking.total_fare} | Commission: ₱{booking.commission_fee} | '
                    f'Driver Earnings: ₱{booking.driver_earnings} | Payment: {payment_label}. '
                    f'📍 Pickup: {pickup_info}'
                ),
                notif_type='info',
            )

            messages.success(request, f'Trip booked! Total Fare: ₱{booking.total_fare}')
            return redirect('my_bookings')

    else:
        form = CustomerBookingForm()
    return render(request, 'transport/book_trip.html', {'trip': trip, 'form': form})


@login_required
def my_bookings(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(customer=request.user).order_by('-booked_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    return render(request, 'transport/my_bookings.html', {'bookings': bookings, 'status_filter': status_filter})

@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    return render(request, 'transport/booking_detail.html', {'booking': booking})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    if booking.status in ('pending', 'confirmed'):
        booking.status = 'cancelled'
        booking.cancel_reason = request.POST.get('reason', 'Cancelled by customer')
        booking.save()
        Notification.objects.create(
            user=request.user, title='Booking Cancelled',
            message=f'Your booking for {booking.trip.origin} → {booking.trip.destination} has been cancelled.',
            notif_type='warning',
        )
        notify_admins(
            title='⚠️ Booking Cancelled',
            message=(
                f'{request.user.username} cancelled Booking #{booking.pk} '
                f'({booking.trip.origin} → {booking.trip.destination}).'
            ),
            notif_type='warning',
        )
        messages.success(request, 'Booking cancelled successfully.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    return redirect('my_bookings')

@login_required
def mark_notification_read(request, notif_id):
    notif = get_object_or_404(Notification, pk=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})


# ─── ADMIN BOOKING MANAGEMENT ────────────────────────────────────────────────

@login_required
def booking_list(request):
    bookings = Booking.objects.all().order_by('-booked_at')
    completed_qs = bookings.filter(status='completed')
    context = {
        'bookings': bookings,
        'total_commission':      completed_qs.aggregate(t=Sum('commission_fee'))['t'] or 0,
        'total_fare_collected':  completed_qs.aggregate(t=Sum('total_fare'))['t'] or 0,
        'total_driver_earnings': completed_qs.aggregate(t=Sum('driver_earnings'))['t'] or 0,
    }
    return render(request, 'transport/booking_list.html', context)

@login_required
def accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        booking.status = 'confirmed'
        booking.save()
        Passenger.objects.get_or_create(
            trip=booking.trip,
            name=booking.customer.get_full_name() or booking.customer.username,
            defaults={'mobile': ''}
        )
        Notification.objects.create(
            user=booking.customer, title='Booking Confirmed',
            message=(
                f'Your booking for {booking.trip.origin} → {booking.trip.destination} is confirmed! '
                f'Total Fare: ₱{booking.total_fare}.'
            ),
            notif_type='success',
        )
        notify_admins(
            title='✅ Booking Accepted',
            message=(
                f'Booking #{booking.pk} confirmed for {booking.customer.username}. '
                f'Fare: ₱{booking.total_fare} | Commission: ₱{booking.commission_fee} | '
                f'Driver Earnings: ₱{booking.driver_earnings}.'
            ),
            notif_type='success',
        )
        messages.success(request, f'Booking #{booking.pk} accepted!')
    return redirect('booking_list')

@login_required
def reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.cancel_reason = 'Rejected by admin'
        booking.save()
        Notification.objects.create(
            user=booking.customer, title='Booking Rejected',
            message=f'Your booking for {booking.trip.origin} → {booking.trip.destination} has been rejected.',
            notif_type='danger',
        )
        messages.error(request, f'Booking #{booking.pk} rejected.')
    return redirect('booking_list')

def search_vehicle(request):
    name = request.GET.get('name')
    try:
        vehicle = Vehicle.objects.get(name__iexact=name)
        return JsonResponse({'driver': vehicle.driver.name if vehicle.driver else '', 'plate_number': vehicle.plate_number})
    except Vehicle.DoesNotExist:
        return JsonResponse({'driver': '', 'plate_number': ''})


# ─── FUEL LOG CRUD ───────────────────────────────────────────────────────────

@login_required
def fuel_list(request):
    fuels = FuelLog.objects.all().order_by('-date')
    return render(request, 'transport/fuel_list.html', {
        'fuels': fuels,
        'total_cost': sum(f.total_cost for f in fuels),
        'total_liters': sum(f.liters for f in fuels),
    })

@login_required
def fuel_create(request):
    if request.method == 'POST':
        form = FuelLogForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fuel log added successfully!')
            return redirect('fuel_list')
    else:
        form = FuelLogForm()
    return render(request, 'transport/fuel_form.html', {'form': form})

@login_required
def fuel_update(request, pk):
    fuel = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        form = FuelLogForm(request.POST, instance=fuel)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fuel log updated successfully!')
            return redirect('fuel_list')
    else:
        form = FuelLogForm(instance=fuel)
    return render(request, 'transport/fuel_form.html', {'form': form})

@login_required
def fuel_delete(request, pk):
    fuel = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        fuel.delete()
        messages.success(request, 'Fuel log deleted successfully!')
        return redirect('fuel_list')
    return render(request, 'transport/fuel_confirm_delete.html', {'fuel': fuel})

@driver_required
def driver_tracking(request):
    return render(request, 'transport/driver_tracking.html')


# ─── DRIVER PANEL ────────────────────────────────────────────────────────────

@driver_required
def driver_dashboard(request):
    try:
        driver = Driver.objects.get(user=request.user)
        trips = Trip.objects.filter(driver=driver).order_by('-id')
        bookings = Booking.objects.filter(trip__in=trips).order_by('-booked_at')
        pending_bookings   = bookings.filter(status='pending')
        confirmed_bookings = bookings.filter(status='confirmed')
        driver_total_earnings = bookings.filter(status='completed').aggregate(
            t=Sum('driver_earnings')
        )['t'] or 0
        trips_pending_fare = trips.filter(status='pending')
        today = timezone.now().date()
        today_attendance, _ = Attendance.objects.get_or_create(driver=driver, date=today)
        attendance_history = Attendance.objects.filter(driver=driver).order_by('-date')[:10]

    except Driver.DoesNotExist:
        driver = None
        trips = []
        bookings = []
        pending_bookings = []
        confirmed_bookings = []
        driver_total_earnings = 0
        trips_pending_fare = []
        today_attendance = None
        attendance_history = []

    context = {
        'driver':                driver,
        'bookings':              bookings,
        'trips':                 trips,
        'pending_bookings':      pending_bookings,
        'confirmed_bookings':    confirmed_bookings,
        'total_trips':           Trip.objects.filter(driver=driver).count() if driver else 0,
        'driver_total_earnings': driver_total_earnings,
        'pending_trips':         [t for t in trips if t.status == 'pending'],
        'ongoing_trips':         [t for t in trips if t.status == 'ongoing'],
        'completed_trips':       [t for t in trips if t.status == 'completed'],
        'trips_pending_fare':    trips_pending_fare,
        'today_attendance': today_attendance,
        'attendance_history': attendance_history,
    }
    return render(request, 'driver_dashboard.html', context)


@driver_required
def driver_accept_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        booking.status = 'confirmed'
        booking.save()
        Passenger.objects.get_or_create(
            trip=booking.trip,
            name=booking.customer.get_full_name() or booking.customer.username,
            defaults={'mobile': ''}
        )
        Notification.objects.create(
            user=booking.customer, title='Booking Confirmed',
            message=(
                f'Your booking for {booking.trip.origin} → {booking.trip.destination} '
                f'has been confirmed by the driver! Total Fare: ₱{booking.total_fare}.'
            ),
            notif_type='success',
        )
        notify_admins(
            title='🚌 Driver Accepted Booking',
            message=(
                f'Driver confirmed Booking #{booking.pk} for {booking.customer.username}. '
                f'Fare: ₱{booking.total_fare} | Commission: ₱{booking.commission_fee} | '
                f'Driver Earnings: ₱{booking.driver_earnings}.'
            ),
            notif_type='success',
        )
        messages.success(request, 'Booking confirmed!')
    return redirect('driver_my_trips')


@driver_required
def driver_reject_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.cancel_reason = 'Rejected by driver'
        booking.save()
        Notification.objects.create(
            user=booking.customer, title='Booking Rejected',
            message=f'Your booking for {booking.trip.origin} → {booking.trip.destination} has been rejected by the driver.',
            notif_type='danger',
        )
        messages.error(request, 'Booking rejected.')
    return redirect('driver_my_trips')


# ─── DRIVER SUGGEST FARE ─────────────────────────────────────────────────────

@driver_required
def driver_suggest_fare(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        messages.error(request, 'Driver profile not found.')
        return redirect('driver_dashboard')

    if trip.driver != driver:
        messages.error(request, 'You are not assigned to this trip.')
        return redirect('driver_dashboard')

    if request.method == 'POST':
        suggested = request.POST.get('suggested_fare', '').strip()
        if not suggested:
            messages.error(request, 'Please enter a fare amount.')
            return render(request, 'transport/driver_suggest_fare.html', {'trip': trip})

        try:
            from decimal import Decimal
            suggested_decimal = Decimal(suggested)
            if suggested_decimal <= 0:
                raise ValueError
        except (ValueError, Exception):
            messages.error(request, 'Please enter a valid fare amount.')
            return render(request, 'transport/driver_suggest_fare.html', {'trip': trip})

        trip.suggested_fare = suggested_decimal
        trip.fare_approved  = False
        trip.save()

        notify_admins(
            title='💰 Driver Suggested Fare',
            message=(
                f'Driver {driver.name} suggested a fare of ₱{suggested_decimal} '
                f'for trip {trip.origin} → {trip.destination}. '
                f'Admin base fare: ₱{trip.fare_per_seat}. Please review and approve.'
            ),
            notif_type='info',
        )
        messages.success(request, f'Fare suggestion of ₱{suggested_decimal} submitted! Waiting for admin approval.')
        return redirect('driver_my_trips')

    return render(request, 'transport/driver_suggest_fare.html', {
        'trip': trip,
        'admin_fare': trip.fare_per_seat,
        'current_suggestion': trip.suggested_fare,
    })


# ─── ADMIN APPROVE / REJECT DRIVER FARE ──────────────────────────────────────

@login_required
def fare_approval_list(request):
    pending_fares = Trip.objects.filter(
        suggested_fare__isnull=False, fare_approved=False
    ).select_related('driver', 'vehicle').order_by('-id')
    return render(request, 'transport/fare_approval_list.html', {
        'pending_fares': pending_fares,
    })


@login_required
def approve_fare(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if request.method == 'POST':
        trip.fare_approved = True
        trip.save()
        if trip.driver and trip.driver.user:
            Notification.objects.create(
                user=trip.driver.user,
                title='✅ Fare Approved',
                message=(
                    f'Your suggested fare of ₱{trip.suggested_fare} for '
                    f'{trip.origin} → {trip.destination} has been approved!'
                ),
                notif_type='success',
            )
        messages.success(request, f'Fare of ₱{trip.suggested_fare} approved!')
    return redirect('fare_approval_list')


@login_required
def reject_fare(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id)
    if request.method == 'POST':
        trip.suggested_fare = None
        trip.fare_approved  = False
        trip.save()
        if trip.driver and trip.driver.user:
            Notification.objects.create(
                user=trip.driver.user,
                title='❌ Fare Rejected',
                message=(
                    f'Your suggested fare for {trip.origin} → {trip.destination} was rejected. '
                    f'Admin base fare of ₱{trip.fare_per_seat} will be used.'
                ),
                notif_type='danger',
            )
        messages.warning(request, 'Fare suggestion rejected. Admin base fare will be used.')
    return redirect('fare_approval_list')


# ─── DRIVER FUEL SYSTEM ──────────────────────────────────────────────────────

@driver_required
def driver_fuel_list(request):
    try:
        driver = Driver.objects.get(user=request.user)
        fuels = FuelLog.objects.filter(driver=driver)
    except Driver.DoesNotExist:
        fuels = []
    return render(request, 'transport/driver_fuel_list.html', {'fuels': fuels})

@driver_required
def driver_fuel_create(request):
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        messages.error(request, 'Driver profile not found.')
        return redirect('driver_dashboard')
    if request.method == 'POST':
        form = FuelLogForm(request.POST)
        if form.is_valid():
            fuel = form.save(commit=False)
            fuel.driver = driver
            fuel.submitted_by = request.user
            fuel.status = 'pending'
            fuel.save()
            for admin in User.objects.filter(is_staff=True):
                Notification.objects.create(
                    user=admin, title='⛽ Fuel Request Submitted',
                    message=f'Driver {driver.name} submitted a fuel request: {fuel.liters}L of {fuel.fuel_type} — Total: ₱{fuel.total_cost} on {fuel.date}.',
                    notif_type='info',
                )
            messages.success(request, f'Fuel request submitted! Total: ₱{fuel.total_cost}')
            return redirect('driver_fuel_list')
    else:
        form = FuelLogForm(initial={'driver': driver})
    return render(request, 'transport/driver_fuel_form.html', {'form': form, 'driver': driver})


# ─── ADMIN FUEL APPROVAL ─────────────────────────────────────────────────────

@login_required
def approve_fuel(request, pk):
    fuel = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        fuel.status = 'approved'
        fuel.save()
        if fuel.submitted_by:
            Notification.objects.create(
                user=fuel.submitted_by, title='✅ Fuel Request Approved',
                message=f'Your fuel request of {fuel.liters}L — ₱{fuel.total_cost} on {fuel.date} has been approved!',
                notif_type='success',
            )
        messages.success(request, 'Fuel request approved!')
    return redirect('fuel_list')

@login_required
def reject_fuel(request, pk):
    fuel = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        fuel.status = 'rejected'
        fuel.save()
        if fuel.submitted_by:
            Notification.objects.create(
                user=fuel.submitted_by, title='❌ Fuel Request Rejected',
                message=f'Your fuel request of {fuel.liters}L — ₱{fuel.total_cost} on {fuel.date} has been rejected.',
                notif_type='danger',
            )
        messages.error(request, 'Fuel request rejected.')
    return redirect('fuel_list')


# ─── NOTIFICATIONS JSON ──────────────────────────────────────────────────────

@login_required
def get_notifications_json(request):
    notifs = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    data = [{'id': n.pk, 'title': n.title, 'message': n.message, 'type': n.notif_type, 'time': n.created_at.strftime('%b %d, %I:%M %p')} for n in notifs]
    return JsonResponse({'count': len(data), 'notifications': data})

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)


# ─── DRIVER MY TRIPS ─────────────────────────────────────────────────────────

@driver_required
def driver_my_trips(request):
    try:
        driver = Driver.objects.get(user=request.user)
        trips = Trip.objects.filter(driver=driver).order_by('-id')
        all_bookings = Booking.objects.filter(
            trip__in=trips
        ).select_related('customer', 'trip').order_by('-booked_at')
        pending_bookings   = all_bookings.filter(status='pending')
        confirmed_bookings = all_bookings.filter(status='confirmed')
    except Driver.DoesNotExist:
        driver = None
        trips = []
        all_bookings = []
        pending_bookings = []
        confirmed_bookings = []

    context = {
        'driver':              driver,
        'trips':               trips,
        'all_bookings':        all_bookings,
        'pending_bookings':    pending_bookings,
        'confirmed_bookings':  confirmed_bookings,
        'pending_trips':       [t for t in trips if t.status == 'pending'],
        'ongoing_trips':       [t for t in trips if t.status == 'ongoing'],
        'completed_trips':     [t for t in trips if t.status == 'completed'],
    }
    return render(request, 'transport/driver_my_trips.html', context)


@driver_required
def start_trip(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        trip = booking.trip
        trip.status = 'ongoing'
        trip.save()
        messages.success(request, 'Trip nagsimula na!')
    return redirect('driver_dashboard')


@driver_required
def end_trip(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == 'POST':
        trip = booking.trip
        trip.status = 'completed'
        trip.save()

        booking.status = 'completed'
        booking.save()

        Notification.objects.create(
            user=booking.customer,
            title='Trip Completed',
            message=(
                f'Ang iyong trip mula {trip.origin} → {trip.destination} ay natapos na! '
                f'Total Fare: ₱{booking.total_fare}.'
            ),
            notif_type='success',
        )
        notify_admins(
            title='🏁 Trip Completed — Earnings Update',
            message=(
                f'Trip {trip.origin} → {trip.destination} (Booking #{booking.pk}) completed. '
                f'Total Fare: ₱{booking.total_fare} | '
                f'Admin Commission: ₱{booking.commission_fee} | '
                f'Driver Earnings: ₱{booking.driver_earnings}.'
            ),
            notif_type='success',
        )
        messages.success(request, 'Trip natapos na!')
    return redirect('driver_dashboard')


# ─── TRIP SCHEDULE (Van/Bus Recurring) ───────────────────────────────────────

@login_required
def schedule_list(request):
    schedules = TripSchedule.objects.all().order_by('time_slot')
    return render(request, 'transport/schedule_list.html', {'schedules': schedules})

@login_required
def schedule_create(request):
    if request.method == 'POST':
        TripSchedule.objects.create(
            origin=request.POST.get('origin'),
            destination=request.POST.get('destination'),
            vehicle=Vehicle.objects.get(pk=request.POST.get('vehicle')),
            driver=Driver.objects.get(pk=request.POST.get('driver')) if request.POST.get('driver') else None,
            time_slot=request.POST.get('time_slot'),
            fare_per_seat=request.POST.get('fare_per_seat') or 0,
            commission_rate=request.POST.get('commission_rate') or 10,
            is_active=request.POST.get('is_active') == 'on',
        )
        messages.success(request, 'Schedule added successfully!')
        return redirect('schedule_list')
    vehicles = Vehicle.objects.filter(type__in=['bus', 'van'], is_active=True)
    drivers = Driver.objects.filter(status='active')
    return render(request, 'transport/schedule_form.html', {
        'vehicles': vehicles,
        'drivers': drivers,
        'time_slots': TIME_SLOT_CHOICES,
    })

@login_required
def schedule_delete(request, pk):
    schedule = get_object_or_404(TripSchedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted!')
    return redirect('schedule_list')

@login_required
def generate_trips_today(request):
    from datetime import datetime, time
    today = timezone.now().date()
    schedules = TripSchedule.objects.filter(is_active=True)
    created = 0
    for s in schedules:
        hour, minute = map(int, s.time_slot.split(':'))
        departure = timezone.make_aware(datetime.combine(today, time(hour, minute)))
        already_exists = Trip.objects.filter(
            origin=s.origin,
            destination=s.destination,
            vehicle=s.vehicle,
            departure_time=departure,
        ).exists()
        if not already_exists:
            Trip.objects.create(
                origin=s.origin,
                destination=s.destination,
                vehicle=s.vehicle,
                driver=s.driver,
                departure_time=departure,
                fare_per_seat=s.fare_per_seat,
                commission_rate=s.commission_rate,
                status='pending',
            )
            created += 1
    messages.success(request, f'{created} trip(s) generated for today!')
    return redirect('schedule_list')

@driver_required
def driver_attendance(request):
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        messages.error(request, 'Driver profile not found.')
        return redirect('driver_dashboard')

    today = timezone.now().date()
    attendance, created = Attendance.objects.get_or_create(driver=driver, date=today)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'time_in' and not attendance.time_in:
            attendance.time_in = timezone.now()
            attendance.save()
            messages.success(request, 'Time In recorded!')
        elif action == 'time_out' and attendance.time_in and not attendance.time_out:
            attendance.time_out = timezone.now()
            attendance.save()
            messages.success(request, 'Time Out recorded!')
        return redirect('driver_dashboard')

    return redirect('driver_dashboard')
@login_required
def admin_attendance_list(request):
    from .models import Attendance
    date_filter = request.GET.get('date', '')
    driver_filter = request.GET.get('driver', '')

    attendance_qs = Attendance.objects.select_related('driver').order_by('-date', 'driver__name')

    if date_filter:
        attendance_qs = attendance_qs.filter(date=date_filter)
    if driver_filter:
        attendance_qs = attendance_qs.filter(driver__id=driver_filter)

    drivers = Driver.objects.filter(status='active')

    context = {
        'attendances': attendance_qs,
        'drivers': drivers,
        'date_filter': date_filter,
        'driver_filter': driver_filter,
    }
    return render(request, 'transport/admin_attendance.html', context)
