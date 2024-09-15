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

# Function to verify login credentials for admin (only id and name)
def verify_admin_login(admin_id, admin_name):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Query to check if the admin exists with the matching id and name
    query = "SELECT id FROM admin WHERE id = %s AND name = %s"
    cursor.execute(query, (admin_id, admin_name))
    
    result = cursor.fetchone()
    connection.close()

    if result:
        return True
    return False

# Admin Login UI
st.title("Admin Login")

# Input fields for Admin ID and Full Name
admin_id = st.text_input("Enter your Admin ID")
admin_name = st.text_input("Enter your full name")

# Button to log in
if st.button("Login as Admin"):
    if verify_admin_login(admin_id, admin_name):
        st.session_state.logged_in = True
        st.session_state.admin_id = admin_id
        st.session_state.admin_name = admin_name
        st.success("Login successful!")
        
        # Redirect to the admin page
        st.switch_page("pages/admin🧑‍💼.py")
        st.experimental_rerun()
    else:
        st.error("Login failed. Please check your Admin ID or Full Name.")
