import sqlite3
import pandas as pd
import os
from datetime import datetime

# Database file path
DB_PATH = 'employee_process_matcher.db'

def init_db():
    """Initialize the database with required tables if they don't exist."""
    # Remove existing database to ensure we have the correct schema
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
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

def add_employee(name, email, potential, communication, process_name=None):
    """
    Add a new employee to the database
    
    Args:
        name: Employee name
        email: Employee email (unique identifier)
        potential: Employee potential
        communication: Employee communication level
        process_name: Name of assigned process (if any)
    
    Returns:
        bool: True if successful, False otherwise
        str: Error message if any
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM employees WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email already exists in the database"
    
    process_id = None
    if process_name:
        # Get process ID
        cursor.execute("SELECT id FROM processes WHERE process_name = ?", (process_name,))
        result = cursor.fetchone()
        if result:
            process_id = result[0]
    
    try:
        # Add employee
        cursor.execute(
            "INSERT INTO employees (name, email, potential, communication, process_id, process_name) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, potential, communication, process_id, process_name)
        )
        
        conn.commit()
        conn.close()
        return True, "Employee added successfully"
    except Exception as e:
        conn.close()
        return False, str(e)

def get_employee_assignments():
    """
    Get all employee assignments
    
    Returns:
        DataFrame: Employee assignments data
    """
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT e.id, e.name, e.email, e.potential, e.communication, 
           e.process_name, e.assigned_at
    FROM employees e
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

def find_employee_by_email(email):
    """
    Find an employee by email
    
    Args:
        email: Employee email to search for
    
    Returns:
        dict: Employee data if found, None otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.potential, e.communication, 
               e.process_id, e.process_name
        FROM employees e
        WHERE e.email = ?
    """, (email,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'name': result[1],
            'email': result[2],
            'potential': result[3],
            'communication': result[4],
            'process_id': result[5],
            'process_name': result[6]
        }
    return None

def update_employee(employee_id, name, email, potential, communication, process_name=None):
    """
    Update an employee's details
    
    Args:
        employee_id: ID of employee to update
        name: New employee name
        email: New employee email
        potential: New employee potential
        communication: New employee communication level
        process_name: New assigned process (if any)
    
    Returns:
        bool: True if successful, False otherwise
        str: Error message if any
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if email already exists for another employee
    cursor.execute("SELECT id FROM employees WHERE email = ? AND id != ?", (email, employee_id))
    if cursor.fetchone():
        conn.close()
        return False, "Email already exists for another employee"
    
    # Get current process assignment to update vacancy if changed
    cursor.execute("SELECT process_name FROM employees WHERE id = ?", (employee_id,))
    result = cursor.fetchone()
    if result:
        old_process = result[0]
    else:
        old_process = None
    
    # Update process vacancy counts if assignment changed
    if old_process != process_name:
        # Increase vacancy for old process if there was one
        if old_process:
            update_process_vacancy(old_process, 1)
        
        # Decrease vacancy for new process if there is one
        if process_name:
            update_process_vacancy(process_name, -1)
    
    # Get process ID for the new process
    process_id = None
    if process_name:
        cursor.execute("SELECT id FROM processes WHERE process_name = ?", (process_name,))
        result = cursor.fetchone()
        if result:
            process_id = result[0]
    
    try:
        # Update employee
        cursor.execute("""
            UPDATE employees 
            SET name = ?, email = ?, potential = ?, communication = ?, 
                process_id = ?, process_name = ?
            WHERE id = ?
        """, (name, email, potential, communication, process_id, process_name, employee_id))
        
        conn.commit()
        conn.close()
        return True, "Employee updated successfully"
    except Exception as e:
        conn.close()
        return False, str(e)

def delete_employee(employee_id):
    """
    Delete an employee and update process vacancy
    
    Args:
        employee_id: ID of employee to delete
    
    Returns:
        bool: True if successful, False otherwise
        str: Message with result
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the employee's process to update vacancy
    cursor.execute("SELECT process_name FROM employees WHERE id = ?", (employee_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Employee not found"
    
    process_name = result[0]
    
    # Delete the employee
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    
    # Update process vacancy if employee was assigned
    if process_name:
        update_process_vacancy(process_name, 1)
    
    conn.commit()
    conn.close()
    return True, f"Employee deleted and process '{process_name}' vacancy updated"

def get_process_suggestions(potential, communication):
    """
    Get process suggestions for an employee, sorted by vacancy (high to low)
    
    Args:
        potential: Employee potential
        communication: Employee communication level
    
    Returns:
        DataFrame: Process suggestions
    """
    conn = sqlite3.connect(DB_PATH)
    
    # Query to get matching processes sorted by vacancy
    query = """
    SELECT process_name as Process_Name, potential as Potential, 
           communication as Communication, vacancy as Vacancy
    FROM processes
    WHERE potential = ? AND communication = ? AND vacancy > 0
    ORDER BY vacancy DESC
    """
    
    df = pd.read_sql(query, conn, params=(potential, communication))
    conn.close()
    
    return df

# Initialize the database on module import
init_db()