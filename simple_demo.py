import streamlit as st

# Set page config
st.set_page_config(
    page_title="Process Potential Tracker",
    page_icon="🔍"
)

# Title
st.title("Process Potential Tracker - Demo")

# Description
st.markdown("""
This is a simple demonstration of the Process Potential Tracker application.

The full application helps match employees to appropriate processes based on 
their potential and communication skills, while tracking process vacancies.
""")

# Sample data display
st.subheader("Sample Process Data")

# Create a simple table
data = {
    "Process Name": ["TVS CC", "CW Massbrand", "Bajaj Online Booking"],
    "Potential": ["Service", "Consultation", "Sales"],
    "Communication": ["Good", "Excellent", "Good"],
    "Vacancy": [20, 9, 1]
}

# Display as a table
st.table(data)

# Footer
st.caption("Created by Shadab34 - GitHub: https://github.com/Shadab34/ProcessPotentialTracker") 