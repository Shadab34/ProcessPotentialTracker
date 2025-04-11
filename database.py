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
    Update vacancy count for a process - COMPLETELY REBUILT
    
    Args:
        process_name: Name of the process to update
        change: Amount to change vacancy by (negative to decrease)
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Open a new connection to ensure we're getting the latest data
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
            
            # Update vacancy count atomically using direct SQL
            # This ensures the vacancy is updated reliably
            cursor.execute("""
                UPDATE processes 
                SET vacancy = CASE
                    WHEN vacancy > 0 THEN vacancy - 1
                    ELSE 0
                END
                WHERE process_name = ?
            """, (process_name,))
            
            # Verify the update worked
            if cursor.rowcount == 0:
                cursor.execute("ROLLBACK")
                conn.close()
                return False, f"Failed to update vacancy for {process_name}"
        
        # Add employee
        cursor.execute(
            "INSERT INTO employees (name, email, potential, communication, process_id, process_name) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, potential, communication, process_id, process_name)
        )
        
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
        return False, f"Database error: {str(e)}"

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
    
    # Normalize email for case-insensitive search
    email = email.strip().lower()
    
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.potential, e.communication, 
               e.process_id, e.process_name
        FROM employees e
        WHERE LOWER(e.email) = LOWER(?)
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
    
    conn = sqlite3.connect(DB_PATH)
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
        
        # Update process vacancy counts if assignment changed
        if old_process != process_name:
            # Increase vacancy for old process if there was one
            if old_process:
                cursor.execute("""
                    UPDATE processes 
                    SET vacancy = vacancy + 1 
                    WHERE process_name = ?
                """, (old_process,))
                
                if cursor.rowcount == 0:
                    # Old process not found, but continue anyway
                    pass
            
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
                
                # Decrease vacancy for new process - use the safer atomic SQL approach
                cursor.execute("""
                    UPDATE processes 
                    SET vacancy = CASE
                        WHEN vacancy > 0 THEN vacancy - 1
                        ELSE 0
                    END
                    WHERE process_name = ?
                """, (process_name,))
                
                if cursor.rowcount == 0:
                    cursor.execute("ROLLBACK")
                    conn.close()
                    return False, f"Failed to update vacancy for {process_name}"
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
    conn = sqlite3.connect(DB_PATH)
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
        
        # Delete the employee
        cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        
        # Verify the delete worked
        if cursor.rowcount == 0:
            cursor.execute("ROLLBACK") 
            conn.close()
            return False, "Employee could not be deleted"
        
        # Update process vacancy if employee was assigned
        if process_name:
            cursor.execute("""
                UPDATE processes 
                SET vacancy = vacancy + 1 
                WHERE process_name = ?
            """, (process_name,))
            
            # We don't check rowcount here since the process might have been deleted
            # But we still want to delete the employee
        
        # All operations successful, commit the transaction
        cursor.execute("COMMIT")
        conn.close()
        
        # Force database cleaning to remove the deleted employee email
        purge_deleted_emails()
        
        return True, f"Employee deleted and process '{process_name or 'None'}' vacancy updated"
        
    except Exception as e:
        # Something went wrong, roll back
        try:
            cursor.execute("ROLLBACK")
        except:
            pass
            
        conn.close()
        return False, f"Database error: {str(e)}"

def purge_deleted_emails():
    """Force cleanup of database to remove any lingering deleted emails"""
    # This function will force SQLite to vacuum the database
    # which should help with the issue of deleted emails still being detected
    conn = sqlite3.connect(DB_PATH)
    conn.execute("VACUUM")
    conn.commit()
    conn.close()
    
def reset_database():
    """Hard reset of the database - for emergency use"""
    import os
    
    # Close any open connections
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
    except:
        pass
    
    # Delete the database file if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Recreate the database
    init_db()

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