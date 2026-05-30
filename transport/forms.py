from django import forms
from .models import Vehicle, Driver, Trip, Passenger, Maintenance, PartsInventory, Booking


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'type', 'plate_number', 'capacity', 'status', 'is_active', 'description']


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'mobile', 'age', 'license_no', 'license_expiry',
                  'experience', 'date_of_joining', 'reference', 'address', 'status', 'photo']
        widgets = {
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'origin', 'destination', 'vehicle', 'driver',
            'departure_time', 'arrival_time', 'status',
            'fare_per_seat', 'commission_rate',
            'distance_km', 'rate_per_km',
        ]
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'arrival_time':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'fare_per_seat':   'Base Fare per Seat (₱)',
            'commission_rate': 'Commission Rate (%)',
            'distance_km':     'Distance (km)',
            'rate_per_km':     'Rate per Kilometer (₱)',
        }
        help_texts = {
            'distance_km': 'Ilagay ang distansya para auto-compute ang fare.',
            'rate_per_km': 'Kung may rate per km, ito ang gagamitin bilang fare.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ── Show ALL active vehicles (Bus, Van, Motor, Car) ──────────────────
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True)
        self.fields['vehicle'].label_from_instance = lambda obj: f"{obj.get_type_display()} — {obj.name} ({obj.plate_number})"

        # ── Make origin & destination optional at form level ─────────────────
        # Motor/Car trips use 'TBD' injected by JS; Bus/Van admin fills them in.
        self.fields['origin'].required = False
        self.fields['destination'].required = False
        self.fields['departure_time'].required = False
        self.fields['distance_km'].required = False

    def clean(self):
        cleaned_data = super().clean()
        vehicle = cleaned_data.get('vehicle')
        origin = cleaned_data.get('origin', '').strip()
        destination = cleaned_data.get('destination', '').strip()

        if vehicle:
         vtype = vehicle.type
         is_bus_or_van = vtype in ('bus', 'van')

        if is_bus_or_van:
            if not origin:
                self.add_error('origin', 'Origin is required for Bus/Van trips.')
            if not destination:
                self.add_error('destination', 'Destination is required for Bus/Van trips.')
        else:
            # Force set TBD directly in cleaned_data
            cleaned_data['origin'] = origin if origin else 'TBD'
            cleaned_data['destination'] = destination if destination else 'TBD'
    
        return cleaned_data


class PassengerForm(forms.ModelForm):
    class Meta:
        model = Passenger
        fields = ['name', 'mobile']


class MaintenanceForm(forms.ModelForm):
    class Meta:
        model = Maintenance
        fields = ['vehicle', 'start_date', 'end_date', 'service_info', 'vendor', 'cost', 'status']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'service_info': forms.Textarea(attrs={'rows': 3}),
        }


class PartsInventoryForm(forms.ModelForm):
    class Meta:
        model = PartsInventory
        fields = ['name', 'description', 'stock', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class CustomerBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['seats']
        widgets = {
            'seats': forms.NumberInput(attrs={
                'min': 1,
                'max': 50,
                'class': 'form-control form-control-lg',
            }),
        }
        labels = {
            'seats': 'Number of Seats',
        }


from .models import FuelLog

class FuelLogForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['vehicle', 'driver', 'fuel_type', 'liters', 'price_per_liter', 'odometer', 'date', 'station', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }