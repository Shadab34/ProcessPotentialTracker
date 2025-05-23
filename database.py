import sqlite3
import pandas as pd
import os
from datetime import datetime
import streamlit as st
import threading

# Check if we're running in the cloud - detect standard cloud environment variables
is_streamlit_cloud = os.environ.get('IS_STREAMLIT_CLOUD') == 'true'
is_cloud_platform = any(key in os.environ for key in ['STREAMLIT_SHARING', 'STREAMLIT_SERVER_PORT', 'PORT', 'DYNO'])
is_cloud = is_streamlit_cloud or is_cloud_platform

# Database file path
# For cloud deployments, use a file path that's within the app's writable directory
if is_cloud:
    DB_PATH = './streamlit_data.db'  # Use a file-based DB even in cloud for persistence
else:
    DB_PATH = 'employee_process_matcher.db'

print(f"Database configuration: Path={DB_PATH}, Cloud mode={is_cloud}")

# Thread-local storage for connections
local = threading.local()

def get_connection():
    """Get a database connection that's safe for the current thread"""
    try:
        # Always create a new connection for better thread safety
        conn = sqlite3.connect(DB_PATH)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        # If we can't connect to the file database, use in-memory as fallback
        conn = sqlite3.connect(':memory:')
        # Initialize schema immediately for in-memory database
        init_schema(conn)
        return conn

def init_schema(conn):
    """Initialize the database schema only (no data)"""
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

def init_db():
    """Initialize the database with required tables if they don't exist."""
    try:
        # Only recreate the database in development mode and if the file exists
        if not is_cloud and os.path.exists(DB_PATH) and os.access(DB_PATH, os.W_OK):
            try:
                os.remove(DB_PATH)
                print(f"Removed existing development database at {DB_PATH}")
            except Exception as e:
                print(f"Could not remove existing database at {DB_PATH}: {str(e)}")
        
        # Get a connection for the current thread
        conn = get_connection()
        cursor = conn.cursor()
        
        # Always ensure the schema exists
        init_schema(conn)
        
        # Check if we need to add sample data
        try:
            cursor.execute("SELECT COUNT(*) FROM processes")
            count = cursor.fetchone()[0]
            
            # If we already have data, no need to add sample data
            if count > 0:
                print(f"Database already contains {count} processes")
                conn.close()
                return
                
        except sqlite3.OperationalError:
            # Table might not exist yet, schema will be initialized above
            pass
        
        # Add sample data
        print("Adding sample data to database")
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
        
        print(f"Database initialized at {DB_PATH} (cloud mode: {is_cloud}, thread: {threading.get_ident()})")
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        # Don't crash the app if database initialization fails
        return None

def save_processes_to_db(process_data):
    """
    Save processes data to database
    
    Args:
        process_data: DataFrame containing process information
    """
    try:
        conn = get_connection()
        
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
        
        print(f"Saved {len(process_data)} processes to database")
        return True
    except Exception as e:
        print(f"Error saving processes to database: {str(e)}")
        return False

def load_processes_from_db():
    """
    Load processes from database
    
    Returns:
        DataFrame: Processes data or None if database is empty
    """
    try:
        # Ensure database is initialized
        init_db()  # Make sure tables exist
        
        # Get a clean connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if we have any processes
        cursor.execute("SELECT COUNT(*) FROM processes")
        count = cursor.fetchone()[0]
        
        if count == 0:
            conn.close()
            print("No processes found in database")
            return None
        
        # Load processes into DataFrame with explicit ORDER BY for consistent results
        df = pd.read_sql("""
            SELECT 
                process_name as Process_Name, 
                potential as Potential, 
                communication as Communication, 
                vacancy as Vacancy 
            FROM processes
            ORDER BY vacancy DESC, process_name ASC
        """, conn)
        
        # Always close connection
        conn.close()
        
        # Debug info for tracking
        print(f"Loaded {len(df)} processes from database")
        if not df.empty:
            print(df[['Process_Name', 'Vacancy']].head(5).to_string())
            
        return df
    except Exception as e:
        print(f"Error loading processes: {str(e)}")
        return None

def update_process_vacancy(process_name, change):
    """
    Update vacancy count for a process - COMPLETELY REBUILT
    
    Args:
        process_name: Name of the process to update
        change: Amount to change vacancy by (negative to decrease)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Open a new connection to ensure we're getting the latest data
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use direct SQL for atomic update to avoid race conditions
    if change < 0:
        # For decreasing vacancy, make sure it doesn't go below 0
        cursor.execute("""
            UPDATE processes 
            SET vacancy = CASE
                WHEN vacancy + ? < 0 THEN 0
                ELSE vacancy + ?
            END
            WHERE process_name = ?
        """, (change, change, process_name))
    else:
        # For increasing vacancy, just add
        cursor.execute("""
            UPDATE processes 
            SET vacancy = vacancy + ?
            WHERE process_name = ?
        """, (change, process_name))
    
    # Check if any rows were affected
    if cursor.rowcount == 0:
        conn.close()
        return False
    
    # Commit and close
    conn.commit()
    conn.close()
    
    # Verify the update happened correctly
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (process_name,))
    result = cursor.fetchone()
    conn.close()
    
    # Return true if we found the process
    return result is not None

def add_employee(name, email, potential, communication, process_name=None):
    """
    Add a new employee to the database - COMPLETELY REBUILT for reliability
    
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
    # Clean up the database first to ensure deleted emails are purged
    purge_deleted_emails()
    
    # Create a fresh connection for this transaction
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Normalize the email to ensure case insensitivity
        email = email.strip().lower()
        
        # Check if email already exists with more thorough check
        cursor.execute("SELECT COUNT(*) FROM employees WHERE LOWER(email) = LOWER(?)", (email,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Roll back - no changes made
            cursor.execute("ROLLBACK")
            conn.close()
            return False, "Email already exists in the database"
        
        process_id = None
        if process_name:
            # Get process ID and check vacancy atomically
            cursor.execute("SELECT id, vacancy FROM processes WHERE process_name = ?", (process_name,))
            result = cursor.fetchone()
            
            if not result:
                cursor.execute("ROLLBACK")
                conn.close()
                return False, f"Process {process_name} not found"
                
            process_id = result[0]
            current_vacancy = result[1]
            
            # Check if there's still vacancy available
            if current_vacancy <= 0:
                cursor.execute("ROLLBACK")
                conn.close()
                return False, f"No vacancy available in {process_name}"
            
            # Update vacancy count - decrement by 1
            cursor.execute("""
                UPDATE processes 
                SET vacancy = vacancy - 1
                WHERE process_name = ? AND vacancy > 0
            """, (process_name,))
            
            # Check if update was successful
            if cursor.rowcount == 0:
                cursor.execute("ROLLBACK")
                conn.close()
                return False, f"Failed to update vacancy for {process_name}"
            
            # Verify the new vacancy count
            cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (process_name,))
            new_vacancy = cursor.fetchone()[0]
            print(f"Updated vacancy for {process_name} from {current_vacancy} to {new_vacancy}")
        
        # Add employee
        cursor.execute(
            "INSERT INTO employees (name, email, potential, communication, process_id, process_name) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, potential, communication, process_id, process_name)
        )
        
        # Get the new employee ID
        employee_id = cursor.lastrowid
        print(f"Added employee {name} with ID {employee_id} to process {process_name}")
        
        # Everything worked, commit the transaction
        cursor.execute("COMMIT")
        conn.close()
        
        # Force vacuum to ensure database is clean
        purge_deleted_emails()
        
        return True, "Employee added successfully"
    
    except Exception as e:
        # Something went wrong, roll back any changes
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
        
        conn.close()
        print(f"Error adding employee: {str(e)}")
        return False, f"Database error: {str(e)}"

def get_employee_assignments():
    """
    Get all employee assignments
    
    Returns:
        DataFrame: Employee assignments data
    """
    conn = get_connection()
    
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
    conn = get_connection()
    
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
    # First run a purge to ensure we have no deleted records
    purge_deleted_emails()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Normalize email for case-insensitive search
    email = email.strip().lower()
    
    # Use COUNT first to check if the employee exists at all
    cursor.execute("SELECT COUNT(*) FROM employees WHERE LOWER(email) = LOWER(?)", (email,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        conn.close()
        return None
    
    # If employee exists, get all details
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.potential, e.communication, 
               e.process_id, e.process_name
        FROM employees e
        WHERE LOWER(e.email) = LOWER(?)
        LIMIT 1
    """, (email,))
    
    result = cursor.fetchone()
    
    # Print debug info
    if result:
        print(f"Found employee: ID={result[0]}, Name={result[1]}, Email={result[2]}")
    else:
        print(f"No employee found with email: {email}")
    
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
    Update an employee's details - REBUILT with transactions
    
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
    # Clean up the database first
    purge_deleted_emails()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Normalize email for case-insensitive comparison
        email = email.strip().lower()
        
        # Check if email already exists for another employee (case insensitive)
        cursor.execute("SELECT id FROM employees WHERE LOWER(email) = LOWER(?) AND id != ?", (email, employee_id))
        if cursor.fetchone():
            cursor.execute("ROLLBACK")
            conn.close()
            return False, "Email already exists for another employee"
        
        # Get current process assignment to update vacancy if changed
        cursor.execute("SELECT process_name FROM employees WHERE id = ?", (employee_id,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("ROLLBACK")
            conn.close()
            return False, "Employee not found"
            
        old_process = result[0]
        print(f"Updating employee {employee_id} from process '{old_process}' to '{process_name}'")
        
        # Update process vacancy counts if assignment changed
        if old_process != process_name:
            # Increase vacancy for old process if there was one
            if old_process:
                cursor.execute("""
                    UPDATE processes 
                    SET vacancy = vacancy + 1 
                    WHERE process_name = ?
                """, (old_process,))
                
                # Get the updated vacancy for old process
                cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (old_process,))
                old_vacancy = cursor.fetchone()
                if old_vacancy:
                    print(f"Increased vacancy for {old_process} to {old_vacancy[0]}")
            
            # Get process ID and check vacancy for the new process
            process_id = None
            if process_name:
                cursor.execute("SELECT id, vacancy FROM processes WHERE process_name = ?", (process_name,))
                result = cursor.fetchone()
                if not result:
                    cursor.execute("ROLLBACK")
                    conn.close()
                    return False, f"Process {process_name} not found"
                    
                process_id = result[0]
                current_vacancy = result[1]
                
                # Check if there's vacancy available
                if current_vacancy <= 0:
                    cursor.execute("ROLLBACK")
                    conn.close()
                    return False, f"No vacancy available in {process_name}"
                
                # Decrease vacancy for new process - simpler approach
                cursor.execute("""
                    UPDATE processes 
                    SET vacancy = vacancy - 1
                    WHERE process_name = ? AND vacancy > 0
                """, (process_name,))
                
                if cursor.rowcount == 0:
                    cursor.execute("ROLLBACK")
                    conn.close()
                    return False, f"Failed to update vacancy for {process_name}"
                
                # Get the updated vacancy for new process
                cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (process_name,))
                new_vacancy = cursor.fetchone()
                if new_vacancy:
                    print(f"Decreased vacancy for {process_name} to {new_vacancy[0]}")
        else:
            # No change in process assignment
            # Get process ID for the current process
            process_id = None
            if process_name:
                cursor.execute("SELECT id FROM processes WHERE process_name = ?", (process_name,))
                result = cursor.fetchone()
                if result:
                    process_id = result[0]
        
        # Update employee with the new details
        cursor.execute("""
            UPDATE employees 
            SET name = ?, email = ?, potential = ?, communication = ?, 
                process_id = ?, process_name = ?
            WHERE id = ?
        """, (name, email, potential, communication, process_id, process_name, employee_id))
        
        # Verify the update worked
        if cursor.rowcount == 0:
            cursor.execute("ROLLBACK")
            conn.close()
            return False, "Employee not found or no changes made"
        
        # All operations successful, commit
        cursor.execute("COMMIT")
        conn.close()
        
        # Force vacuum to ensure database is clean
        purge_deleted_emails()
        
        return True, "Employee updated successfully"
    
    except Exception as e:
        # Something went wrong, roll back
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
            
        conn.close()
        print(f"Error updating employee: {str(e)}")
        return False, f"Database error: {str(e)}"

def delete_employee(employee_id):
    """
    Delete an employee and update process vacancy - REBUILT with transactions
    
    Args:
        employee_id: ID of employee to delete
    
    Returns:
        bool: True if successful, False otherwise
        str: Message with result
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Get the employee's process information
        cursor.execute("SELECT process_name, email FROM employees WHERE id = ?", (employee_id,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute("ROLLBACK")
            conn.close()
            return False, "Employee not found"
        
        process_name = result[0]
        email = result[1]
        
        print(f"Deleting employee with ID {employee_id}, email {email}, process {process_name}")
        
        # Delete the employee
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        
        # Verify the delete worked
        if cursor.rowcount == 0:
            cursor.execute("ROLLBACK") 
            conn.close()
            return False, "Employee could not be deleted"
        
        # Double-check deletion
        cursor.execute("SELECT COUNT(*) FROM employees WHERE id = ?", (employee_id,))
        if cursor.fetchone()[0] > 0:
            print(f"ERROR: Employee {employee_id} still exists after deletion!")
            cursor.execute("ROLLBACK")
            conn.close() 
            return False, "Failed to completely delete employee"
            
        # Also ensure no record with this email exists
        cursor.execute("SELECT COUNT(*) FROM employees WHERE LOWER(email) = LOWER(?)", (email,))
        if cursor.fetchone()[0] > 0:
            print(f"ERROR: Employee with email {email} still exists after deletion!")
            cursor.execute("DELETE FROM employees WHERE LOWER(email) = LOWER(?)", (email,))
            
        # Update process vacancy if employee was assigned
        if process_name:
            # Directly increment the vacancy 
            cursor.execute("""
                UPDATE processes 
                SET vacancy = vacancy + 1 
                WHERE process_name = ?
            """, (process_name,))
            
            # Log the update for troubleshooting
            cursor.execute("SELECT vacancy FROM processes WHERE process_name = ?", (process_name,))
            new_vacancy = cursor.fetchone()
            if new_vacancy:
                print(f"Updated vacancy for {process_name} to {new_vacancy[0]}")
            else:
                print(f"Warning: Process {process_name} not found when updating vacancy")
        
        # All operations successful, commit the transaction
        cursor.execute("COMMIT")
        
        # Ensure all changes are written to disk
        conn.commit()
        conn.close()
        
        # Force database cleaning
        purge_deleted_emails()
        
        return True, f"Employee deleted and process '{process_name or 'None'}' vacancy updated"
        
    except Exception as e:
        # Something went wrong, roll back
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
            
        conn.close()
        print(f"Error deleting employee: {str(e)}")
        return False, f"Error: {str(e)}"

def purge_deleted_emails():
    """Force cleanup of database to remove any lingering deleted emails"""
    try:
        # Vacuum the database to reclaim space and improve performance
        conn = get_connection()
        conn.execute("VACUUM")
        conn.commit()
        conn.close()
        
        print("Database purge completed successfully")
    except Exception as e:
        print(f"Error during database purge: {str(e)}")
        # Don't attempt any further operations on error

def reset_database():
    """Hard reset of the database - for emergency use"""
    try:
        # Close any open connections
        try:
            conn = get_connection()
            conn.close()
        except:
            pass
        
        # Delete the database file if it exists and we're not in cloud mode
        if not is_cloud and os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
                print(f"Database file {DB_PATH} removed")
            except Exception as e:
                print(f"Error removing database file: {str(e)}")
        
        # For cloud mode or if file deletion failed, just clear all tables
        conn = get_connection()
        cursor = conn.cursor()
        
        # Drop tables if they exist
        cursor.execute("DROP TABLE IF EXISTS employees")
        cursor.execute("DROP TABLE IF EXISTS processes")
        conn.commit()
        
        # Recreate the database
        init_schema(conn)
        conn.close()
        
        # Initialize with sample data
        init_db()
        
        print("Database has been reset")
        return True
    except Exception as e:
        print(f"Error resetting database: {str(e)}")
        return False

def get_process_suggestions(potential, communication):
    """
    Get process suggestions for an employee, sorted by vacancy (high to low)
    
    Args:
        potential: Employee potential
        communication: Employee communication level
    
    Returns:
        DataFrame: Process suggestions
    """
    conn = get_connection()
    
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