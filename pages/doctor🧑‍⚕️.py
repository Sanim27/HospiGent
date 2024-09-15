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

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
todate = date.today()
today = todate.strftime("%A")

# Check if the user is logged in
if not st.session_state.get('doc_logged_in', False):
    st.warning("You must log in first to access the Doctor's page.")
    st.switch_page("pages/doc_login.py")  # Redirect to login page
    st.experimental_rerun()  # Rerun the app to show the login page

st.title(f"Welcome, {st.session_state.full_name}!")


def get_patients(doctors_name, day=today):
    # Connect to MySQL
    connection = mysql.connector.connect(
        host=os.getenv('Host'),
        database=os.getenv('Database_name'),
        user=os.getenv('Database_user'),
        password=os.getenv('Database_password')
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
        print(patients)

        # Use `with` statement to manage MongoDB connection
        with MongoClient(os.getenv('mongo_client')) as client:
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
                additional_details = collection.find_one({"username": patient[0]})

                if additional_details:
                    # Exclude '_id' field from additional details if it exists
                    additional_details.pop('_id', None)
                    patient_data['additional'] = additional_details

                patients_with_additional_details.append(patient_data)
                print(patients_with_additional_details)
                

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
    patients_info  = get_patients(st.session_state.full_name,'Thursday')

    if "messages_doc" not in st.session_state:
        st.session_state.messages_doc = [
                {"role": "system", "content": """You are an assistant for a doctor at a hospital. Your job is to help the doctor by providing information about the patients they will examine today. Here’s how you should respond:

        1. **If the doctor asks who they are examining today,** provide a list of patients in this format: 
        - name: patient_name
        - problem: patient_problem
        - appointment_time: time_range

        Example: 
        name: John Doe, problem: headache, appointment_time: 2:00pm-3:00pm

        Then also ask doctor if the doctor specifically wants any additional details of any patients.

        2. **If the doctor asks for more details about a patient,** provide extra information only if it's available from the patient's data. If no extra details are available, just say that the information is not available.

        3. Do not create or guess any patient information on your own. You will be given the patient's information, and you should only use that.

        4. Since you are a good chatbot, it is your duty to always reply to the user(in this case doctor)

        You will receive a list of patients and their information. Some patients might have additional details from their medical report, but others may not. If no extra information is available, just note that the patient does not have a report."""},
                {"role": "system", "content": f"Here is the patient's information for the day: {patients_info}"}
            ]


     #displaying messages
    for message in st.session_state.messages_doc:
        if message["role"] != "system":
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    question = st.chat_input("How may I help you ?")
    if question:
        with st.chat_message("user"):
            st.markdown(question)

        st.session_state.messages_doc.append({"role": "user", "content": question})

        with st.chat_message("assistant"):
            # Generate a response from the assistant
            generated = client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages_doc
                ],
                stream=False,
            )
            response_content = generated.choices[0].message.content
            st.session_state.messages_doc.append({"role":"assistant","content":response_content})
            display_in_chunks_with_cursor(response_content)


if __name__=="__main__":
    main()
