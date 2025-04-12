import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import sqlite3

# Ensure we use a file-based database for local development
os.environ['IS_STREAMLIT_CLOUD'] = 'false'
DB_PATH = 'employee_process_matcher.db'

# Set page config
st.set_page_config(
    page_title="Employee-Process Matcher",
    page_icon="🔍",
    layout="wide"
)

# Database setup
def init_db():
    """Initialize the database with required tables if they don't exist."""
    # Remove existing database if it exists
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except:
            st.error(f"Could not remove existing database at {DB_PATH}")
            return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create process table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        process_name TEXT NOT NULL,
        potential TEXT NOT NULL,
        communication TEXT NOT NULL,
        vacancy INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create employees table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        potential TEXT NOT NULL,
        communication TEXT NOT NULL,
        process_id INTEGER,
        process_name TEXT,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (process_id) REFERENCES processes (id)
    )
    ''')
    
    # Sample process data
    sample_processes = [
        ('Sales Support', 'Sales', 'Good', 5),
        ('Customer Service', 'Service', 'Very Good', 3),
        ('Technical Support', 'Support', 'Good', 4),
        ('Account Management', 'Consultation', 'Excellent', 2),
        ('TVS CC', 'Service', 'Good', 20),
        ('CW Massbrand', 'Consultation', 'Excellent', 9),
        ('CW Inbound', 'Service', 'Good', 8),
        ('Bgauss CC', 'Service', 'Good', 3),
        ('Ather CC', 'Service', 'Good', 2)
    ]
    
    # Insert sample processes
    for process in sample_processes:
        cursor.execute(
            "INSERT INTO processes (process_name, potential, communication, vacancy) VALUES (?, ?, ?, ?)",
            process
        )
    
    conn.commit()
    conn.close()
    return True

def load_processes():
    """Load processes from database"""
    conn = sqlite3.connect(DB_PATH)
    
    # Load processes into DataFrame
    df = pd.read_sql("""
        SELECT 
            process_name as Process_Name, 
            potential as Potential, 
            communication as Communication, 
            vacancy as Vacancy 
        FROM processes
        ORDER BY vacancy DESC, process_name ASC
    """, conn)
    
    conn.close()
    return df

def create_vacancy_chart(process_data):
    """Create a horizontal bar chart showing vacancies for each process"""
    # Sort by vacancy count (descending)
    sorted_data = process_data.sort_values('Vacancy', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        sorted_data,
        y='Process_Name',
        x='Vacancy',
        color='Vacancy',
        orientation='h',
        color_continuous_scale='plasma',
        title='Process Vacancies',
        text='Vacancy',
        hover_data={'Process_Name': True, 'Vacancy': True, 'Potential': True, 'Communication': True}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Available Vacancies',
        yaxis_title='Process Name',
        height=min(400, 100 + len(process_data) * 30),
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(title="Vacancies"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Make the text more readable and bars more vibrant
    fig.update_traces(
        textposition='outside', 
        textfont_size=10,
        marker_line_width=1,
        marker_line_color='rgba(0,0,0,0.3)',
        opacity=0.9
    )
    
    return fig

def create_process_distribution(process_data):
    """Create a pie chart showing distribution of processes by potential"""
    # Group by potential type and count
    potential_counts = process_data.groupby('Potential')['Process_Name'].nunique().reset_index(name='count')
    
    # Calculate percentages for display
    total = potential_counts['count'].sum()
    potential_counts['percentage'] = (potential_counts['count'] / total * 100).round(1)
    potential_counts['label'] = potential_counts['Potential'] + ' (' + potential_counts['percentage'].astype(str) + '%)'
    
    # Create pie chart with custom colors
    colors = px.colors.qualitative.Bold
    
    fig = px.pie(
        potential_counts,
        values='count',
        names='label',
        title='Processes by Potential Type',
        color_discrete_sequence=colors
    )
    
    # Update layout and text
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Update text inside pie chart
    fig.update_traces(
        textinfo='percent+label',
        textposition='inside',
        textfont=dict(size=12, color='white'),
        marker=dict(line=dict(color='#000000', width=1)),
        pull=[0.05] * len(potential_counts),
        hoverinfo='label+percent+value'
    )
    
    return fig

# Initialize database
if not os.path.exists(DB_PATH):
    if not init_db():
        st.error("Failed to initialize database. Please check permissions.")
        st.stop()

# Title and description
st.title("Employee-Process Matcher")
st.markdown("""
This application helps match employees to appropriate processes based on their 
potential and communication skills, while tracking process vacancies.
""")

# Get process data
process_data = load_processes()

# Display data
if process_data is not None and not process_data.empty:
    # Display process data with real-time vacancy counts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Process Data")
        
        # Filter controls
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            potential_filter = st.multiselect(
                "Filter by Potential",
                options=['All'] + sorted(process_data['Potential'].unique().tolist()),
                default='All'
            )
        
        with filter_col2:
            communication_filter = st.multiselect(
                "Filter by Communication",
                options=['All'] + sorted(process_data['Communication'].unique().tolist()),
                default='All'
            )
        
        # Apply filters
        filtered_data = process_data.copy()
        
        if potential_filter and 'All' not in potential_filter:
            filtered_data = filtered_data[filtered_data['Potential'].isin(potential_filter)]
            
        if communication_filter and 'All' not in communication_filter:
            filtered_data = filtered_data[filtered_data['Communication'].isin(communication_filter)]
        
        # Display filtered data
        st.dataframe(filtered_data, use_container_width=True)
    
    with col2:
        st.subheader("Vacancy Overview")
        
        # Create a vacancy chart
        fig = create_vacancy_chart(process_data)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create a potential distribution chart
        fig2 = create_process_distribution(process_data)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.error("No process data found in database. Please reinitialize the database.")
    
    if st.button("Reinitialize Database"):
        if init_db():
            st.success("Database reinitialized. Please refresh the page.")
            st.rerun()

# Footer
st.divider()
st.caption("Employee-Process Matcher | Local Demo Version") 