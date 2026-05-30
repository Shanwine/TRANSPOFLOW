from django.urls import path
from . import views

urlpatterns = [
    # ── Admin / Staff ──────────────────────────────────────────────────────
    path('', views.dashboard, name='dashboard'),
    path('vehicles/', views.vehicle_list, name='vehicle_list'),
    path('vehicles/create/', views.vehicle_create, name='vehicle_create'),
    path('vehicles/<int:pk>/update/', views.vehicle_update, name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/create/', views.driver_create, name='driver_create'),
    path('drivers/<int:pk>/update/', views.driver_update, name='driver_update'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),
    path('trips/', views.trip_list, name='trip_list'),
    path('trips/create/', views.trip_create, name='trip_create'),
    path('trips/<int:pk>/update/', views.trip_update, name='trip_update'),
    path('trips/<int:pk>/delete/', views.trip_delete, name='trip_delete'),
    path('trips/<int:trip_id>/passengers/', views.passenger_list, name='passenger_list'),
    path('trips/<int:trip_id>/passengers/create/', views.passenger_create, name='passenger_create'),
    path('passengers/<int:pk>/update/', views.passenger_update, name='passenger_update'),
    path('passengers/<int:pk>/delete/', views.passenger_delete, name='passenger_delete'),
    path('reports/', views.reports, name='reports'),
    path('driver-location/', views.get_driver_location, name='driver_location'),
    path('update-location/', views.update_driver_location, name='update_location'),
    path('map/', views.map_view, name='map_view'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/create/', views.maintenance_create, name='maintenance_create'),
    path('maintenance/<int:pk>/update/', views.maintenance_update, name='maintenance_update'),
    path('maintenance/<int:pk>/delete/', views.maintenance_delete, name='maintenance_delete'),
    path('parts/', views.parts_list, name='parts_list'),
    path('parts/create/', views.parts_create, name='parts_create'),
    path('parts/<int:pk>/update/', views.parts_update, name='parts_update'),
    path('parts/<int:pk>/delete/', views.parts_delete, name='parts_delete'),

    # ── Customer Panel ─────────────────────────────────────────────────────
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/vehicles/', views.customer_vehicle_list, name='customer_vehicles'),
    path('customer/trips/', views.available_trips, name='available_trips'),
    path('customer/book/<int:trip_id>/', views.book_trip, name='book_trip'),
    path('customer/my-bookings/', views.my_bookings, name='my_bookings'),
    path('customer/booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('customer/booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('customer/notification/<int:notif_id>/read/', views.mark_notification_read, name='mark_notif_read'),

    # ── Admin Booking Management ───────────────────────────────────────────
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/<int:booking_id>/accept/', views.accept_booking, name='accept_booking'),
    path('bookings/<int:booking_id>/reject/', views.reject_booking, name='reject_booking'),

    path('search-vehicle/', views.search_vehicle, name='search_vehicle'),

    # ── Fuel ───────────────────────────────────────────────────────────────
    path('fuel/', views.fuel_list, name='fuel_list'),
    path('fuel/create/', views.fuel_create, name='fuel_create'),
    path('fuel/<int:pk>/update/', views.fuel_update, name='fuel_update'),
    path('fuel/<int:pk>/delete/', views.fuel_delete, name='fuel_delete'),
    path('fuel/<int:pk>/approve/', views.approve_fuel, name='approve_fuel'),
    path('fuel/<int:pk>/reject/', views.reject_fuel, name='reject_fuel'),

    # ── Driver Panel ───────────────────────────────────────────────────────
    path('driver/', views.driver_dashboard, name='driver_dashboard'),
    path('driver/share-location/', views.driver_tracking, name='driver_tracking'),  # ← INILIPAT DITO
    path('driver/accept/<int:booking_id>/', views.driver_accept_booking, name='driver_accept_booking'),
    path('driver/reject/<int:booking_id>/', views.driver_reject_booking, name='driver_reject_booking'),
    path('driver/fuel/', views.driver_fuel_list, name='driver_fuel_list'),
    path('driver/fuel/add/', views.driver_fuel_create, name='driver_fuel_create'),
    path('driver/my-trips/', views.driver_my_trips, name='driver_my_trips'),
    path('driver/start-trip/<int:booking_id>/', views.start_trip, name='start_trip'),
    path('driver/end-trip/<int:booking_id>/', views.end_trip, name='end_trip'),
    path('get-driver-location/', views.get_driver_location, name='get_driver_location'),
    path('update-driver-location/', views.update_driver_location, name='update_driver_location'),
    path('schedules/', views.schedule_list, name='schedule_list'),
path('schedules/add/', views.schedule_create, name='schedule_create'),
path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
path('schedules/generate/', views.generate_trips_today, name='generate_trips_today'),
path('driver/attendance/', views.driver_attendance, name='driver_attendance'),
path('attendance/', views.admin_attendance_list, name='admin_attendance_list'),
]