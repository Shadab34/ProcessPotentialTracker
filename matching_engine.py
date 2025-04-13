import pandas as pd
import numpy as np

def find_matching_process(process_data, potential, communication):
    """
    Find a matching process for an employee based on potential and communication skills
    
    Args:
        process_data: DataFrame containing process information
        potential: Employee's potential (Sales, Consultation, Service, Support)
        communication: Employee's communication level (Excellent, Good, Very Good)
    
    Returns:
        dict: Matching process information or None if no match found
    """
    # Filter processes by potential and communication
    matching_processes = process_data[
        (process_data['Potential'] == potential) & 
        (process_data['Communication'] == communication) &
        (process_data['Vacancy'] > 0)
    ]
    
    # If no matches, try to find a match with only potential
    if matching_processes.empty:
        matching_processes = process_data[
            (process_data['Potential'] == potential) & 
            (process_data['Vacancy'] > 0)
        ]
    
    # Sort by vacancy (higher vacancy first)
    matching_processes = matching_processes.sort_values('Vacancy', ascending=False)
    
    # Return the best match or None if no matches
    if not matching_processes.empty:
        return matching_processes.iloc[0].to_dict()
    else:
        return None

def get_process_suggestions(process_data, potential, communication):
    """
    Get process suggestions that partially match the employee's skills
    
    Args:
        process_data: DataFrame containing process information
        potential: Employee's potential (Sales, Consultation, Service, Support)
        communication: Employee's communication level (Excellent, Good, Very Good)
    
    Returns:
        DataFrame: Suggested processes
    """
    # Get processes with either matching potential or communication
    suggested_processes = process_data[
        ((process_data['Potential'] == potential) | 
         (process_data['Communication'] == communication)) &
        (process_data['Vacancy'] > 0)
    ]
    
    # Sort by relevance
    # - Matching potential is more important than matching communication
    suggested_processes['relevance'] = 0
    suggested_processes.loc[suggested_processes['Potential'] == potential, 'relevance'] += 2
    suggested_processes.loc[suggested_processes['Communication'] == communication, 'relevance'] += 1
    
    return suggested_processes.sort_values(['relevance', 'Vacancy'], ascending=[False, False])
