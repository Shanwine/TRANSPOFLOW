from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Vehicle, Driver, Trip, Passenger, DriverLocation,
    Maintenance, PartsInventory, Booking, Notification, FuelLog
)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'plate_number', 'type', 'capacity', 'status', 'is_active']
    search_fields = ['name', 'plate_number']
    list_filter = ['is_active', 'status', 'type']


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'license_no', 'status', 'subscription_badge', 'subscription_expiry']
    search_fields = ['name', 'license_no']
    list_filter = ['status', 'is_subscribed']
    readonly_fields = ['subscription_badge']

    # Show subscription fields in the form
    fieldsets = (
        ('Personal Info', {
            'fields': ('user', 'name', 'mobile', 'age', 'address', 'photo')
        }),
        ('License & Experience', {
            'fields': ('license_no', 'license_expiry', 'experience', 'date_of_joining', 'reference')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Subscription', {
            'fields': ('is_subscribed', 'subscription_expiry', 'subscription_badge'),
            'description': 'Manage driver subscription status and expiry date.',
        }),
    )

    def subscription_badge(self, obj):
        if obj.subscription_active:
            return format_html('<span style="color:green;font-weight:bold;">✅ Active</span>')
        elif obj.is_subscribed:
            return format_html('<span style="color:red;font-weight:bold;">❌ Expired</span>')
        return format_html('<span style="color:gray;">— None</span>')
    subscription_badge.short_description = 'Subscription Status'


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['origin', 'destination', 'vehicle', 'driver', 'departure_time', 'status']
    search_fields = ['origin', 'destination']
    list_filter = ['status']


@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile', 'trip']
    search_fields = ['name']


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ['driver', 'latitude', 'longitude', 'updated_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'trip', 'seats', 'commission_fee', 'status', 'booked_at']
    search_fields = ['customer__username', 'trip__origin', 'trip__destination']
    list_filter = ['status']
    readonly_fields = ['booked_at']

    # Quick actions to accept/reject directly from admin
    actions = ['mark_confirmed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        # Notify each affected customer
        for booking in queryset.filter(status='confirmed'):
            Notification.objects.create(
                user=booking.customer,
                title='Booking Confirmed',
                message=f'Your booking for {booking.trip.origin} → {booking.trip.destination} has been confirmed!',
                notif_type='success',
            )
        self.message_user(request, f'{updated} booking(s) confirmed.')
    mark_confirmed.short_description = '✅ Mark selected as Confirmed'

    def mark_cancelled(self, request, queryset):
        updated = queryset.exclude(status='completed').update(status='cancelled')
        self.message_user(request, f'{updated} booking(s) cancelled.')
    mark_cancelled.short_description = '❌ Mark selected as Cancelled'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notif_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title']
    list_filter = ['notif_type', 'is_read']
    readonly_fields = ['created_at']

    actions = ['mark_all_read']

    def mark_all_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, 'Selected notifications marked as read.')
    mark_all_read.short_description = '📖 Mark selected as Read'


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'start_date', 'end_date', 'vendor', 'cost', 'status']
    list_filter = ['status']
    search_fields = ['vehicle__name', 'vendor']


@admin.register(PartsInventory)
class PartsInventoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'stock', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name']


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'driver', 'fuel_type', 'liters', 'price_per_liter', 'total_cost', 'date']
    list_filter = ['fuel_type']
    search_fields = ['vehicle__name', 'driver__name', 'station']
    readonly_fields = ['total_cost', 'created_at']