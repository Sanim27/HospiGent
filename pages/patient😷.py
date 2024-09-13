import os
from dotenv import load_dotenv
import streamlit as st
import mysql.connector
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
from database import add_new_patient


# Load environment variables
load_dotenv()
GROQ_BASE_URL = "https://api.groq.ai/v1/"  # Updated base URL for Groq API

# Use Groq API key from the environment
# api_key = os.getenv('GROQ_API_KEY')
client = Groq(
    # This is the default and can be omitted
    api_key=os.environ.get("GROQ_API_KEY"),
)

# genai.configure(api_key=os.environ["gemini_key"])

# model = "gemini-1.5-flash-vlm"

st.title("MediSched")

def send_emails(patient_email, text_to_send):
    connection = mysql.connector.connect(
        host="localhost",
        database='hospital',
        user="root",
        password=os.getenv('mysql_password')
    )
    try:
        # Email server setup
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Login credentials (use environment variables for security)
        sender_email = os.getenv('email')
        sender_password = os.getenv('password')
        server.login(sender_email, sender_password)

        # Compose the email
        subject = "Confirmation mail"
        result = ""

        # Check the connection and fetch the password
        if connection.is_connected():
            cursor = connection.cursor()
            check_query = """SELECT password FROM patients WHERE email = %s"""
            
            # The issue was here, patient_email should be passed as a tuple
            cursor.execute(check_query, (patient_email,))
            result = cursor.fetchone()

        # Handle case where no password is found
        if result:
            password = result[0]  # Fetch the password from the result
        else:
            password = "No password found for this email."

        body = f"{text_to_send}. Your password for the additional information section is: {password}"

        # Setup the email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = patient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.send_message(msg)
        print("Mail sent successfully.")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Close connections
        if connection.is_connected():
            connection.close()
        server.quit()

#Book appointment function
def book_appointment(patient_info):
    connection = mysql.connector.connect(
    host="localhost",
    database='hospital',
    user="root",
    password=os.getenv('mysql_password')
)
    
    if connection.is_connected():
        cursor = connection.cursor()

        # Extract patient information
        doctor_name = patient_info['doctor']
        preferred_day = patient_info['preferred_day']
        preferred_time = patient_info['preferred_time']

        # Check if the preferred day and time are already booked for the doctor
        check_query = """SELECT * FROM patients 
                         WHERE doctor_booked = %s AND appointment_day = %s AND appointment_time = %s"""
        cursor.execute(check_query, (doctor_name, preferred_day, preferred_time))
        result = cursor.fetchone()

        if result:
            # The time slot is already booked
            response_dict = {"response": "The selected time slot on {} at {} is already booked. Please choose another time slot.".format(preferred_day, preferred_time)}
            response_json = json.dumps(response_dict)
            st.markdown(response_dict["response"])
            st.session_state.messages.append({"role": "assistant", "content": response_json})

        else:
            print("add new patient huna aatyo")
            add_new_patient(patient_info['name'], patient_info['problem'], patient_info['email'], doctor_name, preferred_day, preferred_time)

            conformation_text="Appointment booked successfully for {} on {} at {}.".format(patient_info['name'], preferred_day, preferred_time)
            # st.markdown(marking)
            send_emails(patient_info['email'],conformation_text) 

        connection.close()

def reschedule_appointment(new_info):
    connection = mysql.connector.connect(
    host="localhost",
    database='hospital',
    user="root",
    password=os.getenv('mysql_password')
)
    
    if connection.is_connected():
        cursor = connection.cursor()

        # Fetch the current appointment details
        fetch_query = """SELECT email,doctor_booked, appointment_day, appointment_time 
                         FROM patients WHERE full_name = %s"""
        cursor.execute(fetch_query, (new_info['patient_name'],))
        result = cursor.fetchone()
        
        if result:
            email,doctor_name, current_day, current_time = result

            # Check if the new day and time slot are already booked for the same doctor
            check_query = """SELECT * FROM patients 
                             WHERE doctor_booked = %s AND appointment_day = %s AND appointment_time = %s"""
            cursor.execute(check_query, (doctor_name, new_info['new_day'], new_info['new_time']))
            check_result = cursor.fetchone()

            if check_result:
                # New time slot is already booked
                response_dict = {"response": "The selected new time slot on {} at {} is already booked. Please choose another time slot.".format(new_info['new_day'], new_info['new_time'])}
                response_json = json.dumps(response_dict)
                st.markdown(response_dict["response"])
                st.session_state.messages.append({"role": "assistant", "content": response_json})
            else:
                # The new time slot is available, proceed with rescheduling
                update_patient_query = """UPDATE patients 
                                          SET appointment_day = %s, appointment_time = %s 
                                          WHERE full_name = %s"""
                cursor.execute(update_patient_query, (new_info['new_day'], new_info['new_time'], new_info['patient_name']))
                connection.commit()

                confirmation_text="Appointment rescheduled successfully to {} on {}.".format(new_info['new_time'], new_info['new_day'])
                send_emails(email,confirmation_text)
                
        else:
            st.markdown("Patient not found.")

        connection.close()

          
