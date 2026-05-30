from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]
    TYPE_CHOICES = [
        ('bus', 'Bus'),
        ('truck', 'Motor'),
        ('van', 'Van'),
        ('car', 'Car'),
    ]
    name = models.CharField(max_length=100, default='')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='bus')
    plate_number = models.CharField(max_length=20, unique=True)
    capacity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='pending')
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Driver(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_trip', 'On Trip'),
    ]
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    age = models.IntegerField(default=0)
    license_no = models.CharField(max_length=50)
    license_expiry = models.DateField(null=True, blank=True)
    experience = models.CharField(max_length=50, default='')
    date_of_joining = models.DateField(null=True, blank=True)
    reference = models.TextField(blank=True, default='')
    address = models.TextField(default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    photo = models.ImageField(upload_to='drivers/', blank=True, null=True)

    # ── Subscription ─────────────────────────────────────────────────────────
    is_subscribed = models.BooleanField(default=False)
    subscription_expiry = models.DateField(null=True, blank=True)

    # ── Earnings ─────────────────────────────────────────────────────────────
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0,
        help_text="Cumulative net earnings of the driver (after commission).")

    def __str__(self):
        return self.name

    @property
    def subscription_active(self):
        if not self.is_subscribed:
            return False
        if self.subscription_expiry and self.subscription_expiry < timezone.now().date():
            return False
        return True


class Trip(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    origin = models.CharField(max_length=100, blank=True, default='TBD')
    destination = models.CharField(max_length=100, blank=True, default='TBD')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)
    departure_time = models.DateTimeField(null=True, blank=True)
    arrival_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # ── Distance-based Fare ───────────────────────────────────────────────────
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Distance ng trip sa kilometers."
    )
    rate_per_km = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Presyo per kilometer (set by admin)."
    )

    # ── Fare & Commission set by Admin ────────────────────────────────────────
    fare_per_seat = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Base fare per seat set by admin.")
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        validators=[MinValueValidator(10), MaxValueValidator(30)],
        help_text="Admin commission rate (10% - 30%)."
    )

    # ── Driver can suggest/adjust fare ───────────────────────────────────────
    suggested_fare = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Fare suggested by driver. If set, this overrides admin's base fare."
    )
    fare_approved = models.BooleanField(
        default=False,
        help_text="Set to True by admin to approve driver's suggested fare."
    )

    def __str__(self):
        return f"{self.origin} → {self.destination}"

    @property
    def effective_fare(self):
        """
        Priority:
        1. Driver's approved suggested fare
        2. Distance-based fare (rate_per_km x distance_km)
        3. Admin's base fare_per_seat
        """
        if self.suggested_fare and self.fare_approved:
            return self.suggested_fare
        if self.rate_per_km and self.distance_km:
            return round(self.rate_per_km * self.distance_km, 2)
        return self.fare_per_seat

    def commission_amount(self, seats=1):
        """Compute commission fee based on effective fare and rate."""
        return round(self.effective_fare * seats * self.commission_rate / 100, 2)

    def driver_earning(self, seats=1):
        """Compute driver net earning after commission."""
        total = self.effective_fare * seats
        return round(total - self.commission_amount(seats), 2)


class Passenger(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.name


class DriverLocation(models.Model):
    driver = models.OneToOneField(User, on_delete=models.CASCADE)
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.driver.username} location"


class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('inprogress', 'InProgress'),
        ('completed', 'Completed'),
    ]
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    service_info = models.TextField()
    vendor = models.CharField(max_length=100, blank=True, default='')
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')

    def __str__(self):
        return f"{self.vehicle} - {self.service_info}"


