import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import sys

# IMPORTANT: For local development, force file-based database
# This prevents SQLite thread issues with in-memory databases
os.environ['IS_STREAMLIT_CLOUD'] = 'false'

# Print environment variables for debugging
print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith('STREAMLIT') or key == 'PORT' or key == 'IS_STREAMLIT_CLOUD':
        print(f"  {key}={value}")

from data_handler import load_data, save_data
from matching_engine import find_matching_process
from visualization import create_vacancy_chart, create_process_distribution
import database as db

# Initialize the database before doing anything else
db.init_db()

# Set page config
st.set_page_config(
    page_title="Employee-Process Matcher",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state variables
if 'process_data' not in st.session_state:
    # Try to load from database first
    process_data = db.load_processes_from_db()
    if process_data is not None:
        st.session_state.process_data = process_data
    else:
        st.session_state.process_data = None
    
if 'show_add_employee' not in st.session_state:
    st.session_state.show_add_employee = False
    
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
    
if 'show_find_employee' not in st.session_state:
    st.session_state.show_find_employee = False
    
if 'employee_to_edit' not in st.session_state:
    st.session_state.employee_to_edit = None
    
if 'show_reset_db' not in st.session_state:
    st.session_state.show_reset_db = False
    
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0
    
if 'success_message' not in st.session_state:
    st.session_state.success_message = ""

# Function to force refresh data from database
def refresh_data():
    """Force a complete refresh of data from the database"""
    # Clean the database first
    db.purge_deleted_emails()
    
    # Clear and reload process data
    st.session_state.process_data = None
    st.session_state.process_data = db.load_processes_from_db()
    
    # Increment refresh counter to trigger reactive reloads
    st.session_state.refresh_counter += 2
    
    # Clear any stale success messages
    st.session_state.success_message = ""
    
    print("Data refreshed from database!")

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
                
                # Save to database
                db.save_processes_to_db(st.session_state.process_data)
                
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
        col1, col2 = st.columns(2)
        with col1:
            st.button("Add New Employee", 
                     on_click=lambda: setattr(st.session_state, 'show_add_employee', True),
                     use_container_width=True)
        with col2:
            st.button("View History", 
                     on_click=lambda: setattr(st.session_state, 'show_history', True),
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
    
    # Option to use sample data
    if st.button("Use Sample Data", type="primary"):
        try:
            sample_path = "sample_data/sample_processes.csv"
            sample_df = pd.read_csv(sample_path)
            st.session_state.process_data = sample_df
            
            # Save to database
            db.save_processes_to_db(sample_df)
            
            st.success(f"Sample data loaded successfully with {len(sample_df)} processes!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample data: {str(e)}")
    
else:
    # CRITICAL: Always reload fresh data to ensure we have the latest vacancy counts
    # We're forcing a complete reload from the database every time
    st.session_state.process_data = db.load_processes_from_db()
    st.session_state.refresh_counter += 1
    
    # Display any stored success messages
    if 'success_message' in st.session_state and st.session_state.success_message:
        st.success(st.session_state.success_message)
        # Clear the message after displaying it
        st.session_state.success_message = ""
        # Force a reload of the page to ensure fresh data
        if st.session_state.success_message and ('added' in st.session_state.success_message.lower() or 'deleted' in st.session_state.success_message.lower() or 'updated' in st.session_state.success_message.lower()):
            st.session_state.refresh_counter += 1
            st.rerun()
    
    # Display process data with real-time vacancy counts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Process Data")
        
        # Add a refresh button to force UI updates
        if st.button("↻ Refresh Data", key=f"refresh_button_{st.session_state.refresh_counter}"):
            # Complete forced reload from database
            refresh_data()
            st.success("Data refreshed from database!")
            st.rerun()
        
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
        
        # Display filtered data - add key based on refresh counter to force updates
        st.dataframe(filtered_data, use_container_width=True)
    
    with col2:
        st.subheader("Vacancy Overview")
        
        # Create a vacancy chart - add key based on refresh counter to force updates
        fig = create_vacancy_chart(st.session_state.process_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a potential distribution chart
        fig2 = create_process_distribution(st.session_state.process_data)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Add sidebar button for find employee
    if st.session_state.process_data is not None:
        st.sidebar.divider()
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.button("Find/Edit Employee", 
                    on_click=lambda: setattr(st.session_state, 'show_find_employee', True),
                    use_container_width=True)
                    
        with col2:
            st.button("Reset Database", type="primary",
                    on_click=lambda: setattr(st.session_state, 'show_reset_db', True),
                    use_container_width=True)
    
    # Add new employee form
    if st.session_state.show_add_employee:
        st.divider()
        st.subheader("Add New Employee")
        
        # Use session state to store employee data temporarily
        if 'temp_employee_name' not in st.session_state:
            st.session_state.temp_employee_name = ""
        if 'temp_employee_email' not in st.session_state:
            st.session_state.temp_employee_email = ""
        if 'temp_potential' not in st.session_state:
            st.session_state.temp_potential = "Sales"
        if 'temp_communication' not in st.session_state:
            st.session_state.temp_communication = "Excellent"
        if 'show_process_list' not in st.session_state:
            st.session_state.show_process_list = False
            
        # Input form for employee details
        with st.form("employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.temp_employee_name = st.text_input("Employee Name", value=st.session_state.temp_employee_name)
                st.session_state.temp_employee_email = st.text_input("Employee Email (unique)", value=st.session_state.temp_employee_email)
                st.session_state.temp_potential = st.selectbox(
                    "Potential",
                    options=['Sales', 'Consultation', 'Service', 'Support'],
                    index=['Sales', 'Consultation', 'Service', 'Support'].index(st.session_state.temp_potential)
                )
            
            with col2:
                st.session_state.temp_communication = st.selectbox(
                    "Communication",
                    options=['Excellent', 'Very Good', 'Good'],
                    index=['Excellent', 'Very Good', 'Good'].index(st.session_state.temp_communication)
                )
            
            submitted = st.form_submit_button("Find Matching Processes")
            
            if submitted:
                if not st.session_state.temp_employee_name or not st.session_state.temp_employee_email:
                    st.error("Please enter both employee name and email")
                else:
                    st.session_state.show_process_list = True
        
        # Show process list outside of form (so buttons will work)
        if st.session_state.show_process_list:
            employee_name = st.session_state.temp_employee_name
            employee_email = st.session_state.temp_employee_email
            potential = st.session_state.temp_potential
            communication = st.session_state.temp_communication
            
            # Get suggested processes sorted by vacancy (high to low)
            matching_processes = db.get_process_suggestions(potential, communication)
            
            if not matching_processes.empty:
                st.success(f"Found {len(matching_processes)} matching processes for {employee_name}!")
                
                # Display all matching processes
                st.subheader("Available Matching Processes (Sorted by Vacancy)")
                st.dataframe(matching_processes, use_container_width=True)
                
                # Display processes with an 'Add' button for each process
                st.subheader("Available Matching Processes (Select one to assign)")
                
                # Create a DataFrame with an additional "Action" column
                # We'll use this custom dataframe view with buttons
                processes_with_actions = matching_processes.copy()
                
                # Display the processes
                for i, row in processes_with_actions.iterrows():
                    process_name = row['Process_Name']
                    vacancy = row['Vacancy']
                    potential_val = row['Potential']
                    comm_val = row['Communication']
                    
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{process_name}** (Vacancy: {vacancy})")
                    with col2:
                        st.write(f"Potential: {potential_val}")
                    with col3:
                        st.write(f"Communication: {comm_val}")
                    with col4:
                        if st.button(f"Add to {process_name}", key=f"add_{i}"):
                            # Add employee to the database with selected process
                            success, message = db.add_employee(
                                employee_name, 
                                employee_email,
                                potential, 
                                communication, 
                                process_name
                            )
                            
                            if success:
                                # Reload process data to reflect updated vacancies
                                # Force full reload to prevent caching issues
                                db.purge_deleted_emails()  # Clean database
                                st.session_state.process_data = None  # Clear cache
                                st.session_state.process_data = db.load_processes_from_db()  # Load fresh
                                st.session_state.refresh_counter += 2  # Force UI update
                                
                                # Store success message in session state for display after rerun
                                st.session_state.success_message = message
                                st.session_state.employee_to_edit = None
                                
                                # Force rerun to update all UI elements
                                st.rerun()
                            else:
                                st.error(message)
                    
                    st.divider()
            else:
                st.error("No matching processes found with available vacancies")
                
                # Option to add employee without process assignment
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.warning("No matching processes available with vacancies")
                with col2:
                    if st.button("Add Without Assignment"):
                        success, message = db.add_employee(
                            employee_name, 
                            employee_email,
                            potential, 
                            communication
                        )
                        
                        if success:
                            st.success("Employee added without process assignment")
                            st.session_state.show_process_list = False
                            st.rerun()
                        else:
                            st.error(message)
        
        # Button to close the form
        if st.button("Close Add Form"):
            st.session_state.show_add_employee = False
            st.rerun()
            
    # Find/Edit Employee Section
    if st.session_state.show_find_employee:
        st.divider()
        st.subheader("Find/Edit Employee")
        
        # Search by email
        email_search = st.text_input("Enter Employee Email to Find")
        
        search_clicked = st.button("Search for Employee")
        
        if email_search and search_clicked:
            try:
                employee = db.find_employee_by_email(email_search)
                
                if employee:
                    st.success(f"Found employee: {employee['name']}")
                    
                    # Display employee info
                    employee_info = pd.DataFrame([{
                        'Name': employee['name'],
                        'Email': employee['email'],
                        'Potential': employee['potential'],
                        'Communication': employee['communication'],
                        'Process': employee['process_name'] or 'Not Assigned'
                    }])
                    
                    st.dataframe(employee_info, use_container_width=True)
                    
                    # Edit and Delete buttons
                    edit_col, delete_col = st.columns(2)
                    
                    with edit_col:
                        if st.button("Edit Employee"):
                            st.session_state.employee_to_edit = employee
                    
                    with delete_col:
                        if st.button("Delete Employee", type="primary"):
                            if st.checkbox("I confirm I want to delete this employee"):
                                success, message = db.delete_employee(employee['id'])
                                if success:
                                    # Reload process data to reflect updated vacancies
                                    # Force full reload to prevent caching issues
                                    db.purge_deleted_emails()  # Clean database
                                    st.session_state.process_data = None  # Clear cache
                                    st.session_state.process_data = db.load_processes_from_db()  # Load fresh
                                    st.session_state.refresh_counter += 2  # Force UI update
                                    
                                    # Double-check deletion was successful
                                    check_employee = db.find_employee_by_email(employee['email'])
                                    if check_employee:
                                        st.error(f"Error: Employee with email {employee['email']} still found in database!")
                                    else:
                                        # Store success message in session state for display after rerun
                                        st.session_state.success_message = message
                                        
                                        # Force rerun to update all UI elements
                                        st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.error(f"No employee found with email: {email_search}")
            except Exception as e:
                st.error(f"Error while searching: {str(e)}")
        
        # Edit employee form
        if st.session_state.employee_to_edit:
            employee = st.session_state.employee_to_edit
            
            st.divider()
            st.subheader(f"Edit {employee['name']}")
            
            with st.form("edit_employee_form"):
                edit_col1, edit_col2 = st.columns(2)
                
                with edit_col1:
                    new_name = st.text_input("Name", value=employee['name'])
                    new_email = st.text_input("Email", value=employee['email'])
                    new_potential = st.selectbox(
                        "Potential",
                        options=['Sales', 'Consultation', 'Service', 'Support'],
                        index=['Sales', 'Consultation', 'Service', 'Support'].index(employee['potential'])
                    )
                
                with edit_col2:
                    new_communication = st.selectbox(
                        "Communication",
                        options=['Excellent', 'Very Good', 'Good'],
                        index=['Excellent', 'Very Good', 'Good'].index(employee['communication'])
                    )
                    
                    # Get all processes
                    processes = []
                    if st.session_state.process_data is not None:
                        processes = st.session_state.process_data['Process_Name'].tolist()
                    processes.insert(0, 'None')
                    
                    # Determine the index for the current process
                    current_idx = 0
                    if employee['process_name']:
                        try:
                            current_idx = processes.index(employee['process_name'])
                        except ValueError:
                            current_idx = 0
                    
                    new_process = st.selectbox(
                        "Assigned Process",
                        options=processes,
                        index=current_idx
                    )
                
                if new_process == 'None':
                    new_process = None
                
                update_submitted = st.form_submit_button("Update Employee")
                
                if update_submitted:
                    success, message = db.update_employee(
                        employee['id'],
                        new_name,
                        new_email,
                        new_potential,
                        new_communication,
                        new_process
                    )
                    
                    if success:
                        # Reload the process data to reflect any vacancy changes
                        # Force full reload to prevent caching issues
                        db.purge_deleted_emails()  # Clean database
                        st.session_state.process_data = None  # Clear cache
                        st.session_state.process_data = db.load_processes_from_db()  # Load fresh
                        st.session_state.refresh_counter += 2  # Force UI update
                        
                        # Store success message in session state for display after rerun
                        st.session_state.success_message = message
                        st.session_state.employee_to_edit = None
                        
                        # Force rerun to update all UI elements
                        st.rerun()
                    else:
                        st.error(message)
        
        # Button to close the form
        if st.button("Close Find/Edit Form"):
            st.session_state.show_find_employee = False
            st.session_state.employee_to_edit = None
            st.rerun()
    
    # Reset Database confirmation dialog
    if st.session_state.show_reset_db:
        st.divider()
        st.subheader("Reset Database", divider="red")
        st.warning("⚠️ This will permanently delete all employee and process data and reset the database to its initial state. This action cannot be undone!")
        
        confirm_col1, confirm_col2 = st.columns([3, 1])
        with confirm_col1:
            confirmation = st.text_input("Type 'RESET' to confirm database reset:")
        with confirm_col2:
            if st.button("Reset Database", type="primary") and confirmation == "RESET":
                # Reset the database
                db.reset_database()
                
                # Clear session state
                st.session_state.process_data = None
                st.session_state.show_add_employee = False
                st.session_state.show_find_employee = False 
                st.session_state.show_history = False
                st.session_state.show_process_list = False
                st.session_state.employee_to_edit = None
                st.session_state.show_reset_db = False
                
                st.success("Database has been reset successfully!")
                st.rerun()
            elif st.button("Cancel Reset"):
                st.session_state.show_reset_db = False
                st.rerun()
    
    # History view
    if st.session_state.show_history:
        st.divider()
        st.subheader("Employee Assignment History")
        
        # Get employee history from database
        employee_data = db.get_employee_assignments()
        
        if employee_data.empty:
            st.info("No employee assignments found in the database.")
        else:
            # Format date column
            if 'assigned_at' in employee_data.columns:
                employee_data['assigned_at'] = pd.to_datetime(
                    employee_data['assigned_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Display the assignments
            st.dataframe(employee_data, use_container_width=True)
            
            # Removed assignment summary as requested
        
        # Button to close the view
        if st.button("Close History"):
            st.session_state.show_history = False
            st.rerun()
