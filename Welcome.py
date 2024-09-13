import streamlit as st

# Remove the sidebar (comment out this section if you're fine with manual routing)
st.set_page_config(layout="centered",
            page_icon="⛑️",
            page_title="MediSched"
)  # Optional: makes the page centered

# Main homepage
st.title("Welcome to the Hospital Management System")
st.write("Please select your role to proceed to login:")

# Create a select box for navigation
option = st.selectbox(
    "Choose your role",
    ("Select...", "Patient_Appointment", "Doctor", "Admin", "Additional_Info_SignIn")
)

# Logic to redirect users based on role selection
if option == "Patient_Appointment":
    st.write("Redirecting to Patient login...")
    st.switch_page(page="/Users/sanimpandey/Desktop/lang/pages/patient😷.py")
    st.experimental_rerun()  # Reload the app with the new query param

elif option == "Doctor":
    st.write("Redirecting to Doctor login...")
    st.switch_page(page="/Users/sanimpandey/Desktop/lang/pages/doctor🧑‍⚕️.py")
    st.experimental_rerun()

elif option == "Admin":
    st.write("Redirecting to Admin login...")
    st.switch_page(page="/Users/sanimpandey/Desktop/lang/pages/admin🧑‍💼.py")
    st.experimental_rerun()

elif option == "Additional_Info_SignIn":
    st.write("Redirecting to Additional Info login...")
    st.switch_page(page="/Users/sanimpandey/Desktop/lang/pages/signin✅_for_additional.py")
    st.experimental_rerun()




