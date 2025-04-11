import sqlite3
import pandas as pd
import os
from datetime import datetime

# Database file path
DB_PATH = 'employee_process_matcher.db'

def init_db():
    """Initialize the database with required tables if they don't exist."""
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
        potential TEXT NOT NULL,
        communication TEXT NOT NULL,
        process_id INTEGER,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (process_id) REFERENCES processes (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def save_processes_to_db(process_data):
    """
    Save processes data to database
    
    Args:
        process_data: DataFrame containing process information
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Clear existing processes
    conn.execute("DELETE FROM processes")
    
    # Insert new processes
    for _, row in process_data.iterrows():
        conn.execute(
            "INSERT INTO processes (process_name, potential, communication, vacancy) VALUES (?, ?, ?, ?)",
            (row['Process_Name'], row['Potential'], row['Communication'], row['Vacancy'])
        )
    
    conn.commit()
    conn.close()

def load_processes_from_db():
    """
    Load processes from database
    
    Returns:
        DataFrame: Processes data or None if database is empty
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Check if we have any processes
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM processes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        conn.close()
        return None
    
    # Load processes into DataFrame
    df = pd.read_sql("SELECT process_name as Process_Name, potential as Potential, "
                     "communication as Communication, vacancy as Vacancy FROM processes", conn)
    
    conn.close()
    return df

def update_process_vacancy(process_name, change):
    """
    Update vacancy count for a process
    
    Args:
        process_name: Name of the process to update
        change: Amount to change vacancy by (negative to decrease)
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current vacancy
    cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (process_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    current_vacancy = result[0]
    new_vacancy = current_vacancy + change
    
    # Ensure vacancy doesn't go below 0
    if new_vacancy < 0:
        conn.close()
        return False
    
    # Update vacancy
    cursor.execute("UPDATE processes SET vacancy = ? WHERE process_name = ?", 
                   (new_vacancy, process_name))
    
    conn.commit()
    conn.close()
    return True

def add_employee(name, potential, communication, process_name=None):
    """
    Add a new employee to the database
    
    Args:
        name: Employee name
        potential: Employee potential
        communication: Employee communication level
        process_name: Name of assigned process (if any)
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    process_id = None
    if process_name:
        # Get process ID
        cursor.execute("SELECT id FROM processes WHERE process_name = ?", (process_name,))
        result = cursor.fetchone()
        if result:
            process_id = result[0]
    
    # Add employee
    cursor.execute(
        "INSERT INTO employees (name, potential, communication, process_id) VALUES (?, ?, ?, ?)",
        (name, potential, communication, process_id)
    )
    
    conn.commit()
    conn.close()
    return True

def get_employee_assignments():
    """
    Get all employee assignments
    
    Returns:
        DataFrame: Employee assignments data
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT e.id, e.name, e.potential, e.communication, 
           p.process_name, e.assigned_at
    FROM employees e
    LEFT JOIN processes p ON e.process_id = p.id
    ORDER BY e.assigned_at DESC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def get_assignment_history():
    """
    Get history of assignments by date
    
    Returns:
        DataFrame: Assignment history with counts by date
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        date(assigned_at) as assignment_date,
        COUNT(*) as assignments,
        SUM(CASE WHEN process_id IS NOT NULL THEN 1 ELSE 0 END) as successful_matches,
        SUM(CASE WHEN process_id IS NULL THEN 1 ELSE 0 END) as no_matches
    FROM employees
    GROUP BY date(assigned_at)
    ORDER BY date(assigned_at) DESC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

# Initialize the database on module import
init_db()