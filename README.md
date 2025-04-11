# Employee-Process Matcher

This application helps match employees to appropriate processes based on their potential and communication skills, while tracking process vacancies.

## Features

- Import process data from Excel/CSV files
- Match employees to appropriate processes based on skills
- Automatically update process vacancy counts when employees are assigned
- Filter processes by potential types (Sales, Consultation, Service, Support)
- Filter processes by communication levels (Excellent, Good, Very Good)
- Data visualization for process vacancies and assignments
- Simple user interface for adding new employees

## Setup Instructions

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install streamlit pandas numpy plotly openpyxl
   ```
3. Run the application:
   ```
   streamlit run app.py
   ```

## Data Format

The application expects data in the following format:

| Process_Name     | Potential    | Communication | Vacancy |
|------------------|--------------|--------------|---------|
| Sales Support    | Sales        | Good         | 5       |
| Customer Service | Service      | Very Good    | 3       |

### Required Columns:

- **Process_Name**: Name of the process
- **Potential**: One of: Sales, Consultation, Service, Support
- **Communication**: One of: Excellent, Very Good, Good
- **Vacancy**: Number of available positions (integer)

## Usage Instructions

### 1. Data Import

- Use the sidebar to upload an Excel (.xlsx) or CSV (.csv) file with process data
- A sample data file is provided in the `sample_data` folder

### 2. View Processes

- All uploaded processes will be displayed in a table
- Use the filters to narrow down processes by potential type or communication level
- Visualizations show vacancy distribution and potential type breakdown

### 3. Add New Employee

- Click the "Add New Employee" button in the sidebar
- Enter employee name and select potential and communication skills
- The system will find the best matching process based on skills
- If a match is found, the vacancy count for that process will be automatically updated
- If no match is found, you'll see a "No Match Found" message

### 4. Download Data

- After making changes, you can download the updated process data in Excel format

## Notes

- Potential types are limited to: Sales, Consultation, Service, Support
- Communication levels are limited to: Excellent, Very Good, Good
- The system prioritizes exact matches (both potential and communication) but can fall back to matching just potential if necessary
- Processes with zero vacancies will not be matched

## Sample Data

A sample dataset is provided in `sample_data/sample_processes.csv`. You can use this file to test the application.
