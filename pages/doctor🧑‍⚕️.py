import streamlit as st
from langchain_groq import ChatGroq
import mysql.connector
from groq import Groq
import dotenv
import time
from datetime import date
import os
from pymongo import MongoClient
dotenv.load_dotenv()

client = Groq()
todate = date.today()
today = todate.strftime("%A")

# Check if the user is logged in
if not st.session_state.get('logged_in', False):
    st.warning("You must log in first to access the Doctor's page.")
    st.switch_page("/Users/sanimpandey/Desktop/lang/pages/doc_login.py")  # Redirect to login page
    st.experimental_rerun()  # Rerun the app to show the login page

st.title(f"Welcome, {st.session_state.full_name}!")


def get_patients(doctors_name, day=today):
    # Connect to MySQL
    connection = mysql.connector.connect(
        host="localhost",
        database='hospital',
        user="root",
        password=os.getenv('mysql_password')
    )

    patients_with_additional_details = []

    if connection.is_connected():
        cursor = connection.cursor()

        # Query to fetch patients for the given doctor and day
        check_query = """SELECT full_name, problem, email, appointment_time
                         FROM patients 
                         WHERE doctor_booked = %s AND appointment_day = %s"""
        
        cursor.execute(check_query, (doctors_name, day))
        patients = cursor.fetchall()

        # Use `with` statement to manage MongoDB connection
        with MongoClient('mongodb://localhost:27017/') as client:
            db = client['Hospital']
            collection = db['Patients']

            for patient in patients:
                patient_data = {
                    "full_name": patient[0],
                    "problem": patient[1],
                    "email": patient[2],
                    "appointment_time": patient[3],
                    "additional": {}
                }

                # Fetch additional details from MongoDB based on patient's full_name
                additional_details = collection.find_one({"name": patient[0]})

                if additional_details:
                    # Exclude '_id' field from additional details if it exists
                    additional_details.pop('_id', None)
                    patient_data['additional'] = additional_details

                patients_with_additional_details.append(patient_data)

        # Close MySQL connection
        cursor.close()
        connection.close()

    return patients_with_additional_details

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


def main():
    st.title("Doctor's agent")
    patients_info  = get_patients('Dr. Bob Johnson', 'Monday')

    if "messages" not in st.session_state:
        st.session_state.messages=[
            {"role":"system","content":"""you are an hospital's agent designed to help the doctors about various patients he will be looking today and also 
             provide a detail analysis of what medical issue the patient might have based on your knowledge.
             answer whenever doctor asks about something. 
              Your will be provided with 
             a list of all the patients the doctor will visit today and the patient's data contain some general information as well as additional information which is taken from their medical report.
             if additional information is empty, it means that the patient doesnot have any report .
             """},
             {"role": "system", "content": f"Here is the doctor's information: {patients_info}"}
        ]

     #displaying messages
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
            st.session_state.messages.append({"role":"assistant","content":response_content})
            display_in_chunks_with_cursor(response_content)


if __name__=="__main__":
    main()
