import streamlit as st
import dotenv
import os
import json
import re
from PIL import Image
from audio_recorder_streamlit import audio_recorder
import base64
from io import BytesIO
import google.generativeai as genai
import random
from pymongo import MongoClient

dotenv.load_dotenv()
# Check if user is logged in
if not st.session_state.get('logged_in', False):
    st.text("PLEASE GO TO SIGNIN PAGE FIRST")
    st.switch_page("/Users/sanimpandey/Desktop/lang/pages/signin✅_for_additional.py")  # Redirect back to login page if not logged in

# Your additional page content goes here
# st.title(f"Welcome, {st.session_state.username}!")

# Function to find information by patient name
def find_information(patient_name):
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Hospital']
    collection = db['Patients']
    patient_info = collection.find_one({"name": patient_name})
    print(patient_info)

# Function to store patient information in MongoDB
def information_store(patient_info, user, pw):
    print("information store called")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['Hospital']
    collection = db['Patients']

    # Check if username and password already exist in the database
    existing_user = collection.find_one({"username": user, "password": pw})
    
    # Prepare the document to store
    document = {
        "username": user,
        "password": pw,
        "patient_info": patient_info
    }
    
    if existing_user:
        # Update the existing user with new patient information
        collection.update_one(
            {"username": user, "password": pw},
            {"$set": {"patient_info": patient_info}}
        )
        print(f"Updated patient information for user: {user}")
    else:
        # Insert new record if the user does not exist
        collection.insert_one(document)
        print(f"Inserted new patient information for user: {user}")


# Convert messages to a format for the Gemini model
def messages_to_gemini(messages):
    gemini_messages = []
    prev_role = None
    for message in messages:
        if prev_role and (prev_role == message["role"]):
            gemini_message = gemini_messages[-1]
        else:
            gemini_message = {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [],
            }
        # Check if message["content"] is a list, if not, treat it as a single string
        if isinstance(message["content"], list):
            for content in message["content"]:
                if isinstance(content, dict):  # Ensure content is a dictionary
                    if content["type"] == "text":
                        gemini_message["parts"].append(content["text"])
                    elif content["type"] == "image_url":
                        gemini_message["parts"].append(base64_to_image(content["image_url"]["url"]))
                    elif content["type"] == "video_file":
                        gemini_message["parts"].append(genai.upload_file(content["video_file"]))
                    elif content["type"] == "audio_file":
                        gemini_message["parts"].append(genai.upload_file(content["audio_file"]))
        else:
            gemini_message["parts"].append(message["content"])

        if prev_role != message["role"]:
            gemini_messages.append(gemini_message)
        
        prev_role = message["role"]

    return gemini_messages

def stream_llm_response():
    genai.configure()
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config={
            "temperature": 0.3,
        }
    )
    gemini_messages = messages_to_gemini(st.session_state.messages)
    response = model.generate_content(contents=gemini_messages, stream=False)
    response = response.text
    print(response)
    
    # Attempt to extract JSON-like part of the response
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        response_dict = json.loads(json_match.group())
        response_message = response_dict.get("patient_response", "No response available")  # Default message if not present
        
        # Check if the conversation is complete
        chat_complete = response_dict.get('chat_complete', '').lower()  # Lowercase comparison
        if chat_complete == 'yes':
            print("Chat completed, triggering information_store") # For debugging
            information_store(response_dict['information_to_store'], st.session_state.username, st.session_state.password)
            print("Information stored as chat_complete is 'yes'")
        else:
            st.markdown(response_message)
        
        # Append assistant message regardless of chat_complete status
        st.session_state.messages.append({
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": response_message,
                }
            ]
        })
    else:
        st.markdown("No valid response received from the model.")



# Helper function to convert file to base64
def get_image_base64(image_raw):
    buffered = BytesIO()
    image_raw.save(buffered, format=image_raw.format)
    img_byte = buffered.getvalue()
    return base64.b64encode(img_byte).decode('utf-8')

# Function to convert base64 string to image
def base64_to_image(base64_string):
    base64_string = base64_string.split(",")[1]
    return Image.open(BytesIO(base64.b64decode(base64_string)))

