import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL connection setup
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
    )
    return connection

# Function to verify login credentials (only doctor_id and full_name)
def verify_login(doctor_id, full_name):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Query to check if the doctor exists with the matching doctor_id and full_name
    query = "SELECT doctor_id FROM doctors WHERE doctor_id = %s AND full_name = %s"
    cursor.execute(query, (doctor_id, full_name))
    
    result = cursor.fetchone()
    connection.close()

    if result:
        return True
    return False

# Login UI
st.title("Doctor Login")

# Input fields for Doctor ID and Full Name
doctor_id = st.text_input("Enter your Doctor ID")
full_name = st.text_input("Enter your full name")

# Button to log in
if st.button("Login"):
    if verify_login(doctor_id, full_name):
        st.session_state.logged_in = True
        st.session_state.doctor_id = doctor_id
        st.session_state.full_name = full_name
        st.success("Login successful!")
        
        # Redirect to the doctor page
        st.switch_page("pages/doctor🧑‍⚕️.py")
        st.experimental_rerun()
    else:
        st.error("Login failed. Please check your Doctor ID or Full Name.")
