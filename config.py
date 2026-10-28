import os


DB_HOST = os.getenv("MEDICAL_DB_HOST", "localhost")
DB_PORT = int(os.getenv("MEDICAL_DB_PORT", "3307"))
DB_USER = os.getenv("MEDICAL_DB_USER", "root")
DB_PASSWORD = os.getenv("MEDICAL_DB_PASSWORD", "")
DB_NAME = os.getenv("MEDICAL_DB_NAME", "medical_appointment_db")
