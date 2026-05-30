# TranspoFlow – Smart Transportation Management System

A beginner-friendly full-stack web application built with Django for managing transportation operations efficiently.

## Features

- **User Authentication**: Register, Login, Logout with role-based access (Admin and Driver)
- **Dashboard**: Overview of total vehicles, trips, and drivers with statistics
- **Vehicle Management**: CRUD operations for vehicles (type, plate number, status)
- **Driver Management**: CRUD operations for drivers with user linking
- **Trip Scheduling**: Create and manage trips with vehicle and driver assignments
- **Passenger Records**: Add and manage passengers per trip
- **Reports**: Simple reports for trips and vehicles

## Technology Stack

- **Backend**: Django (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap
- **Authentication**: Django's built-in auth with groups for roles

## Installation

1. Clone or download the project.
2. Navigate to the project directory.
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install django`
6. Run migrations: `python manage.py migrate`
7. Create groups: Run in shell `python manage.py shell` then `from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Admin'); Group.objects.get_or_create(name='Driver')`
8. Run the server: `python manage.py runserver`

## Usage

1. Register a new user and select role (Admin or Driver).
2. Login with your credentials.
3. Admins can manage all data; Drivers can view assigned trips and manage passengers.
4. Use the dashboard to see statistics.
5. Navigate through the menus to perform CRUD operations.

## Project Structure

```
transflow/
├── accounts/          # Authentication app
├── transport/         # Main app for transport management
├── templates/         # HTML templates
├── static/            # Static files (CSS, JS)
├── transflow/         # Project settings
├── manage.py          # Django management script
└── db.sqlite3         # Database file
```

## Models

- **Vehicle**: type, plate_number, status
- **Driver**: user (FK), name, license_number, contact
- **Trip**: vehicle (FK), driver (FK), route, date, time, status
- **Passenger**: trip (FK), name, contact

## Contributing

This is a beginner-friendly project. Feel free to enhance with more features like real-time updates, advanced reports, or mobile app integration.

## License

Open source - use freely for learning and development.