import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(
    page_title="Employee-Process Matcher",
    page_icon="🔍",
    layout="wide"
)

# Demo data
demo_process_data = pd.DataFrame({
    'Process_Name': [
        'TVS CC', 'CW Massbrand', 'CW Inbound', 'Bgauss CC', 'TVS Credit',
        'abSure', 'Consumer Feedback', 'Citroen CC', 'CW Cross Sell',
        'Bajaj Online Booking', 'TVS DC', 'Jawa & Yezdi DC', 'Piaggio DC',
        'Ather DC', 'Jeep CC', 'Citroen DC', 'UCD CC'
    ],
    'Potential': [
        'Service', 'Consultation', 'Service', 'Service', 'Service',
        'Consultation', 'Support', 'Service', 'Service',
        'Sales', 'Service', 'Service', 'Service',
        'Service', 'Service', 'Service', 'Service'
    ],
    'Communication': [
        'Good', 'Excellent', 'Good', 'Good', 'Good',
        'Excellent', 'Good', 'Good', 'Good',
        'Good', 'Good', 'Good', 'Good',
        'Good', 'Good', 'Good', 'Good'
    ],
    'Vacancy': [
        20, 9, 8, 3, 2,
        2, 2, 2, 2,
        1, 1, 1, 1,
        1, 1, 1, 1
    ]
})

# Demo employees
demo_employees = pd.DataFrame({
    'Name': ['John Doe', 'Jane Smith', 'Mark Johnson'],
    'Email': ['john@example.com', 'jane@example.com', 'mark@example.com'],
    'Potential': ['Service', 'Sales', 'Consultation'],
    'Communication': ['Good', 'Excellent', 'Very Good'],
    'Process': ['TVS CC', 'Bajaj Online Booking', 'CW Massbrand']
})

# Function to create a vacancy chart
def create_vacancy_chart(process_data):
    """
    Create a horizontal bar chart showing vacancies for each process
    """
    # Sort by vacancy count (descending)
    sorted_data = process_data.sort_values('Vacancy', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        sorted_data,
        y='Process_Name',
        x='Vacancy',
        color='Vacancy',
        orientation='h',
        color_continuous_scale='plasma',
        title='Process Vacancies',
        text='Vacancy',
        hover_data={'Process_Name': True, 'Vacancy': True, 'Potential': True, 'Communication': True}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Available Vacancies',
        yaxis_title='Process Name',
        height=min(400, 100 + len(process_data) * 30),
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(title="Vacancies"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Make the text more readable and bars more vibrant
    fig.update_traces(
        textposition='outside', 
        textfont_size=10,
        marker_line_width=1,
        marker_line_color='rgba(0,0,0,0.3)',
        opacity=0.9
    )
    
    return fig

# Function to create pie chart
def create_process_distribution(process_data):
    """
    Create a pie chart showing distribution of processes by potential
    """
    # Group by potential type and count
    potential_counts = process_data.groupby('Potential')['Process_Name'].nunique().reset_index(name='count')
    
    # Calculate percentages for display
    total = potential_counts['count'].sum()
    potential_counts['percentage'] = (potential_counts['count'] / total * 100).round(1)
    potential_counts['label'] = potential_counts['Potential'] + ' (' + potential_counts['percentage'].astype(str) + '%)'
    
    # Create pie chart with custom colors
    colors = px.colors.qualitative.Bold
    
    fig = px.pie(
        potential_counts,
        values='count',
        names='label',
        title='Processes by Potential Type',
        color_discrete_sequence=colors
    )
    
    # Update layout and text
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Update text inside pie chart
    fig.update_traces(
        textinfo='percent+label',
        textposition='inside',
        textfont=dict(size=12, color='white'),
        marker=dict(line=dict(color='#000000', width=1)),
        pull=[0.05] * len(potential_counts),
        hoverinfo='label+percent+value'
    )
    
    return fig

# Title and description
st.title("Employee-Process Matcher")
st.markdown("""
This application helps match employees to appropriate processes based on their 
potential and communication skills, while tracking process vacancies.

**Note: This is a cloud demo version. For full functionality, run the app locally.**
""")

# Add sidebar explanation
with st.sidebar:
    st.header("Cloud Demo Mode")
    st.info("""
    This is a cloud demonstration of the Process Potential Tracker application.
    
    In this mode, you can view sample data and visualizations, but database operations
    are disabled.
    
    For full functionality with employee management and database storage,
    please run the application locally using:
    ```
    streamlit run app.py
    ```
    """)
    
    st.write("GitHub Repository:")
    st.markdown("[Shadab34/ProcessPotentialTracker](https://github.com/Shadab34/ProcessPotentialTracker)")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Process Data")
    st.dataframe(demo_process_data, use_container_width=True)
    
    st.subheader("Sample Employees")
    st.dataframe(demo_employees, use_container_width=True)

with col2:
    st.subheader("Vacancy Overview")
    fig = create_vacancy_chart(demo_process_data)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Processes by Potential Type")
    fig2 = create_process_distribution(demo_process_data)
    st.plotly_chart(fig2, use_container_width=True)

# Footer
st.divider()
st.caption("Employee-Process Matcher Demo | Created by Shadab34") 