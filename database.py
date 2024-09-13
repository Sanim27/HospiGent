# import mysql.connector
# import os
# from dotenv import load_dotenv

# # Load environment variables from .env file
# load_dotenv()

# # Get the database connection details from environment variables
# mysql_password = os.getenv("mysql_password")


# def initialize_database():
#     db_connection = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password=mysql_password
#     )
#     cursor = db_connection.cursor()
    
#     # Drop and create the database
#     cursor.execute("DROP DATABASE IF EXISTS hospital")
#     cursor.execute("CREATE DATABASE hospital")
#     cursor.execute("USE hospital")
    
#     # Create tables
#     cursor.execute("""
#         CREATE TABLE doctors (
#             doctor_id INT NOT NULL UNIQUE,
#             full_name VARCHAR(255) NOT NULL,
#             availability_days VARCHAR(255) NOT NULL,
#             availability_time VARCHAR(255) NOT NULL,
#             specialization VARCHAR(255) NOT NULL
#         )
#     """)
    
#     cursor.execute("""
#         CREATE TABLE patients (
#             id INT AUTO_INCREMENT PRIMARY KEY,
#             full_name VARCHAR(100),
#             problem VARCHAR(255),
#             email VARCHAR(255),
#             doctor_booked VARCHAR(100),
#             appointment_day VARCHAR(50),
#             appointment_time VARCHAR(50),
#             password VARCHAR(255) UNIQUE NOT NULL
#         )
#     """)
    
#     # Insert initial data into doctors table
#     doctors_data = [
#         (202401, 'Dr. Alice Smith', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Cardiology'),
#         (202402, 'Dr. Bob Johnson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Dermatology'),
#         (202403, 'Dr. Charlie Davis', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Endocrinology'),
#         (202404, 'Dr. Diana Moore', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Gastroenterology'),
#         (202405, 'Dr. Edward Brown', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Hematology'),
#         (202406, 'Dr. Fiona Wilson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Neurology'),
#         (202407, 'Dr. George Taylor', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Oncology'),
#         (202408, 'Dr. Helen Anderson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Ophthalmology'),
#         (202409, 'Dr. Ian Thompson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Orthopedics'),
#         (202410, 'Dr. Jane Martinez', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Pediatrics'),
#         (202411, 'Dr. Kevin White', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Psychiatry'),
#         (202412, 'Dr. Laura Harris', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Radiology')
#     ]
    
#     cursor.executemany("""
#         INSERT INTO doctors (doctor_id, full_name, availability_days, availability_time, specialization)
#         VALUES (%s, %s, %s, %s, %s)
#     """, doctors_data)
    
#     db_connection.commit()
#     cursor.close()
#     db_connection.close()

# # Initialize the database
# if __name__ == "__main__":
#     initialize_database()

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database connection details from environment variables
mysql_password = os.getenv("mysql_password")


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
    
    # Create doctors table
    cursor.execute("""
        CREATE TABLE doctors (
            doctor_id INT NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            availability_days VARCHAR(255) NOT NULL,
            availability_time VARCHAR(255) NOT NULL,
            specialization VARCHAR(255) NOT NULL
        )
    """)
    
    # Create patients table
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

    # Create admin table
    cursor.execute("""
        CREATE TABLE admin (
            id INT NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL
        )
    """)

    # Insert initial data into doctors table
    doctors_data = [
        (202401, 'Dr. Alice Smith', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Cardiology'),
        (202402, 'Dr. Bob Johnson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Dermatology'),
        (202403, 'Dr. Charlie Davis', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Endocrinology'),
        (202404, 'Dr. Diana Moore', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Gastroenterology'),
        (202405, 'Dr. Edward Brown', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Hematology'),
        (202406, 'Dr. Fiona Wilson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Neurology'),
        (202407, 'Dr. George Taylor', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Oncology'),
        (202408, 'Dr. Helen Anderson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Ophthalmology'),
        (202409, 'Dr. Ian Thompson', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Orthopedics'),
        (202410, 'Dr. Jane Martinez', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Pediatrics'),
        (202411, 'Dr. Kevin White', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Psychiatry'),
        (202412, 'Dr. Laura Harris', 'Monday to Friday', '10:00 AM - 12:00 PM, 1:00 PM - 3:00 PM', 'Radiology')
    ]
    
    cursor.executemany("""
        INSERT INTO doctors (doctor_id, full_name, availability_days, availability_time, specialization)
        VALUES (%s, %s, %s, %s, %s)
    """, doctors_data)
    
    # Insert initial data into admin table
    admin_data = [
        (202501, 'Sanim Pandey'),
        (202502, 'Yubraj Sharma')
    ]

    cursor.executemany("""
        INSERT INTO admin (id, name)
        VALUES (%s, %s)
    """, admin_data)
    
    # Commit changes and close connection
    db_connection.commit()
    cursor.close()
    db_connection.close()

# Initialize the database
if __name__ == "__main__":
    initialize_database()



