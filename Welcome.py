import streamlit as st
from streamlit_lottie import st_lottie
import requests

# Function to load Lottie files
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Page configuration
st.set_page_config(
    layout="wide",
    page_icon="⛑️",
    page_title="MediSched"
)

# Custom CSS
st.markdown("""
<style>
    body {
        color: #333333;
        background-color: #FFFFFF;
    }
    .stApp {
        background-color: #FFFFFF;
    }
    .stSelectbox {
        color: #333333;
    }
    .stSelectbox > div > div {
        background-color: #F0F0F0;
    }
    .stButton > button {
        color: #FFFFFF;
        background-color: #FF4B4B;
        border-radius: 20px;
    }
    .stButton > button:hover {
        background-color: #FF7171;
    }
    .css-10trblm {
        color: #333333;
    }
    .css-1offfwp p {
        color: #333333;
    }
    .instruction-text {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Load Lottie animation of a doctor
lottie_doctor = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_jcikwtux.json")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.title("Welcome to HospiGent")
    
    # Use custom HTML to apply the new style
    st.markdown('<p class="instruction-text">Please select your role to proceed to login:</p>', unsafe_allow_html=True)
    
    st.write("Patients can schedule their appointments through patient agent. Doctors can use doctor agent. If you are an administrator, please use admin agent.")

    # Create a select box for navigation
    option = st.selectbox(
        "Choose your role",
        ("Select...", "Patient_Appointment", "Doctor", "Admin", "Additional_Info_SignIn")
    )

    # Logic to redirect users based on role selection
    if option != "Select...":
        st.write(f"Redirecting to {option} login...")
        if option == "Patient_Appointment":
            st.switch_page(page="pages/patient.py")
        elif option == "Doctor":
            st.switch_page(page="pages/doctor🧑‍⚕️.py")
        elif option == "Admin":
            st.switch_page(page="pages/admin🧑‍💼.py")
        elif option == "Additional_Info_SignIn":
            st.switch_page(page="pages/signin✅_for_additional.py")
        st.experimental_rerun()

with col2:
    st_lottie(lottie_doctor, height=400, key="doctor")