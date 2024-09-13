import mysql.connector
import os
import random
import string
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database connection details from environment variables
mysql_password = os.getenv("mysql_password")

# Function to generate a random unique password
def generate_unique_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def initialize_database():
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=mysql_password
    )
    cursor = db_connection.cursor()
    
    # Drop and create the database
    cursor.execute("DROP DATABASE IF EXISTS hospital")
    cursor.execute("CREATE DATABASE hospital")
    cursor.execute("USE hospital")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE doctors (
            full_name VARCHAR(255) NOT NULL,
            availability_days VARCHAR(255) NOT NULL,
            availability_time VARCHAR(255) NOT NULL,
            specialization VARCHAR(255) NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100),
            problem VARCHAR(255),
            email VARCHAR(255),
            doctor_booked VARCHAR(100),
            appointment_day VARCHAR(50),
            appointment_time VARCHAR(50),
            password VARCHAR(255) UNIQUE NOT NULL
        )
    """)
    
    # Insert initial data into doctors table
    doctors_data = [
        ('Dr. Alice Smith', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Cardiology'),
        ('Dr. Bob Johnson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Dermatology'),
        ('Dr. Charlie Davis', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Endocrinology'),
        ('Dr. Diana Moore', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Gastroenterology'),
        ('Dr. Edward Brown', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Hematology'),
        ('Dr. Fiona Wilson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Neurology'),
        ('Dr. George Taylor', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Oncology'),
        ('Dr. Helen Anderson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Ophthalmology'),
        ('Dr. Ian Thompson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Orthopedics'),
        ('Dr. Jane Martinez', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Pediatrics'),
        ('Dr. Kevin White', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Psychiatry'),
        ('Dr. Laura Harris', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Radiology')
    ]
    cursor.executemany("""
        INSERT INTO doctors (full_name, availability_days, availability_time, specialization)
        VALUES (%s, %s, %s, %s)
    """, doctors_data)
    
    db_connection.commit()
    cursor.close()
    db_connection.close()

def add_new_patient(full_name, problem, email, doctor_booked, appointment_day, appointment_time):
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=mysql_password,
        database="hospital"
    )
    
    cursor = db_connection.cursor()
    
    password = generate_unique_password()
    insert_query = """
        INSERT INTO patients (full_name, problem, email, doctor_booked, appointment_day, appointment_time, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    patient_data = (full_name, problem, email, doctor_booked, appointment_day, appointment_time, password)
    
    try:
        cursor.execute(insert_query, patient_data)
        db_connection.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        db_connection.rollback()
    finally:
        cursor.close()
        db_connection.close()

# Initialize the database
if __name__ == "__main__":
    initialize_database()

