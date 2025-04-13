import pandas as pd
import numpy as np

def find_matching_process(process_data, potential, communication):
    """
    Find matching processes for an employee based on potential and communication skills
    
    Args:
        process_data: DataFrame containing process information
        potential: Employee's potential (Sales, Consultation, Service, Support)
        communication: Employee's communication level (Excellent, Good, Very Good)
    
    Returns:
        DataFrame: All matching processes with vacancies
    """
    if process_data is None or process_data.empty:
        return None
        
    # Filter processes by potential and communication
    matching_processes = process_data[
        (process_data['Potential'].str.strip() == potential.strip()) & 
        (process_data['Communication'].str.strip() == communication.strip()) &
        (process_data['Vacancy'] > 0)
    ].copy()
    
    # If no exact matches, try to find matches with only potential
    if matching_processes.empty:
        matching_processes = process_data[
            (process_data['Potential'].str.strip() == potential.strip()) & 
            (process_data['Vacancy'] > 0)
        ].copy()
    
    # Sort by vacancy (higher vacancy first) and process name
    if not matching_processes.empty:
        matching_processes = matching_processes.sort_values(['Vacancy', 'Process_Name'], ascending=[False, True])
        print(f"Found {len(matching_processes)} matching processes with total {matching_processes['Vacancy'].sum()} vacancies")
        return matching_processes
    else:
        print(f"No matching processes found for Potential: {potential}, Communication: {communication}")
        return None

def get_process_suggestions(process_data, potential, communication):
    """
    Get process suggestions that partially match the employee's skills
    
    Args:
        process_data: DataFrame containing process information
        potential: Employee's potential (Sales, Consultation, Service, Support)
        communication: Employee's communication level (Excellent, Good, Very Good)
    
    Returns:
        DataFrame: Suggested processes sorted by relevance and vacancy
    """
    if process_data is None or process_data.empty:
        return None
        
    # Get processes with either matching potential or communication
    suggested_processes = process_data[
        ((process_data['Potential'].str.strip() == potential.strip()) | 
         (process_data['Communication'].str.strip() == communication.strip())) &
        (process_data['Vacancy'] > 0)
    ].copy()
    
    if suggested_processes.empty:
        return None
    
    # Calculate relevance score
    suggested_processes['relevance'] = 0
    suggested_processes.loc[suggested_processes['Potential'].str.strip() == potential.strip(), 'relevance'] += 2
    suggested_processes.loc[suggested_processes['Communication'].str.strip() == communication.strip(), 'relevance'] += 1
    
    # Sort by relevance (high to low), vacancy (high to low), and process name
    result = suggested_processes.sort_values(
        ['relevance', 'Vacancy', 'Process_Name'], 
        ascending=[False, False, True]
    )
    
    print(f"Found {len(result)} suggested processes with total {result['Vacancy'].sum()} vacancies")
    return result
