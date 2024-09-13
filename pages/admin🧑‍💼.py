import streamlit as st
import mysql.connector
from groq import Groq
import os
import time
import dotenv
import re
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
dotenv.load_dotenv()

client = Groq()

if not st.session_state.get('logged_in', False):
    st.warning("You must log in first to access the Admin page.")
    st.switch_page("/Users/sanimpandey/Desktop/lang/pages/admin_login.py")  # Redirect to login page
    st.experimental_rerun() 

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
        subject = "test report"
        body = f"{text_to_send}"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = patient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.send_message(msg)
        print("Mail sent")


    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Close the server connection
        server.quit()

def doctor_unavailable(doctor_name,message):
# Helper function to get the next day of the week
    def get_next_day(current_day):
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Find the index of the current day
        current_index = days_of_week.index(current_day)
        
        # Calculate the next day
        next_index = (current_index + 1) % 7
        
        return days_of_week[next_index]
    # Connect to MySQL
    connection = mysql.connector.connect(
        host="localhost",
        database='hospital',
        user="root",
        password=os.getenv('mysql_password')
    )

    if connection.is_connected():
        cursor = connection.cursor()

        # Select patients with current doctor's appointment
        select_query = """SELECT full_name, appointment_day,email
                          FROM patients 
                          WHERE doctor_booked = %s"""
        cursor.execute(select_query, (doctor_name,))
        patients = cursor.fetchall()

        # Check if there are any patients to update
        if not patients:
            display_in_chunks_with_cursor(f"{doctor_name} has no any appointments today so the unavailability won't matter much.")
            st.session_state.messages.append({"role":"assistant","content":f"{doctor_name} has no any appointments today so the unavailability won't matter much."})
            cursor.close()
            connection.close()
            return

        # Iterate through the patients and update their appointment day
        for patient in patients:
            full_name, current_day,email = patient
            
            # Get the next day of the week
            next_day = get_next_day(current_day)

            # Update the appointment day to the next day of the week
            update_query = """UPDATE patients 
                              SET appointment_day = %s 
                              WHERE doctor_booked = %s AND full_name = %s"""
            cursor.execute(update_query, (next_day, doctor_name, full_name))
            send_emails(email,message)

        connection.commit()

        st.session_state.messages.append({"role":"assistant","content":"I have successfully updated the database and conveyed this information to patients."})
        display_in_chunks_with_cursor("I have successfully updated the database and conveyed this information to patients.")

        # Close the connection
        cursor.close()
        connection.close()


def send_message_to_patient(patients_dict, message):
    # Connect to MySQL
    connection = mysql.connector.connect(
        host="localhost",
        database='hospital',
        user="root",
        password=os.getenv('mysql_password')
    )

    if connection.is_connected():
        cursor = connection.cursor()

        if patients_dict.get('patients') == 'all':
            # Fetch all patients
            select_query = """SELECT full_name, email FROM patients"""
            cursor.execute(select_query)
        else:
            # Extract the list of patient names from the dictionary
            patient_names = patients_dict.get('patients', [])
            st.markdown(patient_names)
            if not patient_names:
                display_in_chunks_with_cursor("you didn't provided patients name")
                st.session_state.messages.append({"role":"assistant","content":"you didn't provided patients name"})
                cursor.close()
                connection.close()
                return
            
            # Fetch the emails of the patients in the provided list
            format_strings = ','.join(['%s'] * len(patient_names))
            select_query = f"SELECT full_name, email FROM patients WHERE full_name IN ({format_strings})"
            cursor.execute(select_query, tuple(patient_names))
        
        result = cursor.fetchall()

        # If no patients were found, return
        if not result:
            display_in_chunks_with_cursor("no any patients of such names. please recheck and provide correct names of the patients.")
            st.session_state.messages.append({"role":"assistant","content":"no any patients of such names. please recheck and provide correct names of the patients."})
            cursor.close()
            connection.close()
            return
        
        # Iterate through each patient and send the email
        for patient in result:
            full_name, email = patient
            send_emails(email,message)

        st.session_state.messages.append({"role":"assistant","content":"Your task has been executed successfully. All the patients are notified."})
        display_in_chunks_with_cursor("Your task has been executed successfully. All the patients are notified.")
        # Close the cursor and connection
        cursor.close()
        connection.close()

