# CarePoint Medical Appointment Scheduling System

A desktop medical appointment scheduling application built with Python, Tkinter,
and MySQL. CarePoint helps manage patients, doctors, departments, availability,
appointments, and payments from one interface.

## Features

- Patient, doctor, department, appointment, and payment management
- Doctor availability and appointment-slot validation
- Duplicate booking protection for the same doctor, date, and time
- MySQL database and table creation on startup
- Idempotent demonstration data seeding
- CSV import support for all six database tables
- Dashboard summary cards and table views

## Requirements

- Python 3.9 or newer
- MySQL Server
- A MySQL account with permission to create the application database and tables

## Installation

```powershell
python -m pip install -r requirements.txt
```

Configure the database with environment variables when the defaults do not match
your local MySQL installation:

| Variable | Default | Description |
| --- | --- | --- |
| `MEDICAL_DB_HOST` | `localhost` | MySQL host |
| `MEDICAL_DB_PORT` | `3307` | MySQL port |
| `MEDICAL_DB_USER` | `root` | MySQL username |
| `MEDICAL_DB_PASSWORD` | empty | MySQL password |
| `MEDICAL_DB_NAME` | `medical_appointment_db` | Application database |

Example for the current PowerShell session:

```powershell
$env:MEDICAL_DB_PASSWORD = "your-local-password"
```

Run the application:

```powershell
python app.py
```

The application creates the database and six tables when the configured MySQL
account has the required permissions.

## Demonstration data

On the first connection, the application seeds an idempotent demonstration
dataset containing at least:

- 5 departments
- 50 patients
- 15 doctors
- 30 availability rows
- 15 appointments
- 15 payments

Existing records are preserved, and restarting the application does not duplicate
the demonstration rows.

## CSV import

The sample CSV files are included in the project folder. Import them in this order:

1. `departments.csv`
2. `patients.csv`
3. `doctors.csv`
4. `doctor_availability.csv`
5. `appointments.csv`
6. `payments.csv`

Patients, doctors, and doctor availability must be imported before appointments.
Patient and doctor IDs must already exist. Appointment IDs are generated
automatically, so confirm those IDs before importing payments into a different
database.

## Security and privacy

- Database credentials are read from environment variables and are not stored in
  the source code.
- Do not commit `.env` files, passwords, API keys, or production patient data.
- The included CSV files are demonstration data. Review and anonymize them before
  publishing a public repository if they contain real personal information.
- Use a private GitHub repository for any real patient or production data.

## Project structure

```text
app.py                    Main application
config.py                 Environment-based database configuration
requirements.txt          Python dependency list
*.csv                     Sample data and import files
```
