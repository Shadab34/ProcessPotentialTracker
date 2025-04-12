import streamlit as st
import os
import pandas as pd
import sqlite3

# Check if we're running in the cloud
is_cloud = os.environ.get('IS_STREAMLIT_CLOUD', False)

# Database setup
def init_connection():
    """Initialize the database connection - use in-memory SQLite in cloud environments"""
    if is_cloud:
        # Use in-memory database for Streamlit Cloud
        conn = sqlite3.connect(':memory:')
        print("Using in-memory database for cloud environment")
    else:
        # Use file-based database for local development
        conn = sqlite3.connect('employee_process_matcher.db')
        print("Using file-based database for local environment")
    return conn

# Initialize sample data for cloud deployment
def init_sample_data():
    """Initialize sample data for cloud deployment"""
    if not is_cloud:
        return
        
    conn = init_connection()
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
    print("Sample data initialized for cloud environment")

# Initialize database connection in session state
def get_connection():
    """Get cached database connection"""
    if 'conn' not in st.session_state:
        st.session_state.conn = init_connection()
    return st.session_state.conn

# Initialize when this module is imported
if is_cloud:
    # Set environment variable for cloud
    os.environ['IS_STREAMLIT_CLOUD'] = 'true'
    # Initialize sample data
    init_sample_data() 