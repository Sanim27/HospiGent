import os
from dotenv import load_dotenv
import streamlit as st
import mysql.connector
import json
import re
import mysql.connector
import os
import string
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
import time
import textwrap


# Load environment variables
load_dotenv()

# client = openai.OpenAI(api_key=api_key, base_url=AI71_BASE_URL)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("MediSched")
def generate_unique_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def send_emails(patient_email, text_to_send):
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
        body = f"{text_to_send}"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = patient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.send_message(msg)


    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Close the server connection
        server.quit()


#Book appointment function
def book_appointment(response_dict):
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        patient_info = response_dict['patient_info']
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
            response = "The selected time slot on {} at {} is already booked. Please choose another time slot.".format(preferred_day, preferred_time)
            display_in_chunks_with_cursor(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

        else:
            password = generate_unique_password()
            # The time slot is available, proceed with booking
            insert_query = """INSERT INTO patients (full_name, problem,email, doctor_booked, appointment_day, appointment_time,password) 
                              VALUES (%s, %s, %s, %s, %s, %s,%s)"""
            cursor.execute(insert_query, (
                patient_info['name'], 
                patient_info['problem'], 
                patient_info['email'], 
                doctor_name, 
                preferred_day, 
                preferred_time,
                password
            ))
            connection.commit()

            conformation_text="Appointment booked successfully for {} on {} at {}. and your additional information section login patient id is {}".format(patient_info['name'], preferred_day, preferred_time,password)
            send_emails(patient_info['email'],conformation_text)
            st.session_state.messages.append({"role":"assistant","content":response_dict['response']})
            display_in_chunks_with_cursor(response_dict['response'])
    

        connection.close()

def reschedule_appointment(response_dict):
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        new_info=response_dict['new_info']
        # Fetch the current appointment details
        fetch_query = """SELECT email,doctor_booked, appointment_day, appointment_time 
                         FROM patients WHERE full_name = %s and password = %s"""
        cursor.execute(fetch_query, (new_info['patient_name'],new_info['password'],))
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
                response = "The selected new time slot on {} at {} is already booked. Please choose another time slot.".format(new_info['new_day'], new_info['new_time'])
                display_in_chunks_with_cursor(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # The new time slot is available, proceed with rescheduling
                update_patient_query = """UPDATE patients 
                                          SET appointment_day = %s, appointment_time = %s 
                                          WHERE full_name = %s and password = %s"""
                cursor.execute(update_patient_query, (new_info['new_day'], new_info['new_time'], new_info['patient_name'],new_info['patient_id']))
                connection.commit()

                confirmation_text="Appointment rescheduled successfully to {} on {}.".format(new_info['new_time'], new_info['new_day'])
                send_emails(email,confirmation_text)
                st.session_state.messages.append({"role":"assistant","content":response_dict['response']})
                display_in_chunks_with_cursor(response_dict['response'])
                
        else:
            display_in_chunks_with_cursor("Patient not found.")
            st.session_state.messages.append({"role":"assistant","content":"Patient not found"})

        connection.close()

          
def cancel_appointment(response_dict):
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
    )

    if connection.is_connected():
        cursor = connection.cursor()
        patient_name = response_dict['patient_name']
        password = response_dict['patient_id']
        # Fetch the current appointment details for the patient
        fetch_query = """SELECT email,doctor_booked, appointment_day, appointment_time 
                         FROM patients WHERE full_name = %s and password = %s"""
        cursor.execute(fetch_query, (patient_name,password,))
        result = cursor.fetchone()
        
        if result:
            email,doctor_name, appointment_day, appointment_time = result

            # Remove the patient's appointment from the patients table
            delete_patient_query = """DELETE FROM patients WHERE full_name = %s and password = %s"""
            cursor.execute(delete_patient_query, (patient_name,password,))
            
            # Commit the changes
            connection.commit()

            confirmation_text = f"Appointment with {doctor_name} on {appointment_day} at {appointment_time} canceled successfully."
            send_emails(email,confirmation_text)
            display_in_chunks_with_cursor(response_dict['response'])
            st.session_state.messages.append({"role":"assistant","content":response_dict['response']})
        else:
            response = "No patient with name {} has booked an appointment.".format(patient_name)
            display_in_chunks_with_cursor(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        
        connection.close()

# Function to retrieve doctors' information from the database
def retrieve_database_info():
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
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

doctors_info = retrieve_database_info()

#Initialize the chat history

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a hospital's chatbot that helps people book, reschedule, or cancel appointments with doctors. You have access to the hospital's doctor information."},
        {"role": "system", "content": f"Here is the doctor's information: {doctors_info}"},
        {"role": "system", "content": """
Instructions:

1. **Conversational Questions:**
   - Reply freely but use the following format:
     ```
     {"response": "your reply", "schedule": "no"}
     ```

2. **Doctor Information:**
   - If asked about a doctor, respond with relevant details and use this format:
     ```
     {"response": "Dr. Alice Smith is available from Monday to Friday at 11:00 AM-12:00 AM and 2:00 PM-3:00 PM.", "schedule": "no"}
     ```
   - Recommend doctors based on the user's problem (e.g., cardiologist for heart issues).

3. **Book an Appointment:**
   - Ask for: full name, problem, preferred day, preferred time, email, and doctor if not provided.
   - If all details are provided(if not ask for the detail again), format the response like this to trigger booking function:
     ```
     {"response": "Your appointment has been scheduled with Dr. Smith for Monday at 2:00 PM - 3:00 PM (or 10:00 AM - 11:00 PM). You will receive a confirmation email soon.(add some greetings and something about arival time )", 
     "patient_info": {"name": "John Doe", "problem": "Headache", "preferred_day": "Monday", "preferred_time": "2:00 PM-3:00 PM", "email": "JohnDoe@gmail.com", "doctor": "Dr. Smith"}, 
     "schedule": "yes"}
     ```  
    - note: after appointment is scheduled, if the user says ok donot book it again , it simply means user knows that his/her appointment is booked.    
         example :
       assistant:  "Your appointment has been scheduled with Dr. Ian Thompson for Monday at 10:00 AM - 11:00 AM. You will receive a confirmation email soon. Please arrive at least 15 minutes prior to your scheduled appointment time. One of our staff members will assist you with the check-in process."

       user: "ok".
         here, user means to say that he understood his appointment has been scheduled. so , reply in conversational format as in 1.

4. **Reschedule an Appointment:**
   - Ask for: user's full name and patient_id that was provided during appointment booking , new day, new time.
   - If all details are provided, format the response like this to trigger rescheduling function.
     ```
     {"response": "Your appointment has been rescheduled for Tuesday at 11:00 AM. You will receive a confirmation email soon.", 
     "new_info": {"patient_name": "John Doe","patient_id":"132243443", "new_day": "Tuesday", "new_time": "11:00 AM - 12:00 PM"}, 
     "schedule": "reschedule"}
     ```

5. **Cancel an Appointment:**
   - Ask for: user's full name and patient_id that was provided while booking.
   - If the name and password is provided, format the response like this to trigger cancellation function.
     ```
     {"response": "Your appointment has been cancelled. You will receive a confirmation email soon.", "patient_name": "John Doe", "patient_id":"12313433",   
     "schedule": "cancel"}
     ```
 -Note that, there are book_appointment,reschedule_appointment and cancel_appointment functions defined to do the appointment,rescheduling and cancellation job. you just need to respond in the corresponding format as shown above to trigger these functions.
       
         """}
    ]
# Display chat messages excluding system messages
for message in st.session_state.messages:
    if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def display_in_chunks_with_cursor(response, chunk_size=10, delay=0.05):
    message_placeholder = st.empty()
    
    # Initialize an empty string to accumulate the text
    accumulated_text = ""
    
    # Iterate over the text in chunks
    for i in range(0, len(response), chunk_size):
        # Get the current chunk
        chunk = response[i:i+chunk_size]
        # Append the chunk to the accumulated text
        accumulated_text += chunk
        # Update the placeholder with the accumulated text and the cursor "▌"
        message_placeholder.markdown(accumulated_text + "▌", unsafe_allow_html=True)
        # Wait for 'delay' seconds before displaying the next chunk
        time.sleep(delay)
    
    # After all chunks are displayed, remove the cursor
    message_placeholder.markdown(accumulated_text, unsafe_allow_html=True)

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
        try:
            # Extract JSON from the response content
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                response_dict = json.loads(json_match.group())
                if response_dict['schedule'] == 'no':
                    st.session_state.messages.append({"role":"assistant","content":response_dict['response']})
                    display_in_chunks_with_cursor(response_dict['response'])

                elif response_dict['schedule'] == 'yes':
                    book_appointment(response_dict)

                elif response_dict['schedule']=='reschedule':
                    reschedule_appointment(response_dict)

                elif response_dict['schedule']=='cancel':
                    cancel_appointment(response_dict)
            else:
                display_in_chunks_with_cursor(response_content)
                st.session_state.messages.append({"role":"assistant","content":response_content})
        except json.JSONDecodeError:
            st.markdown(response_content)
