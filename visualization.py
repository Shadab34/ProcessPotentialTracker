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
        color_continuous_scale='plasma',
        title='Process Vacancies',
        text='Vacancy',
        hover_data={'Process_Name': True, 'Vacancy': True, 'Potential': True, 'Communication': True}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Available Vacancies',
        yaxis_title='Process Name',
        height=min(400, 100 + len(process_data) * 30),  # Adjust height based on number of processes
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

def create_process_distribution(process_data):
    """
    Create a pie chart showing distribution of processes by potential
    
    Args:
        process_data: DataFrame containing process information
    
    Returns:
        Figure: Plotly figure object
    """
    # Group by potential type and count
    # We need to count unique processes, not just rows
    potential_counts = process_data.groupby('Potential')['Process_Name'].nunique().reset_index(name='count')
    
    # Calculate percentages for display
    total = potential_counts['count'].sum()
    potential_counts['percentage'] = (potential_counts['count'] / total * 100).round(1)
    potential_counts['label'] = potential_counts['Potential'] + ' (' + potential_counts['percentage'].astype(str) + '%)'
    
    # Create pie chart with custom colors
    colors = px.colors.qualitative.Bold  # Using a more vibrant color palette
    
    fig = px.pie(
        potential_counts,
        values='count',
        names='label',  # Use the formatted labels with percentages
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
        pull=[0.05] * len(potential_counts),  # Slight pull for better visualization
        hoverinfo='label+percent+value'
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
