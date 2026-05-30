from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # ✅ Unified Login (isa lang para sa lahat)
    path('login/', views.unified_login, name='unified_login'),

    # ✅ Old URLs — i-redirect sa unified login (para walang 404)
    path('admin-login/', RedirectView.as_view(url='/accounts/login/?role=admin'),  name='admin_login'),
    path('driver-login/', RedirectView.as_view(url='/accounts/login/?role=driver'), name='driver_login'),
    path('passenger-login/', RedirectView.as_view(url='/accounts/login/?role=passenger'), name='passenger_login'),

    # ✅ Register, Logout, Profile
    path('register/', views.passenger_register, name='passenger_register'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.customer_profile, name='customer_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]