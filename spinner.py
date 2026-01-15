import random
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict
import streamlit as st

def create_spinner_wheel(tasks: List[Dict], selected_task: Dict = None):
    if not tasks:
        st.warning("No tasks available. Please add tasks first!")
        return None
    
    num_tasks = len(tasks)
    colors = generate_colors(num_tasks)
    
    theta = np.linspace(0, 2 * np.pi, num_tasks + 1)
    
    fig = go.Figure()
    
    for i, task in enumerate(tasks):
        theta_start = theta[i]
        theta_end = theta[i + 1]
        theta_mid = (theta_start + theta_end) / 2
        
        theta_range = np.linspace(theta_start, theta_end, 50)
        r = [1] * len(theta_range)
        
        is_selected = selected_task and task['id'] == selected_task['id']
        
        fig.add_trace(go.Scatterpolar(
            r=r,
            theta=np.degrees(theta_range),
            fill='toself',
            fillcolor=colors[i],
            line=dict(color='white', width=3),
            opacity=1.0 if is_selected else 0.8,
            name=task['task_name'],
            hovertemplate=f"<b>{task['task_name']}</b><br>Category: {task['category']}<br>Priority: {task['priority']}<extra></extra>"
        ))
        
        label_r = 0.6
        label_x = label_r * np.cos(theta_mid)
        label_y = label_r * np.sin(theta_mid)
        
        fig.add_annotation(
            x=label_x,
            y=label_y,
            text=f"<b>{task['task_name']}</b>",
            showarrow=False,
            font=dict(size=12 if num_tasks <= 8 else 10, color='white'),
            bgcolor='rgba(0,0,0,0.5)',
            borderpad=4
        )
    
    center_size = 0.15
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(size=80, color='#1f2937', line=dict(color='white', width=3)),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    arrow_length = 1.2
    fig.add_annotation(
        x=0,
        y=arrow_length,
        ax=0,
        ay=0,
        xref='x',
        yref='y',
        axref='x',
        ayref='y',
        showarrow=True,
        arrowhead=2,
        arrowsize=2,
        arrowwidth=4,
        arrowcolor='#ef4444'
    )
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 1.3]),
            angularaxis=dict(visible=False)
        ),
        showlegend=False,
        width=600,
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def generate_colors(num_colors: int) -> List[str]:
    base_colors = [
        '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', 
        '#f59e0b', '#06b6d4', '#84cc16', '#f97316',
        '#14b8a6', '#6366f1', '#a855f7', '#e11d48'
    ]
    
    if num_colors <= len(base_colors):
        return base_colors[:num_colors]
    
    colors = []
    for i in range(num_colors):
        hue = (i * 360 / num_colors) % 360
        colors.append(f'hsl({hue}, 70%, 50%)')
    
    return colors

def select_random_task(tasks: List[Dict]) -> Dict:
    if not tasks:
        return None
    
    weights = [task['priority'] for task in tasks]
    return random.choices(tasks, weights=weights, k=1)[0]

def create_mini_wheel(task_name: str, color: str = '#10b981'):
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(size=150, color=color, line=dict(color='white', width=3)),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_annotation(
        x=0,
        y=0,
        text=f"<b>{task_name}</b>",
        showarrow=False,
        font=dict(size=16, color='white'),
    )
    
    fig.update_layout(
        xaxis=dict(visible=False, range=[-1, 1]),
        yaxis=dict(visible=False, range=[-1, 1]),
        width=300,
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    return fig
