CarePoint - Medical Appointment Scheduling System

1. Ensure MySQL Server is running.
2. Set the optional MySQL environment variables if your local credentials differ:
   - MEDICAL_DB_HOST (default: localhost)
   - MEDICAL_DB_PORT (default: 3307)
   - MEDICAL_DB_USER (default: root)
   - MEDICAL_DB_PASSWORD (default: empty)
   - MEDICAL_DB_NAME (default: medical_appointment_db)
3. Install dependency: python -m pip install -r requirements.txt
4. Run: python app.py

The application creates the database and tables on startup, if the configured MySQL
account has permission to create databases.
The schema contains exactly six tables: patients, doctors, appointments, departments,
payments and doctor_availability.
On first connection, the application also seeds an idempotent demonstration dataset:
at least 5 departments, 50 patients, 15 doctors, 30 availability rows, 15 appointments
and 15 payments. Existing records are preserved and repeated startups do not duplicate
the demo rows.
Dashboard summary cards intentionally show only these demo records (50 patients,
15 doctors and 15 appointments); the full existing database records remain available
in the table views.

CSV import:
- Patients headers: full_name,age,gender,phone,email,address
- Doctors headers: department_id,full_name,specialization,phone,email,available_days,consultation_fee
- Appointments headers: patient_id,doctor_id,appointment_date,appointment_time,reason,status
- Departments headers: name,description,phone
- Payments headers: appointment_id,amount,payment_method,payment_date,payment_status
- Doctor availability headers: doctor_id,available_date,start_time,end_time,slot_status

Import departments before doctors when assigning a department. Import patients, doctors and
doctor availability before appointments. Patient IDs and doctor IDs must already exist;
appointment IDs are generated automatically. Appointment bookings must fit an Available
doctor availability slot and duplicate doctor/date/time bookings are rejected.

The six sample CSV files are in the project folder. Import them in this order:
departments, patients, doctors, doctor_availability, appointments, payments. The sample
base rows reuse existing database IDs; the
importer skips matching departments, patients and doctors instead of creating duplicates.
Appointments generate their own IDs, so confirm those IDs before importing payments if
the sample is used in a different database.
