import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import streamlit as st

def create_task_frequency_chart(task_freq: List[tuple]):
    if not task_freq or all(count == 0 for _, count in task_freq):
        st.info("No spin data yet. Spin the wheel to see analytics!")
        return None
    
    tasks, counts = zip(*task_freq)
    
    colors = ['#10b981' if c > 0 else '#374151' for c in counts]
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(tasks),
            y=list(counts),
            marker_color=colors,
            text=list(counts),
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Spins: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Task Frequency Distribution",
        xaxis_title="Tasks",
        yaxis_title="Number of Spins",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    return fig

def create_category_pie_chart(category_stats: List[Dict]):
    if not category_stats or all(stat['total'] == 0 for stat in category_stats):
        st.info("No category data yet. Spin the wheel to see distribution!")
        return None
    
    categories = [stat['category'] for stat in category_stats if stat['total'] > 0]
    totals = [stat['total'] for stat in category_stats if stat['total'] > 0]
    
    if not categories:
        return None
    
    fig = go.Figure(data=[
        go.Pie(
            labels=categories,
            values=totals,
            hole=0.4,
            marker=dict(colors=px.colors.qualitative.Set3),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Spins: %{value}<br>%{percent}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Task Distribution by Category",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400
    )
    
    return fig

def create_timeline_chart(df: pd.DataFrame):
    if df.empty:
        st.info("No timeline data yet. Spin the wheel daily to see trends!")
        return None
    
    daily_counts = df.groupby('spin_date').size().reset_index(name='count')
    daily_counts['spin_date'] = pd.to_datetime(daily_counts['spin_date'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily_counts['spin_date'],
        y=daily_counts['count'],
        mode='lines+markers',
        name='Daily Spins',
        line=dict(color='#10b981', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.2)',
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Spins: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Daily Activity Timeline",
        xaxis_title="Date",
        yaxis_title="Number of Spins",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_completion_gauge(completion_rate: float):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=completion_rate,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Completion Rate", 'font': {'color': 'white'}},
        delta={'reference': 80, 'increasing': {'color': "#10b981"}},
        gauge={
            'axis': {'range': [None, 100], 'tickcolor': "white"},
            'bar': {'color': "#10b981"},
            'bgcolor': "rgba(255,255,255,0.1)",
            'borderwidth': 2,
            'bordercolor': "white",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.3)'},
                {'range': [50, 75], 'color': 'rgba(251, 191, 36, 0.3)'},
                {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        },
        number={'suffix': "%", 'font': {'color': 'white'}}
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=300
    )
    
    return fig

def create_heatmap(df: pd.DataFrame):
    if df.empty:
        st.info("No heatmap data yet. Build up your history!")
        return None
    
    df['date'] = pd.to_datetime(df['spun_at']).dt.date
    df['hour'] = pd.to_datetime(df['spun_at']).dt.hour
    
    pivot = df.pivot_table(
        index='hour',
        columns='date',
        values='task_name',
        aggfunc='count',
        fill_value=0
    )
    
    if pivot.empty:
        return None
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=[f"{h:02d}:00" for h in pivot.index],
        colorscale='Greens',
        hovertemplate='Date: %{x}<br>Hour: %{y}<br>Spins: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Activity Heatmap (Hour vs Date)",
        xaxis_title="Date",
        yaxis_title="Hour of Day",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500
    )
    
    return fig

def display_statistics(db):
    col1, col2, col3, col4 = st.columns(4)
    
    total_spins = len(db.get_spin_history(limit=10000))
    total_tasks = db.get_task_count()
    completion_rate = db.get_completion_rate()
    
    history = db.get_spin_history(limit=7)
    recent_activity = len(history)
    
    with col1:
        st.metric(
            label="Total Spins",
            value=total_spins,
            delta=f"{recent_activity} this week"
        )
    
    with col2:
        st.metric(
            label="Active Tasks",
            value=total_tasks
        )
    
    with col3:
        st.metric(
            label="Completion Rate",
            value=f"{completion_rate:.1f}%",
            delta=f"{completion_rate - 75:.1f}%" if completion_rate > 0 else None
        )
    
    with col4:
        if total_spins > 0:
            task_freq = db.get_task_frequency()
            most_common = max(task_freq, key=lambda x: x[1])[0] if task_freq else "N/A"
            st.metric(
                label="Most Spun",
                value=most_common
            )