def display_in_chunks_with_cursor(response, chunk_size=10, delay=0.05):
    message_placeholder = st.empty()
    
    accumulated_text = ""
    
    for i in range(0, len(response), chunk_size):
        chunk = response[i:i+chunk_size]
        accumulated_text += chunk
        message_placeholder.markdown(accumulated_text + "▌", unsafe_allow_html=True)
        time.sleep(delay)
    
    message_placeholder.markdown(accumulated_text, unsafe_allow_html=True)

def get_info_client(query):
    # Connect to the MySQL database
    connection = mysql.connector.connect(
        host="localhost",
        database="hospital",
        user="root",
        password=os.getenv("mysql_password")
    )

    result = None  # Placeholder for the query result
    
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()  # Fetch the query result

        # Close the connection
        cursor.close()
        connection.close()

    if result:
        # Format the result into a human-readable format (for example, JSON)
        formatted_result = "\n".join([str(row) for row in result])

        # Pass the formatted result to the LLM for generating a response
        system_prompt = """
        You are an assistant helping hospital administrative staff. Please provide the requested appointment details in a clear and understandable way. 
        If the information contains patient names, appointment times, or doctor names, format it neatly in bullet points or tables where appropriate.
        Be concise but ensure all relevant information is provided clearly.
        """
        
        # Send query result to LLM
        generated = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"The result of the query: {formatted_result}"}
            ],
            stream=False,
        )
        # Get the response from the LLM
        response_content = generated.choices[0].message.content
        display_in_chunks_with_cursor(response_content)
        st.session_state.messages.append({"role":"assistant","content":response_content})        
    else:
        display_in_chunks_with_cursor("some error realted to query occured.")

def main():
    # st.title("Admin Panel")
    st.title(f"Welcome, {st.session_state.admin_name}!")

    client = Groq()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role":"system","content":"""You are an assistant for hospital administrative staff. You need to make a conversation with the admin staff and perform certain tasks for him/her.
             you have multiple tools to assist you with.
             
        1. To respond to staff for conversation other than task execution , always respond in this format keeping tool key to 'no'. 
        {
        "tool": "no",
        "response": "Your answer or response"
        }

        2. If the staff needs to inform patients about a doctor's unavailability:
        ask for the doctor's name and simple message to tell to the patients. and make a call to doctor_not_available tool by responding in following format.
        {
        "tool": "doctor_not_available",
        "doctor_name": "Name of the doctor",
        "message": "message for the patients (you can elaborate it by mentioning that the patient's appointment has been shifted to one day later and you can reschedule it by going to the booking and rescheduling section.)"
        }
             
        3. If the staff wants to send a message to specific patients(ask for patients names unless not provided) or all patients and also ask for the messages to be sent(unless not provided). 
        once that is provided make a call to send_message_to_patient tool by responding in the following format
        Respond in this format:
        {
        "tool": "send_message_to_patient",
        "patients": "all" or list of patient names like this ['John Doe', 'Jane Smith'],
        "message": "The message to be sent (you can elaborate it )"
        }
             
        4. If the staff wants information about appointments, you need to call 'get_info' tool and send the required sql query (the database hospital has two tables doctors patients. appointment details are stored in patients table . patient table has attributes full_name,problem,email,doctor_booked, appointment_day and appointment_time.)
        you need to respond in this format
        {
        "tool": "get_info",
        "query": "SQL query to fetch the required appointment details"
        }    
             """}
        ]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    question = st.chat_input("How may I help you ?")
    if question:
        with st.chat_message("user"):
            st.markdown(question)

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
            st.markdown(response_content)
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                response_dict = json.loads(json_match.group())
                if response_dict['tool']=='no':
                    display_in_chunks_with_cursor(response_dict['response'])
                    st.session_state.messages.append({"role":"assistant","content":response_dict['response']})
                elif response_dict['tool']=='doctor_not_available':
                    doctor_unavailable(response_dict['doctor_name'],response_dict['message'])
                elif response_dict['tool']=='send_message_to_patient':
                    send_message_to_patient(response_dict,response_dict['message'])
                elif response_dict['tool']=='get_info':
                    get_info_client(response_dict['query'])
            else:
                st.markdown("no json response")


if __name__=="__main__":
    main()   