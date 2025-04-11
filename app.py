import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

from data_handler import load_data, save_data
from matching_engine import find_matching_process
from visualization import create_vacancy_chart, create_process_distribution

# Set page config
st.set_page_config(
    page_title="Employee-Process Matcher",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state variables
if 'process_data' not in st.session_state:
    st.session_state.process_data = None
if 'show_add_employee' not in st.session_state:
    st.session_state.show_add_employee = False

# Title and description
st.title("Employee-Process Matcher")
st.markdown("""
This application helps match employees to appropriate processes based on their 
potential and communication skills, while tracking process vacancies.
""")

# Sidebar for data upload and controls
with st.sidebar:
    st.header("Data Management")
    
    upload_tab, download_tab = st.tabs(["Upload Data", "Download Data"])
    
    with upload_tab:
        uploaded_file = st.file_uploader("Upload Process Data (Excel/CSV)", type=['xlsx', 'csv'])
        
        if uploaded_file is not None:
            try:
                st.session_state.process_data = load_data(uploaded_file)
                st.success(f"Successfully loaded {len(st.session_state.process_data)} processes!")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
    
    with download_tab:
        if st.session_state.process_data is not None:
            buffer = BytesIO()
            st.session_state.process_data.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download Process Data",
                data=buffer,
                file_name="process_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.divider()
    
    if st.session_state.process_data is not None:
        st.button("Add New Employee", 
                 on_click=lambda: setattr(st.session_state, 'show_add_employee', True),
                 use_container_width=True)

# Main content area
if st.session_state.process_data is None:
    st.info("Please upload a process data file to get started.")
    
    # Show expected data format
    st.subheader("Expected Data Format")
    sample_data = pd.DataFrame({
        'Process_Name': ['Sales Support', 'Customer Service', 'Technical Support', 'Account Management'],
        'Potential': ['Sales', 'Service', 'Support', 'Consultation'],
        'Communication': ['Good', 'Very Good', 'Good', 'Excellent'],
        'Vacancy': [5, 3, 4, 2]
    })
    st.dataframe(sample_data, use_container_width=True)
    
else:
    # Display process data
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Process Data")
        
        # Filter controls
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            potential_filter = st.multiselect(
                "Filter by Potential",
                options=['All'] + sorted(st.session_state.process_data['Potential'].unique().tolist()),
                default='All'
            )
        
        with filter_col2:
            communication_filter = st.multiselect(
                "Filter by Communication",
                options=['All'] + sorted(st.session_state.process_data['Communication'].unique().tolist()),
                default='All'
            )
        
        # Apply filters
        filtered_data = st.session_state.process_data.copy()
        
        if potential_filter and 'All' not in potential_filter:
            filtered_data = filtered_data[filtered_data['Potential'].isin(potential_filter)]
            
        if communication_filter and 'All' not in communication_filter:
            filtered_data = filtered_data[filtered_data['Communication'].isin(communication_filter)]
        
        # Display filtered data
        st.dataframe(filtered_data, use_container_width=True)
    
    with col2:
        st.subheader("Vacancy Overview")
        
        # Create a vacancy chart
        fig = create_vacancy_chart(st.session_state.process_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a potential distribution chart
        fig2 = create_process_distribution(st.session_state.process_data)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Add new employee form
    if st.session_state.show_add_employee:
        st.divider()
        st.subheader("Add New Employee")
        
        with st.form("employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_name = st.text_input("Employee Name")
                potential = st.selectbox(
                    "Potential",
                    options=['Sales', 'Consultation', 'Service', 'Support']
                )
            
            with col2:
                communication = st.selectbox(
                    "Communication",
                    options=['Excellent', 'Very Good', 'Good']
                )
            
            submitted = st.form_submit_button("Find Matching Process")
            
            if submitted:
                if not employee_name:
                    st.error("Please enter an employee name")
                else:
                    # Find matching process
                    matching_process = find_matching_process(
                        st.session_state.process_data,
                        potential,
                        communication
                    )
                    
                    if matching_process is not None:
                        st.success(f"Match found! {employee_name} can be assigned to: {matching_process['Process_Name']}")
                        
                        # Update vacancy
                        process_idx = st.session_state.process_data[
                            st.session_state.process_data['Process_Name'] == matching_process['Process_Name']
                        ].index[0]
                        
                        st.session_state.process_data.at[process_idx, 'Vacancy'] -= 1
                        
                        # Display the updated process
                        st.dataframe(st.session_state.process_data.iloc[[process_idx]], use_container_width=True)
                    else:
                        st.error("No Match Found - No process matches these skills or all matching processes have 0 vacancies.")
        
        # Button to close the form
        if st.button("Close Form"):
            st.session_state.show_add_employee = False
            st.rerun()
