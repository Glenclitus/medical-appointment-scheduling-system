import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

BG = "#F3F6FB"
NAVY = "#14213D"
BLUE = "#2563EB"
TEAL = "#0F766E"
WHITE = "#FFFFFF"
TEXT = "#172033"
MUTED = "#64748B"

TABLES = {
    "Patients": {
        "table": "patients",
        "columns": ["patient_id", "full_name", "age", "gender", "phone", "email", "address"],
        "editable": ["full_name", "age", "gender", "phone", "email", "address"],
        "labels": ["ID", "Full name", "Age", "Gender", "Phone", "Email", "Address"],
        "required": ["full_name"],
        "widths": [55, 150, 55, 80, 105, 170, 170],
        "csv": ["full_name", "age", "gender", "phone", "email", "address"],
    },
    "Doctors": {
        "table": "doctors",
        "columns": ["doctor_id", "department_id", "full_name", "specialization", "phone", "email", "available_days", "consultation_fee"],
        "editable": ["department_id", "full_name", "specialization", "phone", "email", "available_days", "consultation_fee"],
        "labels": ["ID", "Department ID", "Doctor name", "Specialization", "Phone", "Email", "Available days", "Fee"],
        "required": ["full_name", "specialization"],
        "widths": [55, 85, 145, 130, 105, 165, 140, 75],
        "csv": ["department_id", "full_name", "specialization", "phone", "email", "available_days", "consultation_fee"],
    },
    "Appointments": {
        "table": "appointments",
        "columns": ["appointment_id", "patient_id", "doctor_id", "appointment_date", "appointment_time", "reason", "status"],
        "editable": ["patient_id", "doctor_id", "appointment_date", "appointment_time", "reason", "status"],
        "labels": ["ID", "Patient ID", "Doctor ID", "Date (YYYY-MM-DD)", "Time (HH:MM)", "Reason", "Status"],
        "required": ["patient_id", "doctor_id", "appointment_date", "appointment_time"],
        "widths": [55, 75, 75, 125, 100, 200, 105],
        "csv": ["patient_id", "doctor_id", "appointment_date", "appointment_time", "reason", "status"],
    },
    "Departments": {
        "table": "departments",
        "columns": ["department_id", "name", "description", "phone"],
        "editable": ["name", "description", "phone"],
        "labels": ["ID", "Name", "Description", "Phone"],
        "required": ["name"],
        "widths": [55, 160, 280, 130],
        "csv": ["name", "description", "phone"],
    },
    "Payments": {
        "table": "payments",
        "columns": ["payment_id", "appointment_id", "amount", "payment_method", "payment_date", "payment_status"],
        "editable": ["appointment_id", "amount", "payment_method", "payment_date", "payment_status"],
        "labels": ["ID", "Appointment ID", "Amount", "Method", "Date", "Status"],
        "required": ["appointment_id", "amount", "payment_method", "payment_date"],
        "widths": [55, 100, 90, 120, 110, 110],
        "csv": ["appointment_id", "amount", "payment_method", "payment_date", "payment_status"],
    },
    "Doctor Availability": {
        "table": "doctor_availability",
        "columns": ["availability_id", "doctor_id", "available_date", "start_time", "end_time", "slot_status"],
        "editable": ["doctor_id", "available_date", "start_time", "end_time", "slot_status"],
        "labels": ["ID", "Doctor ID", "Date", "Start", "End", "Status"],
        "required": ["doctor_id", "available_date", "start_time", "end_time"],
        "widths": [55, 85, 110, 90, 90, 115],
        "csv": ["doctor_id", "available_date", "start_time", "end_time", "slot_status"],
    }
}


