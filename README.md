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
git clone https://github.com/yourusername/ProcessPotentialTracker.git
cd ProcessPotentialTracker
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

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

## License

MIT License