def cancel_appointment(patient_name):
    connection = mysql.connector.connect(
    host="localhost",
    database='hospital',
    user="root",
    password=os.getenv('mysql_password')
)

    if connection.is_connected():
        cursor = connection.cursor()

        # Fetch the current appointment details for the patient
        fetch_query = """SELECT email,doctor_booked, appointment_day, appointment_time 
                         FROM patients WHERE full_name = %s"""
        cursor.execute(fetch_query, (patient_name,))
        result = cursor.fetchone()
        
        if result:
            email,doctor_name, appointment_day, appointment_time = result

            # Remove the patient's appointment from the patients table
            delete_patient_query = """DELETE FROM patients WHERE full_name = %s"""
            cursor.execute(delete_patient_query, (patient_name,))
            
            # Commit the changes
            connection.commit()

            confirmation_text = f"Appointment with {doctor_name} on {appointment_day} at {appointment_time} canceled successfully."
            send_emails(email,confirmation_text)
        else:
            response_dict = {"response": "No patient with name {} has booked an appointment.".format(patient_name)}
            response_json = json.dumps(response_dict)
            st.markdown(response_dict["response"])
            st.session_state.messages.append({"role": "assistant", "content": response_json})
        
        connection.close()

# Function to retrieve doctors' information from the database
def retrieve_database_info():
    connection = mysql.connector.connect(
    host="localhost",
    database='hospital',
    user="root",
    password=os.getenv('mysql_password')
)
    if connection.is_connected():
        doctor_list = []
        if connection.is_connected():
            cursor = connection.cursor()
            query = 'SELECT * FROM doctors'
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            doctor_list = [dict(zip(column_names, row)) for row in rows]
            cursor.close()
            connection.close()
        doctors_info = '\n'.join([str(doctor) for doctor in doctor_list])
        return doctors_info
    
