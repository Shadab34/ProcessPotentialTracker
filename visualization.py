import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_vacancy_chart(process_data):
    """
    Create a horizontal bar chart showing vacancies for each process
    
    Args:
        process_data: DataFrame containing process information
    
    Returns:
        Figure: Plotly figure object
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
        color_continuous_scale='Viridis',
        title='Process Vacancies'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Available Vacancies',
        yaxis_title='Process Name',
        height=min(400, 100 + len(process_data) * 30),  # Adjust height based on number of processes
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def create_process_distribution(process_data):
    """
    Create a pie chart showing distribution of processes by potential
    
    Args:
        process_data: DataFrame containing process information
    
    Returns:
        Figure: Plotly figure object
    """
    # Group by potential type and count
    potential_counts = process_data.groupby('Potential').size().reset_index(name='count')
    
    # Create pie chart
    fig = px.pie(
        potential_counts,
        values='count',
        names='Potential',
        title='Processes by Potential Type',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Update layout
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    return fig

def create_match_heatmap(process_data):
    """
    Create a heatmap showing process availability by potential and communication
    
    Args:
        process_data: DataFrame containing process information
    
    Returns:
        Figure: Plotly figure object
    """
    # Create pivot table
    pivot_data = process_data.pivot_table(
        values='Vacancy',
        index='Potential',
        columns='Communication',
        aggfunc='sum',
        fill_value=0
    )
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='Viridis',
        title='Process Availability by Skills'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Communication Level',
        yaxis_title='Potential Type',
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig
