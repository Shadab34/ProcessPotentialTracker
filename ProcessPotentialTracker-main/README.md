# Process Potential Tracker

A Streamlit application for matching employees to appropriate processes based on their potential and communication skills, while tracking process vacancies.

## Features

- **Process Management**: Track various processes with their vacancies
- **Employee Assignment**: Match employees to compatible processes based on skills
- **Vacancy Tracking**: Automatically update process vacancies when employees are assigned
- **Dashboard Visualization**: Visual representation of vacancy data
- **Employee Management**: Add, edit, and delete employees

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Shadab34/ProcessPotentialTracker.git
cd ProcessPotentialTracker
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application locally:
```bash
streamlit run app.py
```

## Deployment on Streamlit Cloud

This application is ready for deployment on Streamlit Cloud:

1. Fork this repository to your GitHub account
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and sign in
3. Click "New app" and select your forked repository
4. Set the main file path to `app.py`
5. Deploy the application

The application includes the necessary configuration for both local and cloud environments and handles database persistence appropriately in both scenarios.

## Usage

1. Upload process data or use the sample data provided
2. Use the sidebar for data management and employee operations
3. Add new employees and match them to available processes
4. Track vacancies and process distribution through the dashboard
5. Search for and edit existing employees

## Data Format

The application expects process data with the following columns:
- Process_Name: Name of the process
- Potential: Type of potential required (Sales, Service, Support, Consultation)
- Communication: Level of communication required (Excellent, Very Good, Good)
- Vacancy: Number of vacant positions

## Solution for Common Issues

If you encounter an issue with the application not showing all matching processes, ensure you're using the latest version which fixes:
- All matching processes now appear (instead of just the first one)
- Processes are properly sorted by vacancy count and name
- Whitespace handling is improved for better matching

## License

MIT License