def retrieve_patient_info():
    connection = mysql.connector.connect(
        host="localhost",
        database='hospital',
        user="root",
        password=os.getenv('mysql_password')
    )
    if connection.is_connected():
        patient_list = []
        try:
            cursor = connection.cursor()
            query = 'SELECT * FROM patients'
            cursor.execute(query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            patient_list = [dict(zip(column_names, row)) for row in rows]
            cursor.close()
            connection.close()
        except mysql.connector.Error as err:
            print(f"Error: {err}")
        finally:
            connection.close()
        
        patients_info = '\n'.join([str(patient) for patient in patient_list])
        return patients_info
    else:
        return "Unable to connect to the database"

# Example usage
patients_info = retrieve_patient_info()

doctors_info = retrieve_database_info()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """You are a hospital's chatbot that helps patients book, reschedule, or cancel appointments with doctors. You have access to both the hospital's doctor availability and the current appointment schedule, including patient information and time slots already booked. If a patient attempts to book a doctor who is already occupied during their requested time, you should inform the patient that the slot is unavailable and suggest alternative times. For example, if Dr. Ian Thompson is already booked by another patient on Tuesday from 2:00 PM to 3:00 PM, and the current user requests that time, you should clearly inform them that Dr. Thompson is unavailable at that time and provide alternate time slots from the doctor's schedule."""
        },
        {
            "role": "system",
            "content": """You are only allowed to suggest doctors based on the doctor information provided in the hospital database. Do not invent any new doctor names or schedules. If no matching doctor is available, clearly inform the patient that no doctors are available at the requested time."""
        },
        {
            "role": "system",
            "content": f"Here is the doctor's information from the database: {doctors_info}. Only use the information from this list to suggest doctor names and their available times."
        },
        {
            "role": "system",
            "content": f"Here is the patient's appointment information, including times that are already booked: {patients_info}. When checking for doctor availability, cross-check the current user's requested time with these bookings."
        },
        {
            "role": "system",
            "content": """
Instructions:

1. **Conversational Questions:**
   - Reply freely but use the following format strictly because this is used for parsing later on:
     ```
     {"response": "your reply", "schedule": "no"}
     ```

2. **Doctor Information:**
   - If asked about a doctor, respond with relevant details using only the information in the hospital's database. Use this format:
     ```
     {"response": "Dr. Alice Smith is available from Monday to Friday at 10:00 AM - 12:00 PM and 1:00 PM - 3:00 PM.", "schedule": "no"}
     ```
   - Recommend doctors based on the user's problem (e.g., cardiologist for heart issues) **but only from the provided list of doctors**.

3. **Book an Appointment:**
   - Ask for: full name, problem, preferred day, preferred time, email, and doctor (if not provided). **Important note** : ask email compulsorily while asking name.
   - If all details are provided and the doctor is available, format the response like this:
     ```
     {"response": "Your appointment has been scheduled with Dr. Smith for Monday at 2:00 PM. You will receive a confirmation email soon.", 
     "patient_info": {"name": "John Doe", "problem": "Headache", "preferred_day": "Monday", "preferred_time": "2:00 PM - 3:00 PM", "email": "JohnDoe@gmail.com", "doctor": "Dr. Smith"}, 
     "schedule": "yes"}
     ```
   - **Important**: Check if the doctor is already booked during the requested time by comparing against the patient appointment information. If the doctor is not available, suggest alternative slots.
   - Also ask if the patient has any past medical reports, so that it is useful for doctor to review. Ask them to upload their report in important:***additional*** section if they have past medical record. Donot force them as this is not mandatory.

4. **Reschedule an Appointment:**
   - Ask for: user's full name, new day, new time.
   - If all details are provided and the doctor is available, format the response like this:
     ```
     {"response": "Your appointment has been rescheduled for Tuesday at 11:00 AM. You will receive a confirmation email soon.", 
     "new_info": {"patient_name": "John Doe", "new_day": "Tuesday", "new_time": "11:00 AM - 12:00 PM"}, 
     "schedule": "reschedule"}
     ```
   - Check if the new requested time is available for the doctor by comparing with the current patient appointments.

5. **Cancel an Appointment:**
   - Ask for: user's full name.
   - If the name is provided, format the response like this:
     ```
     {"response": "Your appointment with Dr. Smith has been cancelled. You will receive a confirmation email soon.", 
     "patient_name": "John Doe", 
     "schedule": "cancel"}
     ```

- You must use the `book_appointment`, `reschedule_appointment`, and `cancel_appointment` functions to handle these operations based on the responses you generate. Ensure the responses follow the exact formats specified above to trigger the appropriate functions.
"""
        }
    ]

# Display chat messages excluding system messages
for message in st.session_state.messages:
    if message["role"] != "system":
        if message["role"] == "assistant":
            try:
                json_objects = message["content"].splitlines()
                for json_str in json_objects:
                    if json_str.strip():  
                        response_content_prev = json.loads(json_str)
                        with st.chat_message(message["role"]):
                            st.markdown(response_content_prev["response"])
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


question = st.chat_input("How can I help you?")
if question:
    # Display user message to the container
    with st.chat_message("user"):
        st.markdown(question)
    # Add the message to the history
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        # Generate a response from the assistant
        generated = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ],
            stream=False,
        )
        response_content = generated.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": response_content})
        try:
            # Extract JSON from the response content
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                response_dict = json.loads(json_match.group())
                if response_dict['schedule'] == 'no':
                    st.markdown(response_dict['response'])

                elif response_dict['schedule'] == 'yes':
                    patient_info = response_dict['patient_info']
                    st.markdown(response_dict['response'])
                    book_appointment(patient_info)

                elif response_dict['schedule']=='reschedule':
                    new_info = response_dict['new_info']
                    st.markdown(response_dict['response'])
                    reschedule_appointment(new_info)

                elif response_dict['schedule']=='cancel':
                    patient_name=response_dict['patient_name']
                    st.markdown(response_dict['response'])
                    cancel_appointment(patient_name)
            else:
                st.error("No valid JSON found in the response.")
        except json.JSONDecodeError:
            st.error("Failed to parse response as JSON.")