import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import streamlit as st

def generate_daily_report(db) -> str:
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    history = db.get_spin_history(limit=1000)
    today_spins = [h for h in history if datetime.fromisoformat(h['spun_at']).date() == today]
    
    if not today_spins:
        return "**No activity today yet.** Spin the wheel to get started"
    
    report = f"# Daily Report - {today.strftime('%B %d, %Y')}\n\n"
    report += f"## Summary\n"
    report += f"- **Total Spins Today:** {len(today_spins)}\n"
    
    completed = sum(1 for s in today_spins if s['completed'])
    report += f"- **Completed:** {completed}/{len(today_spins)}\n"
    report += f"- **Completion Rate:** {(completed/len(today_spins)*100):.1f}%\n\n"
    
    report += f"## Tasks Worked On\n"
    for spin in today_spins:
        time = datetime.fromisoformat(spin['spun_at']).strftime('%I:%M %p')
        status = "[Completed]" if spin['completed'] else "[Pending]"
        report += f"{status} **{spin['task_name']}** ({spin['category']}) - {time}\n"
        if spin['notes']:
            report += f"   *Note: {spin['notes']}*\n"
    
    return report

def generate_weekly_report(db) -> str:
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_start_dt = datetime.combine(week_start, datetime.min.time())
    
    history = db.get_spin_history(limit=1000)
    week_spins = [h for h in history if datetime.fromisoformat(h['spun_at']) >= week_start_dt]
    
    if not week_spins:
        return "**No activity this week yet.** Start spinning"
    
    week_end = week_start + timedelta(days=6)
    report = f"# Weekly Report - {week_start.strftime('%b %d')} to {week_end.strftime('%b %d, %Y')}\n\n"
    
    report += f"## Overview\n"
    report += f"- **Total Spins:** {len(week_spins)}\n"
    
    completed = sum(1 for s in week_spins if s['completed'])
    report += f"- **Completed:** {completed}/{len(week_spins)}\n"
    report += f"- **Completion Rate:** {(completed/len(week_spins)*100):.1f}%\n\n"
    
    task_counts = {}
    category_counts = {}
    
    for spin in week_spins:
        task_name = spin['task_name']
        category = spin['category']
        
        task_counts[task_name] = task_counts.get(task_name, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
    
    report += f"## Most Worked Tasks\n"
    sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
    for task, count in sorted_tasks[:5]:
        report += f"- **{task}**: {count} times\n"
    
    report += f"\n## Category Breakdown\n"
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories:
        percentage = (count / len(week_spins) * 100)
        report += f"- **{category}**: {count} spins ({percentage:.1f}%)\n"
    
    daily_activity = {}
    for spin in week_spins:
        day = datetime.fromisoformat(spin['spun_at']).strftime('%A')
        daily_activity[day] = daily_activity.get(day, 0) + 1
    
    report += f"\n## Daily Activity\n"
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days_order:
        count = daily_activity.get(day, 0)
        bar = "█" * count
        report += f"- **{day}**: {bar} ({count})\n"
    
    return report

def generate_monthly_report(db) -> str:
    today = datetime.now().date()
    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    
    history = db.get_spin_history(limit=10000)
    month_spins = [h for h in history if datetime.fromisoformat(h['spun_at']) >= month_start_dt]
    
    if not month_spins:
        return f"**No activity in {today.strftime('%B %Y')} yet.** Get spinning"
    
    report = f"# Monthly Report - {today.strftime('%B %Y')}\n\n"
    
    report += f"## Key Metrics\n"
    report += f"- **Total Spins:** {len(month_spins)}\n"
    
    completed = sum(1 for s in month_spins if s['completed'])
    report += f"- **Completed:** {completed}/{len(month_spins)}\n"
    report += f"- **Completion Rate:** {(completed/len(month_spins)*100):.1f}%\n"
    
    unique_days = len(set(datetime.fromisoformat(s['spun_at']).date() for s in month_spins))
    report += f"- **Active Days:** {unique_days}/{today.day}\n"
    report += f"- **Average Spins/Day:** {len(month_spins)/unique_days:.1f}\n\n"
    
    task_counts = {}
    for spin in month_spins:
        task_name = spin['task_name']
        task_counts[task_name] = task_counts.get(task_name, 0) + 1
    
    report += f"## Top Performing Tasks\n"
    sorted_tasks = sorted(task_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (task, count) in enumerate(sorted_tasks[:10], 1):
        report += f"{i}. **{task}**: {count} times\n"
    
    category_stats = {}
    for spin in month_spins:
        category = spin['category']
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'completed': 0}
        category_stats[category]['total'] += 1
        if spin['completed']:
            category_stats[category]['completed'] += 1
    
    report += f"\n## Category Performance\n"
    for category, stats in sorted(category_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        completion = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        report += f"- **{category}**: {stats['total']} spins, {completion:.1f}% completion\n"
    
    weekly_activity = {}
    for spin in month_spins:
        week_num = (datetime.fromisoformat(spin['spun_at']).day - 1) // 7 + 1
        weekly_activity[f"Week {week_num}"] = weekly_activity.get(f"Week {week_num}", 0) + 1
    
    report += f"\n## Weekly Breakdown\n"
    for week in sorted(weekly_activity.keys()):
        count = weekly_activity[week]
        bar = "█" * (count // 2)
        report += f"- **{week}**: {bar} ({count} spins)\n"
    
    return report

def display_report_dashboard(db):
    st.title("Reports Dashboard")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Daily", "Weekly", "Monthly", "Custom"])
    
    with tab1:
        st.markdown(generate_daily_report(db))
        
        if st.button("Export Daily Report", key="export_daily"):
            report_text = generate_daily_report(db)
            st.download_button(
                label="Download as Text",
                data=report_text,
                file_name=f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    with tab2:
        st.markdown(generate_weekly_report(db))
        
        if st.button("Export Weekly Report", key="export_weekly"):
            report_text = generate_weekly_report(db)
            st.download_button(
                label="Download as Text",
                data=report_text,
                file_name=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    with tab3:
        st.markdown(generate_monthly_report(db))
        
        if st.button("Export Monthly Report", key="export_monthly"):
            report_text = generate_monthly_report(db)
            st.download_button(
                label="Download as Text",
                data=report_text,
                file_name=f"monthly_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
    
    with tab4:
        st.subheader("Custom Date Range Report")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now().date())
        
        if st.button("Generate Custom Report"):
            history = db.get_spin_history(limit=10000)
            filtered_spins = [
                h for h in history 
                if start_date <= datetime.fromisoformat(h['spun_at']).date() <= end_date
            ]
            
            if not filtered_spins:
                st.warning("No data in selected date range")
            else:
                df = pd.DataFrame(filtered_spins)
                
                st.markdown(f"### Custom Report: {start_date} to {end_date}")
                st.write(f"**Total Spins:** {len(filtered_spins)}")
                
                completed = sum(1 for s in filtered_spins if s['completed'])
                st.write(f"**Completion Rate:** {(completed/len(filtered_spins)*100):.1f}%")
                
                st.dataframe(
                    df[['spun_at', 'task_name', 'category', 'completed']],
                    use_container_width=True
                )
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"custom_report_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
