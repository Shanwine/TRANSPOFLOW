from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import PassengerRegisterForm, ProfileUpdateForm
from .models import Profile
from functools import wraps


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login as admin.')
            return redirect('unified_login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Access denied. Admins only.')
            return redirect('unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def passenger_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login as passenger.')
            return redirect('unified_login')
        if request.user.is_staff or request.user.is_superuser:
            messages.error(request, 'Access denied. Passengers only.')
            return redirect('unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def driver_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login as driver.')
            return redirect('unified_login')
        if not request.user.groups.filter(name='Driver').exists():
            messages.error(request, 'Access denied. Drivers only.')
            return redirect('unified_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def unified_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard')
        elif request.user.groups.filter(name='Driver').exists():
            return redirect('driver_dashboard')
        else:
            return redirect('customer_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Auto-detect role
            if user.is_staff or user.is_superuser:
                messages.success(request, f'Welcome Admin {user.username}!')
                return redirect('dashboard')
            elif user.groups.filter(name='Driver').exists():
                messages.success(request, f'Welcome Driver {user.username}!')
                return redirect('driver_dashboard')
            else:
                messages.success(request, f'Welcome {user.username}!')
                return redirect('customer_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/unified_login.html')


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('unified_login')


def passenger_register(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')
    if request.method == 'POST':
        form = PassengerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created! Please login.')
            return redirect('unified_login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PassengerRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def customer_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('customer_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form, 'profile': profile})