class Database:
    def __init__(self):
        self.conn = None

    def connect(self):
        """Connect to MySQL and create the project schema/tables if needed."""
        if self.conn is not None:
            try:
                if self.conn.is_connected():
                    return self.conn
            except Error:
                pass
            self.conn = None

        server = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            connection_timeout=5
        )
        try:
            cur = server.cursor()
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            cur.close()
        finally:
            server.close()

        self.conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, connection_timeout=5
        )
        self.ensure_tables()
        self.seed_demo_data()
        return self.conn

    def ensure_connection(self):
        if self.conn is None:
            return self.connect()
        try:
            if not self.conn.is_connected():
                self.conn = None
                return self.connect()
        except Error:
            self.conn = None
            return self.connect()
        return self.conn

    def ensure_tables(self):
        self.ensure_connection_without_tables()
        cur = self.conn.cursor()
        try:
            cur.execute("""CREATE TABLE IF NOT EXISTS departments (
                department_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                description VARCHAR(255),
                phone VARCHAR(20)
            ) ENGINE=InnoDB""")
            cur.execute("""CREATE TABLE IF NOT EXISTS patients (
                patient_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                age INT,
                gender VARCHAR(20),
                phone VARCHAR(20),
                email VARCHAR(120),
                address VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""")
            cur.execute("""CREATE TABLE IF NOT EXISTS doctors (
                doctor_id INT AUTO_INCREMENT PRIMARY KEY,
                department_id INT NULL,
                full_name VARCHAR(100) NOT NULL,
                specialization VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                email VARCHAR(120),
                available_days VARCHAR(100),
                consultation_fee DECIMAL(10,2) DEFAULT 0.00
            ) ENGINE=InnoDB""")
            cur.execute("""CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id INT NOT NULL,
                doctor_id INT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                reason VARCHAR(255),
                status ENUM('Scheduled','Completed','Cancelled') DEFAULT 'Scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_appointment_patient FOREIGN KEY (patient_id)
                    REFERENCES patients(patient_id) ON UPDATE CASCADE ON DELETE RESTRICT,
                CONSTRAINT fk_appointment_doctor FOREIGN KEY (doctor_id)
                    REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE RESTRICT,
                UNIQUE KEY unique_doctor_slot (doctor_id, appointment_date, appointment_time)
            ) ENGINE=InnoDB""")
            cur.execute("""CREATE TABLE IF NOT EXISTS payments (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                appointment_id INT NOT NULL UNIQUE,
                amount DECIMAL(10,2) NOT NULL,
                payment_method ENUM('Cash','Card','Insurance','Online') NOT NULL,
                payment_date DATE NOT NULL,
                payment_status ENUM('Pending','Paid','Refunded') DEFAULT 'Pending',
                CONSTRAINT fk_payment_appointment FOREIGN KEY (appointment_id)
                    REFERENCES appointments(appointment_id) ON UPDATE CASCADE ON DELETE RESTRICT
            ) ENGINE=InnoDB""")
            cur.execute("""CREATE TABLE IF NOT EXISTS doctor_availability (
                availability_id INT AUTO_INCREMENT PRIMARY KEY,
                doctor_id INT NOT NULL,
                available_date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                slot_status ENUM('Available','Booked','Unavailable') DEFAULT 'Available',
                CONSTRAINT fk_availability_doctor FOREIGN KEY (doctor_id)
                    REFERENCES doctors(doctor_id) ON UPDATE CASCADE ON DELETE RESTRICT,
                UNIQUE KEY unique_doctor_availability
                    (doctor_id, available_date, start_time, end_time)
            ) ENGINE=InnoDB""")
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'doctors'
                  AND COLUMN_NAME = 'department_id'
            """)
            if cur.fetchone()[0] == 0:
                cur.execute("ALTER TABLE doctors ADD COLUMN department_id INT NULL AFTER doctor_id")
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'doctors'
                  AND CONSTRAINT_NAME = 'fk_doctor_department'
            """)
            if cur.fetchone()[0] == 0:
                cur.execute("""ALTER TABLE doctors ADD CONSTRAINT fk_doctor_department
                    FOREIGN KEY (department_id) REFERENCES departments(department_id)
                    ON UPDATE CASCADE ON DELETE SET NULL""")
            self.conn.commit()
        finally:
            cur.close()

    def seed_demo_data(self):
        """Add deterministic records without changing existing user data."""
        self.ensure_connection_without_tables()
        cur = self.conn.cursor()
        departments = [
            ("Cardiology", "Heart and cardiovascular care", "0422-410-2001"),
            ("Neurology", "Brain, spine and nervous system care", "0422-410-2002"),
            ("Dermatology", "Skin, hair and nail care", "0422-410-2003"),
            ("Orthopedics", "Bone, joint and musculoskeletal care", "0422-410-2004"),
            ("Pediatrics", "Medical care for infants and children", "0422-410-2005"),
        ]
        patients = [
            ("Aarav Sharma", 29, "Male", "9100000001", "demo.aarav@example.com", "Coimbatore"),
            ("Diya Menon", 34, "Female", "9100000002", "demo.diya@example.com", "Pollachi"),
            ("Arjun Rao", 41, "Male", "9100000003", "demo.arjun@example.com", "Chennai"),
            ("Ananya Das", 26, "Female", "9100000004", "demo.ananya@example.com", "Erode"),
            ("Ishaan Joseph", 52, "Male", "9100000005", "demo.ishaan@example.com", "Salem"),
            ("Meera Bose", 38, "Female", "9100000006", "demo.meera@example.com", "Madurai"),
            ("Rohan Pillai", 47, "Male", "9100000007", "demo.rohan@example.com", "Trichy"),
            ("Kavya Nair", 23, "Female", "9100000008", "demo.kavya@example.com", "Coimbatore"),
            ("Vikram Iyer", 61, "Male", "9100000009", "demo.vikram@example.com", "Tiruppur"),
            ("Nisha Thomas", 30, "Female", "9100000010", "demo.nisha@example.com", "Ooty"),
            ("Pranav Krishna", 44, "Male", "9100000011", "demo.pranav@example.com", "Kannur"),
            ("Sara Joseph", 36, "Female", "9100000012", "demo.sara@example.com", "Kochi"),
            ("Karthik Raj", 55, "Male", "9100000013", "demo.karthik@example.com", "Coimbatore"),
            ("Priya Shah", 28, "Female", "9100000014", "demo.priya@example.com", "Bengaluru"),
            ("Rahul Varma", 67, "Male", "9100000015", "demo.rahul@example.com", "Chennai"),
            ("Sneha Kapoor", 32, "Female", "9100000016", "demo.sneha@example.com", "Hyderabad"),
            ("Mohan Kumar", 49, "Male", "9100000017", "demo.mohan@example.com", "Madurai"),
            ("Lakshmi Devi", 58, "Female", "9100000018", "demo.lakshmi@example.com", "Salem"),
            ("Neel Joshi", 21, "Male", "9100000019", "demo.neel@example.com", "Pune"),
            ("Tara Singh", 40, "Female", "9100000020", "demo.tara@example.com", "Delhi"),
            ("Aditya Mehta", 33, "Male", "9100000021", "demo.aditya@example.com", "Mumbai"),
            ("Bhavna Reddy", 45, "Female", "9100000022", "demo.bhavna@example.com", "Hyderabad"),
            ("Chirag Patel", 37, "Male", "9100000023", "demo.chirag@example.com", "Ahmedabad"),
            ("Deepa Krishnan", 50, "Female", "9100000024", "demo.deepa@example.com", "Chennai"),
            ("Eshan Gupta", 27, "Male", "9100000025", "demo.eshan@example.com", "Delhi"),
            ("Farah Ali", 42, "Female", "9100000026", "demo.farah@example.com", "Bengaluru"),
            ("Gaurav Sethi", 56, "Male", "9100000027", "demo.gaurav@example.com", "Pune"),
            ("Hema Srinivas", 31, "Female", "9100000028", "demo.hema@example.com", "Mysuru"),
            ("Imran Sheikh", 48, "Male", "9100000029", "demo.imran@example.com", "Kochi"),
            ("Janani Murthy", 25, "Female", "9100000030", "demo.janani@example.com", "Coimbatore"),
            ("Kiran Bhat", 63, "Male", "9100000031", "demo.kiran@example.com", "Mangaluru"),
            ("Latha Prasad", 39, "Female", "9100000032", "demo.latha@example.com", "Vijayawada"),
            ("Manoj Nair", 46, "Male", "9100000033", "demo.manoj@example.com", "Kozhikode"),
            ("Nandini Rao", 29, "Female", "9100000034", "demo.nandini@example.com", "Bengaluru"),
            ("Omkar Joshi", 54, "Male", "9100000035", "demo.omkar@example.com", "Pune"),
            ("Pallavi Singh", 35, "Female", "9100000036", "demo.pallavi@example.com", "Jaipur"),
            ("Qasim Ahmed", 43, "Male", "9100000037", "demo.qasim@example.com", "Lucknow"),
            ("Radha Iyer", 60, "Female", "9100000038", "demo.radha@example.com", "Chennai"),
            ("Sanjay Bose", 32, "Male", "9100000039", "demo.sanjay@example.com", "Kolkata"),
            ("Tanvi Shah", 28, "Female", "9100000040", "demo.tanvi@example.com", "Surat"),
            ("Uday Kulkarni", 51, "Male", "9100000041", "demo.uday@example.com", "Nagpur"),
            ("Vaishali Jain", 36, "Female", "9100000042", "demo.vaishali@example.com", "Indore"),
            ("Wasim Khan", 47, "Male", "9100000043", "demo.wasim@example.com", "Bhopal"),
            ("Yamini Das", 24, "Female", "9100000044", "demo.yamini@example.com", "Guwahati"),
            ("Zubin Contractor", 58, "Male", "9100000045", "demo.zubin@example.com", "Mumbai"),
            ("Aditi Menon", 30, "Female", "9100000046", "demo.aditi@example.com", "Thrissur"),
            ("Bharat Rao", 65, "Male", "9100000047", "demo.bharat@example.com", "Hyderabad"),
            ("Charu Nair", 41, "Female", "9100000048", "demo.charu@example.com", "Kochi"),
            ("Dinesh Verma", 53, "Male", "9100000049", "demo.dinesh@example.com", "Chandigarh"),
            ("Ekta Kapoor", 27, "Female", "9100000050", "demo.ekta@example.com", "Delhi"),
        ]
        doctor_templates = [
            ("Dr. Asha Rao", "Cardiology", "9200000001", "demo.asha.doctor@example.com", "Mon-Wed-Fri", 900),
            ("Dr. Dev Menon", "Cardiology", "9200000002", "demo.dev.doctor@example.com", "Tue-Thu-Sat", 850),
            ("Dr. Neha Iyer", "Cardiology", "9200000003", "demo.neha.doctor@example.com", "Mon-Thu", 950),
            ("Dr. Kabir Shah", "Neurology", "9200000004", "demo.kabir.doctor@example.com", "Mon-Wed", 1100),
            ("Dr. Ritu Nair", "Neurology", "9200000005", "demo.ritu.doctor@example.com", "Tue-Fri", 1000),
            ("Dr. Omar Khan", "Neurology", "9200000006", "demo.omar.doctor@example.com", "Wed-Sat", 1050),
            ("Dr. Maya Joseph", "Dermatology", "9200000007", "demo.maya.doctor@example.com", "Mon-Fri", 700),
            ("Dr. Arvind Das", "Dermatology", "9200000008", "demo.arvind.doctor@example.com", "Tue-Thu", 750),
            ("Dr. Leena Paul", "Dermatology", "9200000009", "demo.leena.doctor@example.com", "Wed-Sat", 725),
            ("Dr. Hari Krishnan", "Orthopedics", "9200000010", "demo.hari.doctor@example.com", "Mon-Wed", 950),
            ("Dr. Pooja Rao", "Orthopedics", "9200000011", "demo.pooja.doctor@example.com", "Tue-Thu", 900),
            ("Dr. Sameer Ali", "Orthopedics", "9200000012", "demo.sameer.doctor@example.com", "Fri-Sat", 925),
            ("Dr. Isha Verma", "Pediatrics", "9200000013", "demo.isha.doctor@example.com", "Mon-Tue", 650),
            ("Dr. Nitin Babu", "Pediatrics", "9200000014", "demo.nitin.doctor@example.com", "Wed-Fri", 625),
            ("Dr. Alina George", "Pediatrics", "9200000015", "demo.alina.doctor@example.com", "Thu-Sat", 675),
        ]
        try:
            for name, description, phone in departments:
                cur.execute(
                    """INSERT INTO departments (name, description, phone)
                    SELECT %s, %s, %s FROM DUAL
                    WHERE NOT EXISTS (SELECT 1 FROM departments WHERE name=%s)""",
                    (name, description, phone, name)
                )
            cur.execute("SELECT department_id, name FROM departments")
            department_ids = {name: department_id for department_id, name in cur.fetchall()}

            for patient in patients:
                cur.execute(
                    """INSERT INTO patients
                    (full_name, age, gender, phone, email, address)
                    SELECT %s, %s, %s, %s, %s, %s FROM DUAL
                    WHERE NOT EXISTS (SELECT 1 FROM patients WHERE email=%s)""",
                    patient + (patient[4],)
                )
            cur.execute(
                """SELECT patient_id FROM patients
                WHERE email LIKE 'demo.%%@example.com'
                ORDER BY patient_id LIMIT 50"""
            )
            patient_ids = [row[0] for row in cur.fetchall()]

            for name, specialization, phone, email, days, fee in doctor_templates:
                department_id = department_ids[specialization]
                cur.execute(
                    """INSERT INTO doctors
                    (department_id, full_name, specialization, phone, email, available_days, consultation_fee)
                    SELECT %s, %s, %s, %s, %s, %s, %s FROM DUAL
                    WHERE NOT EXISTS (SELECT 1 FROM doctors WHERE email=%s)""",
                    (department_id, name, specialization, phone, email, days, fee, email)
                )
            cur.execute(
                """SELECT doctor_id FROM doctors
                WHERE email LIKE 'demo.%%.doctor@example.com'
                ORDER BY doctor_id LIMIT 15"""
            )
            doctor_ids = [row[0] for row in cur.fetchall()]
            if len(patient_ids) < 20 or len(doctor_ids) < 15:
                raise Error("Could not prepare enough patients or doctors.")

            base_date = datetime(2027, 1, 4)
            for index, doctor_id in enumerate(doctor_ids):
                for extra_day in (0, 1):
                    available_date = (base_date + timedelta(days=index * 2 + extra_day)).date()
                    start_hour = 9 + (index % 5)
                    start_time = f"{start_hour:02d}:00:00"
                    end_time = f"{start_hour + 1:02d}:00:00"
                    cur.execute(
                        """INSERT INTO doctor_availability
                        (doctor_id, available_date, start_time, end_time, slot_status)
                        SELECT %s, %s, %s, %s, 'Available' FROM DUAL
                        WHERE NOT EXISTS (
                            SELECT 1 FROM doctor_availability
                            WHERE doctor_id=%s AND available_date=%s
                              AND start_time=%s AND end_time=%s
                        )""",
                        (doctor_id, available_date, start_time, end_time,
                         doctor_id, available_date, start_time, end_time)
                    )

                booked_date = (base_date + timedelta(days=index * 2)).date()
                booked_time = f"{9 + (index % 5):02d}:00:00"
                cur.execute(
                    """SELECT availability_id FROM doctor_availability
                    WHERE doctor_id=%s AND available_date=%s
                      AND start_time=%s AND end_time=%s FOR UPDATE""",
                    (doctor_id, booked_date, booked_time, f"{10 + (index % 5):02d}:00:00")
                )
                availability = cur.fetchone()
                cur.execute(
                    """SELECT appointment_id FROM appointments
                    WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s""",
                    (doctor_id, booked_date, booked_time)
                )
                appointment = cur.fetchone()
                if appointment:
                    appointment_id = appointment[0]
                else:
                    cur.execute(
                        """INSERT INTO appointments
                        (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
                        VALUES (%s, %s, %s, %s, %s, 'Scheduled')""",
                        (patient_ids[index], doctor_id, booked_date, booked_time,
                         "Routine consultation")
                    )
                    appointment_id = cur.lastrowid
                cur.execute(
                    "UPDATE doctor_availability SET slot_status='Booked' WHERE availability_id=%s",
                    (availability[0],)
                )
                cur.execute(
                    """INSERT INTO payments
                    (appointment_id, amount, payment_method, payment_date, payment_status)
                    SELECT %s, %s, %s, %s, %s FROM DUAL
                    WHERE NOT EXISTS (SELECT 1 FROM payments WHERE appointment_id=%s)""",
                    (appointment_id, doctor_templates[index][5],
                     ("Card", "Online", "Insurance", "Cash")[index % 4],
                     booked_date, "Paid" if index % 3 else "Pending", appointment_id)
                )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def ensure_connection_without_tables(self):
        # During connect(), self.conn is already established; this helper prevents recursion.
        if self.conn is None or not self.conn.is_connected():
            raise Error("MySQL connection is not active.")

    def query(self, sql, params=(), fetch=False):
        self.ensure_connection()
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
            columns = [d[0] for d in cur.description] if fetch and cur.description else []
            if fetch:
                return columns, rows
            self.conn.commit()
            return columns, rows
        except Exception:
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            cur.close()

    def require_reference(self, table, column, value, label):
        _, rows = self.query(
            f"SELECT 1 FROM {table} WHERE {column}=%s LIMIT 1",
            (value,), fetch=True
        )
        if not rows:
            raise ValueError(f"{label} {value} does not exist.")

    def find_available_slot(self, doctor_id, appointment_date, appointment_time):
        _, rows = self.query(
            """SELECT availability_id, slot_status
            FROM doctor_availability
            WHERE doctor_id=%s AND available_date=%s
              AND start_time <= %s AND end_time > %s
            ORDER BY start_time LIMIT 1""",
            (doctor_id, appointment_date, appointment_time, appointment_time),
            fetch=True
        )
        if not rows:
            raise ValueError(
                f"Doctor {doctor_id} has no availability covering "
                f"{appointment_date} at {appointment_time}."
            )
        if rows[0][1] != "Available":
            raise ValueError(
                f"Doctor {doctor_id} availability at {appointment_date} "
                f"{appointment_time} is {rows[0][1].lower()}, not available."
            )
        return rows[0][0]

    def book_appointment(self, values, appointment_id=None):
        """Create or reschedule an appointment only inside an available slot."""
        self.ensure_connection()
        cur = self.conn.cursor()
        try:
            if appointment_id is not None:
                cur.execute("""SELECT doctor_id, appointment_date, appointment_time
                    FROM appointments WHERE appointment_id=%s FOR UPDATE""", (appointment_id,))
                old = cur.fetchone()
                if not old:
                    raise ValueError("Appointment was not found.")
                cur.execute("""UPDATE doctor_availability SET slot_status='Available'
                    WHERE doctor_id=%s AND available_date=%s
                      AND start_time <= %s AND end_time > %s""",
                    (old[0], old[1], old[2], old[2]))
            cur.execute(
                """SELECT availability_id, slot_status
                FROM doctor_availability
                WHERE doctor_id=%s AND available_date=%s
                  AND start_time <= %s AND end_time > %s
                ORDER BY start_time LIMIT 1 FOR UPDATE""",
                (values["doctor_id"], values["appointment_date"],
                 values["appointment_time"], values["appointment_time"])
            )
            slot = cur.fetchone()
            if not slot:
                raise ValueError(
                    f"Doctor {values['doctor_id']} has no availability covering "
                    f"{values['appointment_date']} at {values['appointment_time']}."
                )
            if slot[1] != "Available":
                raise ValueError(
                    f"Doctor {values['doctor_id']} availability at "
                    f"{values['appointment_date']} {values['appointment_time']} "
                    f"is {slot[1].lower()}, not available."
                )

            if appointment_id is None:
                cur.execute(
                    """INSERT INTO appointments
                    (patient_id, doctor_id, appointment_date, appointment_time, reason, status)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    tuple(values[field] for field in (
                        "patient_id", "doctor_id", "appointment_date",
                        "appointment_time", "reason", "status"
                    ))
                )
            else:
                cur.execute(
                    """UPDATE appointments SET patient_id=%s, doctor_id=%s,
                    appointment_date=%s, appointment_time=%s, reason=%s, status=%s
                    WHERE appointment_id=%s""",
                    tuple(values[field] for field in (
                        "patient_id", "doctor_id", "appointment_date",
                        "appointment_time", "reason", "status"
                    )) + (appointment_id,)
                )
            cur.execute(
                "UPDATE doctor_availability SET slot_status='Booked' WHERE availability_id=%s",
                (slot[0],)
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def delete_appointment(self, appointment_id):
        self.ensure_connection()
        cur = self.conn.cursor()
        try:
            cur.execute("""SELECT doctor_id, appointment_date, appointment_time
                FROM appointments WHERE appointment_id=%s FOR UPDATE""", (appointment_id,))
            appointment = cur.fetchone()
            if not appointment:
                raise ValueError("Appointment was not found.")
            cur.execute("""UPDATE doctor_availability SET slot_status='Available'
                WHERE doctor_id=%s AND available_date=%s
                  AND start_time <= %s AND end_time > %s""",
                (appointment[0], appointment[1], appointment[2], appointment[2]))
            cur.execute("DELETE FROM appointments WHERE appointment_id=%s", (appointment_id,))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CarePoint | Medical Appointment Scheduler")
        self.geometry("1220x760")
        self.minsize(1000, 650)
        self.configure(bg=BG)
        self.db = Database()
        self.current = "Patients"
        self.selected_id = None
        self.vars = {}
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Connecting to local MySQL...")
        self._style()
        self._layout()
        try:
            self.db.connect()
            self.status_var.set(f"Connected to MySQL Â· database: {DB_NAME}")
            self.navigate("Dashboard")
        except Error as e:
            self.status_var.set("Database connection failed")
            messagebox.showerror(
                "MySQL connection error",
                f"Could not connect to MySQL.\n\n{e}\n\n"
                "Check that MySQL Server is running and config.py has the correct credentials."
            )

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("Treeview", background=WHITE, fieldbackground=WHITE, foreground=TEXT,
                    rowheight=31, borderwidth=0, font=("Segoe UI", 9))
        s.configure("Treeview.Heading", background="#E8EEF8", foreground=NAVY,
                    font=("Segoe UI", 9, "bold"), padding=8)
        s.map("Treeview", background=[("selected", "#DCEAFE")], foreground=[("selected", NAVY)])
        s.configure("TCombobox", padding=5)
        s.configure("TEntry", padding=6)

    def _layout(self):
        sidebar = tk.Frame(self, bg=NAVY, width=205)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="CAREPOINT", bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=20, pady=(25, 4))
        tk.Label(sidebar, text="APPOINTMENT DESK", bg=NAVY, fg="#9FB2D5",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=21, pady=(0, 32))
        self.nav_buttons = {}
        for name, symbol in [
            ("Dashboard", ""), ("Patients", ""), ("Doctors", ""),
            ("Departments", ""), ("Appointments", ""),
            ("Doctor Availability", ""), ("Payments", "")
        ]:
            b = tk.Button(sidebar, text=name, anchor="w", relief="flat",
                          bd=0, cursor="hand2", bg=NAVY, fg="#DCE5F4",
                          activebackground="#263B60", activeforeground=WHITE,
                          font=("Segoe UI", 10), padx=15, pady=12,
                          command=lambda n=name: self.navigate(n))
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = b
        tk.Label(sidebar, text="DBMS PROJECT  |  PYTHON + MYSQL", bg=NAVY, fg="#9FB2D5",
                 font=("Segoe UI", 7), wraplength=165, justify="left").pack(side="bottom", anchor="w", padx=18, pady=20)

        main = tk.Frame(self, bg=BG)
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=WHITE, height=72)
        top.pack(fill="x")
        top.pack_propagate(False)
        self.page_title = tk.Label(top, text="Dashboard", bg=WHITE, fg=NAVY,
                                   font=("Segoe UI", 19, "bold"))
        self.page_title.pack(side="left", padx=25, pady=18)
        tk.Label(top, text="LOCAL DATABASE  |", bg=WHITE, fg=TEAL,
                 font=("Segoe UI", 9, "bold")).pack(side="right", padx=25)

        self.content = tk.Frame(main, bg=BG)
        self.content.pack(fill="both", expand=True, padx=22, pady=18)
        bottom = tk.Frame(main, bg=WHITE, height=28)
        bottom.pack(fill="x", side="bottom")
        tk.Label(bottom, textvariable=self.status_var, bg=WHITE, fg=MUTED,
                 font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=12, pady=5)

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def navigate(self, name):
        self.current = name
        self.selected_id = None
        self.page_title.config(text=name if name != "Dashboard" else "Overview")
        for n, b in self.nav_buttons.items():
            b.configure(bg=BLUE if n == name else NAVY, fg=WHITE if n == name else "#DCE5F4")
        self.clear_content()
        if name == "Dashboard":
            self.build_dashboard()
        else:
            self.build_manager(name)
            self.refresh()

    def build_dashboard(self):
        intro = tk.Frame(self.content, bg=BG)
        intro.pack(fill="x", pady=(0, 16))
        tk.Label(intro, text="Your clinic, organised.", bg=BG, fg=TEXT,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(intro, text="Manage patient records, doctor details and appointment bookings in one place.",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))
        cards = tk.Frame(self.content, bg=BG)
        cards.pack(fill="x")
        self.count_labels = {}
        for title, key, accent in [
            ("PATIENTS", "patients", BLUE),
            ("DOCTORS", "doctors", TEAL),
            ("APPOINTMENTS", "appointments", "#B45309")
        ]:
            card = tk.Frame(cards, bg=WHITE, highlightbackground="#E2E8F0", highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12), ipady=12)
            tk.Label(card, text=title, bg=WHITE, fg=MUTED,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(14, 2))
            lab = tk.Label(card, text="-", bg=WHITE, fg=accent, font=("Segoe UI", 26, "bold"))
            lab.pack(anchor="w", padx=18)
            self.count_labels[key] = lab
        panel = tk.Frame(self.content, bg=WHITE, highlightbackground="#E2E8F0", highlightthickness=1)
        panel.pack(fill="both", expand=True, pady=18)
        tk.Label(panel, text="Quick actions", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(17, 10))
        for label, target in [
            ("Register a patient", "Patients"),
            ("Add a doctor", "Doctors"),
            ("Book an appointment", "Appointments")
        ]:
            tk.Button(panel, text=label, command=lambda t=target: self.navigate(t), anchor="w",
                      bg="#F4F7FC", fg=TEXT, relief="flat", padx=15, pady=12,
                      font=("Segoe UI", 10), cursor="hand2").pack(fill="x", padx=18, pady=5)
        tk.Label(panel, text="Tip: use Import CSV to add multiple records, and Export CSV to save the current table.",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(12, 16))
        self.update_dashboard()

    def update_dashboard(self):
        if not hasattr(self, "count_labels"):
            return
        try:
            for key, lab in self.count_labels.items():
                if not lab.winfo_exists():
                    return
                _, rows = self.db.query(f"SELECT COUNT(*) FROM {key}", fetch=True)
                lab.config(text=str(rows[0][0]))
        except (Error, AttributeError, tk.TclError) as e:
            self.status_var.set(f"Dashboard query failed: {e}")

    def build_manager(self, name):
        cfg = TABLES[name]
        bar = tk.Frame(self.content, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text=f"{name} records", bg=BG, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Button(bar, text="Refresh", command=self.refresh, bg=WHITE, fg=NAVY,
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=(6, 0))
        tk.Button(bar, text="Export CSV", command=self.export_csv, bg=WHITE, fg=NAVY,
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=6)
        tk.Button(bar, text="Import CSV", command=self.import_csv, bg=TEAL, fg=WHITE,
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(side="right", padx=6)

        split = tk.PanedWindow(self.content, orient="horizontal", bg=BG, sashwidth=6, bd=0)
        split.pack(fill="both", expand=True)
        left = tk.Frame(split, bg=WHITE, highlightbackground="#E2E8F0", highlightthickness=1)
        right = tk.Frame(split, bg=WHITE, highlightbackground="#E2E8F0", highlightthickness=1)
        split.add(left, minsize=520, width=690)
        split.add(right, minsize=270, width=340)

        searchrow = tk.Frame(left, bg=WHITE)
        searchrow.pack(fill="x", padx=12, pady=12)
        self.search_var = tk.StringVar()
        ent = ttk.Entry(searchrow, textvariable=self.search_var)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 7))
        ent.bind("<Return>", lambda e: self.refresh())
        tk.Button(searchrow, text="Search", command=self.refresh, bg=BLUE, fg=WHITE,
                  relief="flat", padx=12, pady=6).pack(side="left")
        tk.Button(searchrow, text="Clear", command=lambda: (self.search_var.set(""), self.refresh()),
                  bg="#EEF2F7", fg=TEXT, relief="flat", padx=10, pady=6).pack(side="left", padx=(5, 0))

        self.tree = ttk.Treeview(left, columns=cfg["columns"], show="headings", selectmode="browse")
        for col, label, width in zip(cfg["columns"], cfg["labels"], cfg["widths"]):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, minwidth=50, anchor="w")
        yscroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(left, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.pack(fill="both", expand=True, padx=(12, 0))
        xscroll.pack(fill="x", padx=12)
        yscroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tk.Label(right, text="Record details", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(15, 2))
        tk.Label(right, text="Select a row to edit it, or fill the fields to create a new record.",
                 bg=WHITE, fg=MUTED, font=("Segoe UI", 8), wraplength=275,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 10))
        form = tk.Frame(right, bg=WHITE)
        form.pack(fill="both", expand=True, padx=16)
        self.vars = {}
        for field, label in zip(cfg["editable"], cfg["labels"][1:]):
            tk.Label(form, text=label, bg=WHITE, fg="#475569",
                     font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(4, 1))
            var = tk.StringVar()
            self.vars[field] = var
            if field == "status":
                widget = ttk.Combobox(form, textvariable=var,
                                      values=["Scheduled", "Completed", "Cancelled"], state="readonly")
                widget.set("Scheduled")
            elif field == "payment_method":
                widget = ttk.Combobox(form, textvariable=var,
                                      values=["Cash", "Card", "Insurance", "Online"], state="readonly")
                widget.set("Cash")
            elif field == "payment_status":
                widget = ttk.Combobox(form, textvariable=var,
                                      values=["Pending", "Paid", "Refunded"], state="readonly")
                widget.set("Pending")
            elif field == "slot_status":
                widget = ttk.Combobox(form, textvariable=var,
                                      values=["Available", "Booked", "Unavailable"], state="readonly")
                widget.set("Available")
            elif field == "gender":
                widget = ttk.Combobox(form, textvariable=var,
                                      values=["Female", "Male", "Other", "Prefer not to say"])
            else:
                widget = ttk.Entry(form, textvariable=var)
            widget.pack(fill="x", pady=(0, 3), ipady=1)

        buttons = tk.Frame(right, bg=WHITE)
        buttons.pack(fill="x", padx=16, pady=14)
        tk.Button(buttons, text="Add new", command=self.add_record, bg=BLUE, fg=WHITE,
                  relief="flat", padx=9, pady=8).pack(fill="x", pady=3)
        tk.Button(buttons, text="Save changes", command=self.update_record, bg=TEAL, fg=WHITE,
                  relief="flat", padx=9, pady=8).pack(fill="x", pady=3)
        tk.Button(buttons, text="Delete selected", command=self.delete_record,
                  bg="#FEE2E2", fg="#991B1B", relief="flat", padx=9, pady=8).pack(fill="x", pady=3)
        tk.Button(buttons, text="Clear form", command=self.clear_form, bg="#EEF2F7", fg=TEXT,
                  relief="flat", padx=9, pady=8).pack(fill="x", pady=3)

    def refresh(self):
        if self.current == "Dashboard" or not hasattr(self, "tree"):
            return
        cfg = TABLES[self.current]
        try:
            self.db.ensure_connection()
            for item in self.tree.get_children():
                self.tree.delete(item)
            search = self.search_var.get().strip()
            if search:
                searchable = cfg["columns"][1:]
                clause = " OR ".join([f"CAST({c} AS CHAR) LIKE %s" for c in searchable])
                params = tuple([f"%{search}%"] * len(searchable))
                _, rows = self.db.query(
                    f"SELECT {','.join(cfg['columns'])} FROM {cfg['table']} "
                    f"WHERE {clause} ORDER BY {cfg['columns'][0]} ASC", params, True
                )
            else:
                _, rows = self.db.query(
                    f"SELECT {','.join(cfg['columns'])} FROM {cfg['table']} "
                    f"ORDER BY {cfg['columns'][0]} ASC", fetch=True
                )
            for row in rows:
                self.tree.insert("", "end", values=[("" if v is None else str(v)) for v in row])
            self.status_var.set(f"Connected to MySQL Â· {len(rows)} {self.current.lower()} record(s) shown")
            self.update_dashboard()
        except (Error, AttributeError) as e:
            self.status_var.set("Database connection failed")
            messagebox.showerror("Query error", f"Could not load records:\n{e}")

    def on_select(self, _event=None):
        if not hasattr(self, "tree"):
            return
        selection = self.tree.selection()
        if not selection:
            return
        vals = self.tree.item(selection[0], "values")
        cfg = TABLES[self.current]
        self.selected_id = vals[0]
        for field, val in zip(cfg["editable"], vals[1:]):
            if field in self.vars:
                self.vars[field].set(val)

    def get_values(self):
        cfg = TABLES[self.current]
        values = {}
        for field, var in self.vars.items():
            raw = var.get().strip()
            if field in cfg["required"] and not raw:
                raise ValueError(f"{field.replace('_', ' ').title()} is required.")
            values[field] = raw if raw else None
        if self.current == "Patients" and values.get("age") is not None:
            age = int(values["age"])
            if not 0 <= age <= 125:
                raise ValueError("Age must be between 0 and 125.")
            values["age"] = age
        if self.current == "Doctors":
            if values.get("department_id") is not None:
                values["department_id"] = int(values["department_id"])
            values["consultation_fee"] = float(values["consultation_fee"] or 0)
            if values["consultation_fee"] < 0:
                raise ValueError("Consultation fee cannot be negative.")
        if self.current == "Appointments":
            values["patient_id"] = int(values["patient_id"])
            values["doctor_id"] = int(values["doctor_id"])
            datetime.strptime(values["appointment_date"], "%Y-%m-%d")
            if len(values["appointment_time"]) == 5:
                values["appointment_time"] += ":00"
            values["appointment_time"] = datetime.strptime(
                values["appointment_time"], "%H:%M:%S"
            ).strftime("%H:%M:%S")
            if values["status"] not in ("Scheduled", "Completed", "Cancelled"):
                raise ValueError("Status must be Scheduled, Completed or Cancelled.")
        if self.current == "Payments":
            values["appointment_id"] = int(values["appointment_id"])
            values["amount"] = float(values["amount"])
            if values["amount"] < 0:
                raise ValueError("Payment amount cannot be negative.")
            datetime.strptime(values["payment_date"], "%Y-%m-%d")
            if values["payment_method"] not in ("Cash", "Card", "Insurance", "Online"):
                raise ValueError("Payment method must be Cash, Card, Insurance or Online.")
            if values["payment_status"] not in ("Pending", "Paid", "Refunded", None):
                raise ValueError("Payment status must be Pending, Paid or Refunded.")
            if values["payment_status"] is None:
                values["payment_status"] = "Pending"
        if self.current == "Doctor Availability":
            values["doctor_id"] = int(values["doctor_id"])
            datetime.strptime(values["available_date"], "%Y-%m-%d")
            for field in ("start_time", "end_time"):
                if len(values[field]) == 5:
                    values[field] += ":00"
                values[field] = datetime.strptime(
                    values[field], "%H:%M:%S"
                ).strftime("%H:%M:%S")
            if values["start_time"] >= values["end_time"]:
                raise ValueError("End time must be later than start time.")
            if values["slot_status"] not in ("Available", "Booked", "Unavailable", None):
                raise ValueError("Slot status must be Available, Booked or Unavailable.")
            if values["slot_status"] is None:
                values["slot_status"] = "Available"
        return values

    def add_record(self):
        try:
            self.db.ensure_connection()
            cfg = TABLES[self.current]
            values = self.get_values()
            fields = list(values.keys())
            placeholders = ",".join(["%s"] * len(fields))
            if self.current == "Appointments":
                self.db.book_appointment(values)
            else:
                self.db.query(
                    f"INSERT INTO {cfg['table']} ({','.join(fields)}) VALUES ({placeholders})",
                    tuple(values[f] for f in fields)
                )
            self.clear_form()
            self.refresh()
            messagebox.showinfo("Saved", "Record added successfully.")
        except (ValueError, Error, AttributeError) as e:
            messagebox.showerror("Could not add record", str(e))

    def update_record(self):
        if not self.selected_id:
            messagebox.showwarning("Select a record", "Choose a row from the table before saving changes.")
            return
        try:
            self.db.ensure_connection()
            cfg = TABLES[self.current]
            values = self.get_values()
            assignments = ", ".join([f"{f}=%s" for f in values])
            if self.current == "Appointments":
                self.db.book_appointment(values, self.selected_id)
            else:
                self.db.query(
                    f"UPDATE {cfg['table']} SET {assignments} WHERE {cfg['columns'][0]}=%s",
                    tuple(values[f] for f in values) + (self.selected_id,)
                )
            self.clear_form()
            self.refresh()
            messagebox.showinfo("Updated", "Record updated successfully.")
        except (ValueError, Error, AttributeError) as e:
            messagebox.showerror("Could not update record", str(e))

    def delete_record(self):
        if not self.selected_id:
            messagebox.showwarning("Select a record", "Choose a row from the table before deleting.")
            return
        if not messagebox.askyesno("Confirm deletion", "Delete the selected record? This cannot be undone."):
            return
        cfg = TABLES[self.current]
        try:
            self.db.ensure_connection()
            if self.current == "Appointments":
                self.db.delete_appointment(self.selected_id)
            else:
                self.db.query(
                    f"DELETE FROM {cfg['table']} WHERE {cfg['columns'][0]}=%s",
                    (self.selected_id,)
                )
            self.clear_form()
            self.refresh()
            messagebox.showinfo("Deleted", "Record deleted successfully.")
        except (Error, AttributeError) as e:
            messagebox.showerror(
                "Delete blocked",
                f"MySQL could not delete this record.\n\n{e}\n\n"
                "Appointments linked to a patient or doctor must be removed first."
            )

    def clear_form(self):
        self.selected_id = None
        for field, var in self.vars.items():
            defaults = {
                "status": "Scheduled",
                "payment_method": "Cash",
                "payment_status": "Pending",
                "slot_status": "Available",
            }
            var.set(defaults.get(field, ""))
        if hasattr(self, "tree"):
            for item in self.tree.selection():
                self.tree.selection_remove(item)

    def import_csv(self):
        # Ensure a live DB connection before processing any CSV rows.
        try:
            self.db.ensure_connection()
        except (Error, AttributeError) as e:
            messagebox.showerror("Database connection error", f"Could not connect to MySQL:\n{e}")
            return

        cfg = TABLES[self.current]
        path = filedialog.askopenfilename(
            title="Choose CSV file",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        success = 0
        skipped = []
        failed = []
        try:
            with open(path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError("CSV file must contain a header row.")
                # Trim accidental spaces in CSV headers.
                reader.fieldnames = [name.strip() if name else name for name in reader.fieldnames]
                fields = cfg["csv"]
                missing = [field for field in fields if field not in reader.fieldnames]
                if missing:
                    raise ValueError(
                        "CSV headers do not match this section.\nRequired headers: " + ", ".join(fields)
                    )

                for line, row in enumerate(reader, start=2):
                    try:
                        row = {(k.strip() if k else k): v for k, v in row.items()}
                        values = [(row.get(field) or "").strip() or None for field in fields]

                        if self.current == "Patients":
                            if not values[0]:
                                raise ValueError("Full name is required")
                            if values[1] is not None:
                                values[1] = int(values[1])
                                if not 0 <= values[1] <= 125:
                                    raise ValueError("Age must be between 0 and 125")
                            _, existing = self.db.query(
                                """SELECT patient_id FROM patients
                                WHERE full_name=%s AND (phone=%s OR email=%s)
                                LIMIT 1""",
                                (values[0], values[3], values[4]), fetch=True
                            )
                            if existing:
                                skipped.append(
                                    f"Line {line}: patient already exists (ID {existing[0][0]})"
                                )
                                continue

                        elif self.current == "Doctors":
                            if values[0] is None:
                                raise ValueError("Department ID is required for a doctor.")
                            if values[0] is not None:
                                values[0] = int(values[0])
                                self.db.require_reference(
                                    "departments", "department_id", values[0], "Department ID"
                                )
                            if not values[1]:
                                raise ValueError("Doctor name is required")
                            if not values[2]:
                                raise ValueError("Specialization is required")
                            values[-1] = float(values[-1] or 0)
                            if values[-1] < 0:
                                raise ValueError("Consultation fee cannot be negative")
                            _, existing = self.db.query(
                                """SELECT doctor_id FROM doctors
                                WHERE full_name=%s AND (phone=%s OR email=%s)
                                LIMIT 1""",
                                (values[1], values[3], values[4]), fetch=True
                            )
                            if existing:
                                self.db.query(
                                    """UPDATE doctors SET department_id=%s
                                    WHERE doctor_id=%s AND department_id IS NULL""",
                                    (values[0], existing[0][0])
                                )
                                skipped.append(
                                    f"Line {line}: doctor already exists; reused ID {existing[0][0]}"
                                )
                                continue

                        elif self.current == "Appointments":
                            if not values[0] or not values[1]:
                                raise ValueError("Patient ID and Doctor ID are required")
                            values[0] = int(values[0])
                            values[1] = int(values[1])
                            self.db.require_reference(
                                "patients", "patient_id", values[0], "Patient ID"
                            )
                            self.db.require_reference(
                                "doctors", "doctor_id", values[1], "Doctor ID"
                            )
                            if not values[2] or not values[3]:
                                raise ValueError("Appointment date and time are required")
                            datetime.strptime(values[2], "%Y-%m-%d")
                            if len(values[3]) == 5:
                                values[3] += ":00"
                            values[3] = datetime.strptime(
                                values[3], "%H:%M:%S"
                            ).strftime("%H:%M:%S")
                            if values[5] not in ("Scheduled", "Completed", "Cancelled", None):
                                raise ValueError("Status must be Scheduled, Completed or Cancelled")
                            if values[5] is None:
                                values[5] = "Scheduled"
                            _, existing = self.db.query(
                                """SELECT appointment_id FROM appointments
                                WHERE doctor_id=%s AND appointment_date=%s
                                  AND appointment_time=%s LIMIT 1""",
                                (values[1], values[2], values[3]), fetch=True
                            )
                            if existing:
                                skipped.append(
                                    f"Line {line}: appointment already exists "
                                    f"(ID {existing[0][0]})"
                                )
                                continue
                            self.db.find_available_slot(values[1], values[2], values[3])
                        elif self.current == "Payments":
                            values[0] = int(values[0])
                            values[1] = float(values[1])
                            if values[1] < 0:
                                raise ValueError("Payment amount cannot be negative")
                            self.db.require_reference(
                                "appointments", "appointment_id", values[0], "Appointment ID"
                            )
                            datetime.strptime(values[3], "%Y-%m-%d")
                            if values[2] not in ("Cash", "Card", "Insurance", "Online"):
                                raise ValueError("Payment method must be Cash, Card, Insurance or Online")
                            if values[4] not in ("Pending", "Paid", "Refunded", None):
                                raise ValueError("Payment status must be Pending, Paid or Refunded")
                            if values[4] is None:
                                values[4] = "Pending"
                            _, existing = self.db.query(
                                "SELECT payment_id FROM payments WHERE appointment_id=%s LIMIT 1",
                                (values[0],), fetch=True
                            )
                            if existing:
                                skipped.append(
                                    f"Line {line}: payment already exists (ID {existing[0][0]})"
                                )
                                continue
                        elif self.current == "Doctor Availability":
                            values[0] = int(values[0])
                            self.db.require_reference(
                                "doctors", "doctor_id", values[0], "Doctor ID"
                            )
                            datetime.strptime(values[1], "%Y-%m-%d")
                            if len(values[2]) == 5:
                                values[2] += ":00"
                            if len(values[3]) == 5:
                                values[3] += ":00"
                            values[2] = datetime.strptime(
                                values[2], "%H:%M:%S"
                            ).strftime("%H:%M:%S")
                            values[3] = datetime.strptime(
                                values[3], "%H:%M:%S"
                            ).strftime("%H:%M:%S")
                            if values[2] >= values[3]:
                                raise ValueError("End time must be later than start time")
                            if values[4] not in ("Available", "Booked", "Unavailable", None):
                                raise ValueError("Slot status must be Available, Booked or Unavailable")
                            if values[4] is None:
                                values[4] = "Available"
                            _, existing = self.db.query(
                                """SELECT availability_id FROM doctor_availability
                                WHERE doctor_id=%s AND available_date=%s
                                  AND start_time=%s AND end_time=%s LIMIT 1""",
                                (values[0], values[1], values[2], values[3]), fetch=True
                            )
                            if existing:
                                skipped.append(
                                    f"Line {line}: availability already exists "
                                    f"(ID {existing[0][0]})"
                                )
                                continue
                        elif self.current == "Departments":
                            if not values[0]:
                                raise ValueError("Department name is required")
                            _, existing = self.db.query(
                                "SELECT department_id FROM departments WHERE name=%s LIMIT 1",
                                (values[0],), fetch=True
                            )
                            if existing:
                                skipped.append(
                                    f"Line {line}: department already exists (ID {existing[0][0]})"
                                )
                                continue

                        marks = ",".join(["%s"] * len(fields))
                        if self.current == "Appointments":
                            appointment_values = dict(zip(fields, values))
                            self.db.book_appointment(appointment_values)
                        else:
                            self.db.query(
                                f"INSERT INTO {cfg['table']} ({','.join(fields)}) VALUES ({marks})",
                                tuple(values)
                            )
                        success += 1
                    except Exception as e:
                        failed.append(f"Line {line}: {e}")

            self.refresh()
            summary = f"Imported {success} record(s)."
            if skipped:
                summary += f"\nSkipped {len(skipped)} existing record(s):\n" + "\n".join(skipped[:12])
            if failed:
                summary += f"\nFailed {len(failed)} row(s):\n" + "\n".join(failed[:12])
                if len(failed) > 12:
                    summary += f"\n...and {len(failed) - 12} more."
            messagebox.showinfo("CSV import result", summary)
        except (OSError, ValueError, Error) as e:
            messagebox.showerror("Import failed", str(e))

    def export_csv(self):
        try:
            self.db.ensure_connection()
        except (Error, AttributeError) as e:
            messagebox.showerror("Database connection error", f"Could not connect to MySQL:\n{e}")
            return
        cfg = TABLES[self.current]
        path = filedialog.asksaveasfilename(
            title="Export records",
            defaultextension=".csv",
            initialfile=f"{cfg['table']}_export.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        try:
            _, rows = self.db.query(
                f"SELECT {','.join(cfg['columns'])} FROM {cfg['table']} ORDER BY {cfg['columns'][0]}",
                fetch=True
            )
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(cfg["columns"])
                writer.writerows(rows)
            messagebox.showinfo("Export complete", f"Saved {len(rows)} record(s) to:\n{path}")
        except (OSError, Error, AttributeError) as e:
            messagebox.showerror("Export failed", str(e))


if __name__ == "__main__":
    App().mainloop()
