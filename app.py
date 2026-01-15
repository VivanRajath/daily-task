import streamlit as st
from database import TaskDatabase
from spinner import create_spinner_wheel, select_random_task
from analytics import (
    create_task_frequency_chart, 
    create_category_pie_chart,
    create_timeline_chart,
    create_completion_gauge,
    create_heatmap,
    display_statistics
)
from reports import display_report_dashboard
from datetime import datetime
import time

st.set_page_config(
    page_title="Daily Task Spinner",
    page_icon="target",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    h1, h2, h3 {
        color: #10b981 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 15px 30px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
        margin: 5px 0;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(16, 185, 129, 0.4);
    }
    .task-card {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3);
        margin: 20px 0;
    }
    .task-card h2 {
        color: white !important;
        margin: 0;
        font-size: 24px;
    }
    .task-card p {
        color: rgba(255,255,255,0.9);
        margin: 10px 0;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    div[data-testid="column"] {
        padding: 10px;
    }
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
    }
    .stTextInput input {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
    }
    .section-header {
        margin-top: 30px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

if 'db' not in st.session_state:
    st.session_state.db = TaskDatabase()

if 'selected_task' not in st.session_state:
    st.session_state.selected_task = None

if 'last_spin_id' not in st.session_state:
    st.session_state.last_spin_id = None

if 'spinning' not in st.session_state:
    st.session_state.spinning = False

db = st.session_state.db

st.sidebar.title("Daily Task Spinner")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Spinner", "Analytics", "Reports", "Manage Tasks", "History"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")
total_spins = len(db.get_spin_history(limit=10000))
completion_rate = db.get_completion_rate()
st.sidebar.metric("Total Spins", total_spins)
st.sidebar.metric("Completion Rate", f"{completion_rate:.1f}%")