class PartsInventory(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    stock = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ── Payment Method Choices ────────────────────────────────────────────────────
PAYMENT_METHOD_CHOICES = [
    ('cash', 'Cash'),
    ('gcash', 'GCash'),
    ('maya', 'Maya (PayMaya)'),
    ('credit_card', 'Credit / Debit Card'),
]


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    seats = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cancel_reason = models.TextField(blank=True, default='')

    # ── Payment ───────────────────────────────────────────────────────────────
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        null=True,
        blank=True,
        help_text="Payment method chosen by the customer."
    )
    mobile_number = models.CharField(
        max_length=11, null=True, blank=True,
        help_text="GCash or Maya mobile number."
    )
    card_last4 = models.CharField(
        max_length=4, null=True, blank=True,
        help_text="Last 4 digits of credit/debit card."
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        help_text="Automatically set to paid when booking is completed."
    )
    cash_received_by = models.CharField(
        max_length=50,
        null=True, blank=True,
        help_text="Sino ang nakatanggap ng cash payment (e.g., Driver, Conductor)."
    )

    booked_at = models.DateTimeField(auto_now_add=True)

    # ── Customer Pickup Location ──────────────────────────────────────────
    pickup_location = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Address ng pickup location ng customer."
    )
    pickup_latitude = models.FloatField(
        null=True, blank=True,
        help_text="GPS latitude ng customer."
    )
    pickup_longitude = models.FloatField(
        null=True, blank=True,
        help_text="GPS longitude ng customer."
    )


    # ── Income breakdown (auto-computed on save) ──────────────────────────────
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Total fare paid by passenger (effective_fare × seats).")
    commission_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Admin commission deducted from total fare.")
    driver_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0,
        help_text="Net amount earned by driver after commission.")

    def save(self, *args, **kwargs):
        # Auto-compute fare breakdown
        if self.trip_id and self.seats:
            self.total_fare      = self.trip.effective_fare * self.seats
            self.commission_fee  = self.trip.commission_amount(self.seats)
            self.driver_earnings = self.trip.driver_earning(self.seats)

        # Cash payments: auto-mark as paid when confirmed or completed
        if self.payment_method == 'cash' and self.status in ('confirmed', 'completed'):
            self.payment_status = 'paid'

        # Non-cash: mark paid when completed
        if self.status == 'completed':
            self.payment_status = 'paid'

        # Update Driver.total_earnings only ONCE when status changes to completed
        old = Booking.objects.filter(pk=self.pk).first()
        if self.status == 'completed' and (old is None or old.status != 'completed'):
            driver = self.trip.driver
            if driver:
                from decimal import Decimal
                driver.total_earnings = (driver.total_earnings or Decimal('0')) + self.driver_earnings
                driver.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.username} - {self.trip}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.title}"


class FuelLog(models.Model):
    FUEL_TYPE_CHOICES = [
        ('diesel', 'Diesel'),
        ('gasoline', 'Gasoline'),
        ('lpg', 'LPG'),
    ]
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES, default='diesel')
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_liter = models.DecimalField(max_digits=8, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    odometer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField(default=timezone.now)
    station = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.liters * self.price_per_liter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle} - {self.liters}L on {self.date}"

    class Meta:
        ordering = ['-date']
        # ── Trip Schedule (Van/Bus Recurring) ────────────────────────────────────────

TIME_SLOT_CHOICES = [
    ('06:00', '6:00 AM'),
    ('10:00', '10:00 AM'),
    ('13:00', '1:00 PM'),
    ('16:00', '4:00 PM'),
    ('18:00', '6:00 PM'),
    ('22:00', '10:00 PM'),
]

class TripSchedule(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    time_slot = models.CharField(max_length=5, choices=TIME_SLOT_CHOICES)
    fare_per_seat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        validators=[MinValueValidator(10), MaxValueValidator(30)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.origin} → {self.destination} @ {self.get_time_slot_display()}"

    class Meta:
        ordering = ['time_slot']
class Attendance(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.driver.name} - {self.date}"

    @property
    def duration(self):
        if self.time_in and self.time_out:
            diff = self.time_out - self.time_in
            hours, rem = divmod(diff.seconds, 3600)
            minutes = rem // 60
            return f"{hours}h {minutes}m"
        return "—"