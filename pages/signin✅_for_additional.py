import streamlit as st
import mysql.connector
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

# MySQL connection setup
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        database="hospital",
        user="root",
        password=os.getenv('mysql_password')
    )
    return connection

# Function to verify login credentials
def verify_login(full_name, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Query to check if the user exists and if the password matches
    query = "SELECT password FROM patients WHERE full_name = %s"
    cursor.execute(query, (full_name,))  # Exact match on full name
    
    result = cursor.fetchone()
    print(result)
    connection.close()
    
    if result:
        stored_password = result[0]
        if stored_password == password:
            return True
    return False

# Streamlit app layout
st.title("Login Page")

# Input form for login
full_name = st.text_input("Enter your full name", max_chars=255)
password = st.text_input("Enter your password", type="password", max_chars=50)

# Button to log in
if st.button("Login"):
    if verify_login(full_name, password):
        st.success("Login successful! Redirecting to the next page...")
        
        # Set session state for redirection
        st.session_state.logged_in = True
        st.session_state.username = full_name
        st.session_state.password = password
        
        # Use st.rerun() for page refresh
        st.rerun()
    else:
        st.error("Login failed. Please check your name or password.")

# Handle redirection to the additional.py page
if st.session_state.get('logged_in', False):
    st.switch_page("/Users/sanimpandey/Desktop/lang/pages/additional➕.py")