import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

from data_handler import load_data, save_data
from matching_engine import find_matching_process
from visualization import create_vacancy_chart, create_process_distribution
import database as db

# Set page config
st.set_page_config(
    page_title="Employee-Process Matcher",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state variables
if 'process_data' not in st.session_state:
    # Try to load from database first
    st.session_state.process_data = db.load_processes_from_db()
    
if 'show_add_employee' not in st.session_state:
    st.session_state.show_add_employee = False
    
if 'show_history' not in st.session_state:
    st.session_state.show_history = False

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
                        process_name = matching_process['Process_Name']
                        st.success(f"Match found! {employee_name} can be assigned to: {process_name}")
                        
                        # Update vacancy in session state
                        process_idx = st.session_state.process_data[
                            st.session_state.process_data['Process_Name'] == process_name
                        ].index[0]
                        
                        st.session_state.process_data.at[process_idx, 'Vacancy'] -= 1
                        
                        # Update database
                        db.update_process_vacancy(process_name, -1)
                        
                        # Add employee to database
                        db.add_employee(employee_name, potential, communication, process_name)
                        
                        # Display the updated process
                        st.dataframe(st.session_state.process_data.iloc[[process_idx]], use_container_width=True)
                    else:
                        # Still record the employee, but with no process assignment
                        db.add_employee(employee_name, potential, communication)
                        st.error("No Match Found - No process matches these skills or all matching processes have 0 vacancies.")
        
        # Button to close the form
        if st.button("Close Form"):
            st.session_state.show_add_employee = False
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
            
            # Get summary statistics
            history_summary = db.get_assignment_history()
            
            if not history_summary.empty:
                st.subheader("Assignment Summary by Date")
                
                # Create a bar chart of assignments by date
                fig = px.bar(
                    history_summary,
                    x='assignment_date',
                    y=['successful_matches', 'no_matches'],
                    title='Employee Assignments by Date',
                    labels={'value': 'Number of Employees', 'assignment_date': 'Date'},
                    barmode='group',
                    color_discrete_map={
                        'successful_matches': 'green',
                        'no_matches': 'red'
                    }
                )
                
                fig.update_layout(legend_title_text='Result')
                st.plotly_chart(fig, use_container_width=True)
        
        # Button to close the view
        if st.button("Close History"):
            st.session_state.show_history = False
            st.rerun()