# Main function for the Streamlit app
def main():
    st.title("Additional Information")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": """
                You are a chatbot for a hospital. Your main tasks are:
                
                1. **Extract Information**:
                - If they upload their medical report then you must compulsorily respond them. Asking if they have other additional information they want to share via chat or uploading image in sidebar.
                - Gather key information from the patient's conversation and their medical report (provided in image form).
                - Use this information to respond when doctors inquire about the patient's medical details.

                2. **Respond to Patient Queries**:
                - Answer the patient's questions related to their medical report or any other medical-related queries.
                - Ensure your responses are relevant and informative.

                **Storage of Patient Information**:
                - Store patient details in MongoDB in dictionary format. 
                - The patient's full name (you donot need to ask this, it is already available after user has logged in to the system) will be the main key, with other details stored as key-value pairs.

                **Response Format**:
                - For each response, provide two components:
                    1. The answer to the user's query.
                    2. Any new important information about the patient you gathered.

                - Format each response like this:
                ```json
                {"patient_response": "Your answer to the query", "information_to_store": "The patient's information", "chat_complete": "Yes/No"}
                ```

                **Conversation Continuation**:
                - After each response, ask if the patient has additional information.
                - If they indicate they have no further details to share with you , set `"chat_complete": "Yes"` immediately. Donot ask further questions. Wish them something good like good day. Otherwise, if they have further information to share then keep it as `"chat_complete": "No"`.
                """
            }
        ]
    # Display previous messages if there are any
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                for content in message["content"]:
                    # Check if content is a dictionary before accessing its keys
                    if isinstance(content, dict):
                        if content.get("type") == "text":
                            st.write(content["text"])
                        elif content.get("type") == "image_url":
                            st.image(content["image_url"]["url"])
                        elif content.get("type") == "audio_file":
                            st.audio(content["audio_file"])
                    else:
                        # Handle case where content is not a dictionary (e.g., a string)
                        st.write(content)


    with st.sidebar:
        def reset_conversation():
            if "messages" in st.session_state and len(st.session_state.messages) > 0:
                st.session_state.pop("messages", None)

        st.button("🗑️ Reset conversation", on_click=reset_conversation)

        st.divider()

        st.write("### **🖼️ Add an image:**")

        def add_image_to_messages():
            if st.session_state.uploaded_img or st.session_state.camera_img:
                img_type = st.session_state.uploaded_img.type if st.session_state.uploaded_img else "image/jpeg"
                raw_img = Image.open(st.session_state.uploaded_img or st.session_state.camera_img)
                img = get_image_base64(raw_img)
                
                # Add image to session messages
                st.session_state.messages.append({
                    "role": "user",
                    "content": [{
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{img}"}
                    }]
                })
                
                # Immediately trigger the LLM response after the image is added
                with st.chat_message("assistant"):
                    stream_llm_response()


        cols_img = st.columns(2)

        with cols_img[0]:
            with st.popover("📁 Upload"):
                st.file_uploader(
                    "Upload an image",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=False,
                    key="uploaded_img",
                    on_change=add_image_to_messages,
                )

        with cols_img[1]:
            with st.popover("📸 Camera"):
                activate_camera = st.checkbox("Activate camera")
                if activate_camera:
                    st.camera_input(
                        "Take a picture",
                        key="camera_img",
                        on_change=add_image_to_messages,
                    )

        # Audio Upload
        st.write("### **🎤 Add an audio:**")
        audio_prompt = None
        audio_file_added = False

        if "prev_speech_hash" not in st.session_state:
            st.session_state.prev_speech_hash = None

        speech_input = audio_recorder("Press to talk:", icon_size="3x", neutral_color="#6ca395")

        if speech_input and st.session_state.prev_speech_hash != hash(speech_input):
            st.session_state.prev_speech_hash = hash(speech_input)

            audio_id = random.randint(100000, 999999)
            with open(f"audio_{audio_id}.wav", "wb") as f:
                f.write(speech_input)

            st.session_state.messages.append({
                "role": "user",
                "content": [{
                    "type": "audio_file",
                    "audio_file": f"audio_{audio_id}.wav",
                }]
            })

            audio_file_added = True

    # Chat input
    if prompt := st.chat_input("Hi! Ask me anything...") or audio_prompt or audio_file_added:
        if not audio_file_added:
            st.session_state.messages.append({
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt or audio_prompt,
                }]
            })

            # Display new message
            with st.chat_message("user"):
                st.markdown(prompt)
        else:
            # Display audio file
            with st.chat_message("user"):
                st.audio(f"audio_{audio_id}.wav")

        with st.chat_message("assistant"):
            stream_llm_response()

if __name__ == '__main__':
    main()