if page == "Spinner":
    st.title("Daily Task Spinner")
    st.markdown("### Spin the wheel and commit to your task")
    
    tasks = db.get_all_tasks()
    
    if not tasks:
        st.warning("No tasks available. Please add tasks in the Manage Tasks section.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.session_state.selected_task:
                wheel_fig = create_spinner_wheel(tasks, st.session_state.selected_task)
            else:
                wheel_fig = create_spinner_wheel(tasks)
            
            if wheel_fig:
                st.plotly_chart(wheel_fig, use_container_width=True)
            
            st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
            col_spacer1, col_btn, col_spacer2 = st.columns([1, 2, 1])
            with col_btn:
                if st.button("SPIN THE WHEEL", key="spin_button", use_container_width=True):
                    with st.spinner("Spinning..."):
                        time.sleep(2)
                        selected = select_random_task(tasks)
                        st.session_state.selected_task = selected
                        
                        spin_id = db.record_spin(selected['id'])
                        st.session_state.last_spin_id = spin_id
                        
                        st.success("Task Selected")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Current Task")
            
            if st.session_state.selected_task:
                task = st.session_state.selected_task
                
                st.markdown(f"""
                <div class='task-card'>
                    <h2>{task['task_name']}</h2>
                    <p>
                        Category: {task['category']}<br>
                        Priority: {task['priority']}/5
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                st.markdown("### Mark as Complete")
                notes = st.text_area("Notes (optional)", key="task_notes", height=100)
                
                col_complete1, col_complete2 = st.columns(2)
                
                with col_complete1:
                    if st.button("Complete", key="btn_complete", use_container_width=True):
                        if st.session_state.last_spin_id:
                            db.mark_spin_completed(st.session_state.last_spin_id, True)
                            if notes:
                                conn = db.get_connection()
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE spin_history SET notes = ? WHERE id = ?",
                                    (notes, st.session_state.last_spin_id)
                                )
                                conn.commit()
                                conn.close()
                            st.success("Task marked as complete")
                            st.session_state.selected_task = None
                            st.session_state.last_spin_id = None
                            time.sleep(1)
                            st.rerun()
                
                with col_complete2:
                    if st.button("Skip", key="btn_skip", use_container_width=True):
                        st.session_state.selected_task = None
                        st.rerun()
            else:
                st.info("Click SPIN THE WHEEL to get started")
                
                st.markdown("### How it works")
                st.markdown("""
                1. Click the spin button
                2. The wheel will randomly select a task
                3. Work on the selected task
                4. Mark it complete or spin again
                5. Track your progress in Analytics
                """)

elif page == "Analytics":
    st.title("Analytics Dashboard")
    
    display_statistics(db)
    
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Detailed Stats", "Heatmap", "Insights"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            task_freq = db.get_task_frequency()
            freq_chart = create_task_frequency_chart(task_freq)
            if freq_chart:
                st.plotly_chart(freq_chart, use_container_width=True)
        
        with col2:
            category_stats = db.get_category_stats()
            pie_chart = create_category_pie_chart(category_stats)
            if pie_chart:
                st.plotly_chart(pie_chart, use_container_width=True)
        
        df = db.get_analytics_data(days=30)
        timeline_chart = create_timeline_chart(df)
        if timeline_chart:
            st.plotly_chart(timeline_chart, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            completion_rate = db.get_completion_rate()
            gauge_chart = create_completion_gauge(completion_rate)
            if gauge_chart:
                st.plotly_chart(gauge_chart, use_container_width=True)
        
        with col2:
            st.markdown("### Category Performance")
            category_stats = db.get_category_stats()
            if category_stats:
                for stat in category_stats:
                    completed = stat.get('completed', 0) or 0
                    total = stat['total']
                    if total > 0:
                        completion = (completed / total * 100)
                        st.markdown(f"**{stat['category']}**")
                        st.progress(completion / 100)
                        st.caption(f"{completed}/{total} completed ({completion:.1f}%)")
            else:
                st.info("No category data yet")
    
    with tab3:
        df = db.get_analytics_data(days=30)
        heatmap = create_heatmap(df)
        if heatmap:
            st.plotly_chart(heatmap, use_container_width=True)
        else:
            st.info("Build up more history to see the activity heatmap")
    
    with tab4:
        st.markdown("### Key Insights")
        
        task_freq = db.get_task_frequency()
        if task_freq and any(count > 0 for _, count in task_freq):
            most_spun = max(task_freq, key=lambda x: x[1])
            least_spun = min([t for t in task_freq if t[1] > 0], key=lambda x: x[1], default=("None", 0))
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"Most Spun Task: {most_spun[0]} ({most_spun[1]} times)")
            with col2:
                if least_spun[1] > 0:
                    st.info(f"Least Spun Task: {least_spun[0]} ({least_spun[1]} times)")
            
            history = db.get_spin_history(limit=1000)
            if len(history) >= 7:
                recent_week = history[:7]
                last_week = history[7:14] if len(history) >= 14 else []
                
                if last_week:
                    trend = len(recent_week) - len(last_week)
                    if trend > 0:
                        st.success(f"You are spinning {abs(trend)} more times this week")
                    elif trend < 0:
                        st.warning(f"You are spinning {abs(trend)} less times this week")
                    else:
                        st.info("Consistent activity week over week")
        else:
            st.info("Start spinning to see insights")

elif page == "Reports":
    display_report_dashboard(db)

elif page == "Manage Tasks":
    st.title("Manage Tasks")
    
    tab1, tab2 = st.tabs(["Add Task", "Edit Tasks"])
    
    with tab1:
        st.markdown("### Add New Task")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_task_name = st.text_input("Task Name", key="new_task_name")
            new_category = st.text_input("Category", value="General", key="new_category")
        
        with col2:
            new_priority = st.slider("Priority", min_value=1, max_value=5, value=3, key="new_priority")
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.button("Add Task", key="btn_add_task", use_container_width=True):
            if new_task_name:
                db.add_task(new_task_name, new_category, new_priority)
                st.success(f"Added task: {new_task_name}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter a task name")
    
    with tab2:
        st.markdown("### Edit Existing Tasks")
        
        tasks = db.get_all_tasks(active_only=False)
        
        for task in tasks:
            status = "Active" if task['active'] else "Inactive"
            with st.expander(f"{status}: {task['task_name']} - {task['category']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    updated_name = st.text_input(
                        "Task Name", 
                        value=task['task_name'], 
                        key=f"name_{task['id']}"
                    )
                    updated_category = st.text_input(
                        "Category",
                        value=task['category'],
                        key=f"category_{task['id']}"
                    )
                
                with col2:
                    updated_priority = st.slider(
                        "Priority",
                        min_value=1,
                        max_value=5,
                        value=task['priority'],
                        key=f"priority_{task['id']}"
                    )
                    updated_active = st.checkbox(
                        "Active",
                        value=bool(task['active']),
                        key=f"active_{task['id']}"
                    )
                
                col_update, col_delete = st.columns(2)
                
                with col_update:
                    if st.button("Update", key=f"update_{task['id']}", use_container_width=True):
                        db.update_task(
                            task['id'],
                            task_name=updated_name,
                            category=updated_category,
                            priority=updated_priority,
                            active=updated_active
                        )
                        st.success("Task updated")
                        time.sleep(1)
                        st.rerun()
                
                with col_delete:
                    if st.button("Delete", key=f"delete_{task['id']}", use_container_width=True):
                        db.delete_task(task['id'])
                        st.success("Task deleted")
                        time.sleep(1)
                        st.rerun()

elif page == "History":
    st.title("Spin History")
    
    history = db.get_spin_history(limit=100)
    
    if not history:
        st.info("No history yet. Start spinning to build your history")
    else:
        st.markdown(f"### Showing last {len(history)} spins")
        
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            filter_completed = st.selectbox(
                "Filter by status",
                ["All", "Completed", "Incomplete"],
                key="filter_status"
            )
        
        with filter_col2:
            filter_category = st.selectbox(
                "Filter by category",
                ["All"] + list(set(h['category'] for h in history)),
                key="filter_category"
            )
        
        filtered_history = history
        
        if filter_completed == "Completed":
            filtered_history = [h for h in filtered_history if h['completed']]
        elif filter_completed == "Incomplete":
            filtered_history = [h for h in filtered_history if not h['completed']]
        
        if filter_category != "All":
            filtered_history = [h for h in filtered_history if h['category'] == filter_category]
        
        for i, spin in enumerate(filtered_history):
            spin_time = datetime.fromisoformat(spin['spun_at'])
            status = "Completed" if spin['completed'] else "Pending"
            
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{status}**")
                
                with col2:
                    st.markdown(f"**{spin['task_name']}**")
                    st.caption(f"Category: {spin['category']}")
                
                with col3:
                    st.markdown(f"Time: {spin_time.strftime('%Y-%m-%d %I:%M %p')}")
                    if spin['notes']:
                        st.caption(f"Notes: {spin['notes']}")
                
                with col4:
                    if not spin['completed']:
                        if st.button("Mark Complete", key=f"complete_{spin['id']}", use_container_width=True):
                            db.mark_spin_completed(spin['id'], True)
                            st.success("Marked as complete")
                            time.sleep(1)
                            st.rerun()
                
                st.markdown("---")

st.sidebar.markdown("---")
st.sidebar.markdown("### Tips")
st.sidebar.info("""
- Spin daily for best results
- Mark tasks as complete to track progress
- Check analytics to see patterns
- Use reports for insights
""")

st.sidebar.markdown("---")
st.sidebar.caption("Made with Streamlit")
