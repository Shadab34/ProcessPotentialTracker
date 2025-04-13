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
        try:
            data = pd.read_excel(file)
            # Save a copy of the file for debugging
            with open(f"processed_uploads/{file.name}", "wb") as f:
                file.seek(0)
                f.write(file.getvalue())
                file.seek(0)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    elif file.name.endswith('.csv'):
        try:
            data = pd.read_csv(file)
            # Save a copy of the file for debugging
            with open(f"processed_uploads/{file.name}", "wb") as f:
                file.seek(0)
                f.write(file.getvalue())
                file.seek(0)
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
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
    # Convert to string and strip any whitespace
    data['Potential'] = data['Potential'].astype(str).str.strip()
    invalid_potentials = data[~data['Potential'].isin(valid_potentials)]['Potential'].unique()
    
    if len(invalid_potentials) > 0:
        raise ValueError(f"Invalid potential values found: {', '.join(map(str, invalid_potentials))}. "
                         f"Valid values are: {', '.join(valid_potentials)}")
    
    # Validate communication values
    valid_communications = ['Excellent', 'Very Good', 'Good']
    # Convert to string and strip any whitespace
    data['Communication'] = data['Communication'].astype(str).str.strip()
    invalid_communications = data[~data['Communication'].isin(valid_communications)]['Communication'].unique()
    
    if len(invalid_communications) > 0:
        raise ValueError(f"Invalid communication values found: {', '.join(map(str, invalid_communications))}. "
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
