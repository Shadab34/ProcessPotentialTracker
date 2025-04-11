import pandas as pd
import numpy as np
from io import BytesIO

def load_data(file):
    """
    Load process data from an uploaded file (Excel or CSV)
    
    Args:
        file: The uploaded file object
    
    Returns:
        DataFrame: Processed data with required columns
    """
    # Check file extension
    if file.name.endswith('.xlsx'):
        data = pd.read_excel(file)
    elif file.name.endswith('.csv'):
        data = pd.read_csv(file)
    else:
        raise ValueError("Unsupported file format. Please upload an Excel (.xlsx) or CSV (.csv) file.")
    
    # Validate required columns
    required_columns = ['Process_Name', 'Potential', 'Communication', 'Vacancy']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate data types and values
    if not pd.api.types.is_numeric_dtype(data['Vacancy']):
        try:
            data['Vacancy'] = pd.to_numeric(data['Vacancy'])
        except ValueError:
            raise ValueError("Vacancy must contain numeric values")
    
    # Validate potential values
    valid_potentials = ['Sales', 'Consultation', 'Service', 'Support']
    invalid_potentials = data[~data['Potential'].isin(valid_potentials)]['Potential'].unique()
    
    if len(invalid_potentials) > 0:
        raise ValueError(f"Invalid potential values found: {', '.join(invalid_potentials)}. "
                         f"Valid values are: {', '.join(valid_potentials)}")
    
    # Validate communication values
    valid_communications = ['Excellent', 'Very Good', 'Good']
    invalid_communications = data[~data['Communication'].isin(valid_communications)]['Communication'].unique()
    
    if len(invalid_communications) > 0:
        raise ValueError(f"Invalid communication values found: {', '.join(invalid_communications)}. "
                         f"Valid values are: {', '.join(valid_communications)}")
    
    return data

def save_data(data):
    """
    Save process data to an Excel file
    
    Args:
        data: DataFrame to save
    
    Returns:
        BytesIO: Excel file as BytesIO object
    """
    buffer = BytesIO()
    data.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer
