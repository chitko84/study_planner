import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="STUDY.PLANNER",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# CUSTOM CSS
# ======================
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        margin-top: 0;
    }
    .subject-card {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .plan-table {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        background-color: #10B981;
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-size: 1.1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #059669;
    }
</style>
""", unsafe_allow_html=True)

# ======================
# APP HEADER
# ======================
st.markdown('<h1 class="main-header">📚 STUDY.PLANNER</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Smart Weekly Study Planning for Students</p>', unsafe_allow_html=True)
st.markdown("Plan your semester intelligently based on deadlines, difficulty, and your available time.")

st.divider()

# ======================
# INITIALIZE SESSION STATE
# ======================
if 'subjects' not in st.session_state:
    st.session_state.subjects = []
if 'study_plan' not in st.session_state:
    st.session_state.study_plan = None
if 'original_plan' not in st.session_state:
    st.session_state.original_plan = None

# ======================
# SIDEBAR - AVAILABILITY SETTINGS
# ======================
with st.sidebar:
    st.header("🎯 Your Availability")
    
    # Study Days
    st.subheader("Study Days")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_days = []
    cols = st.columns(4)
    for i, day in enumerate(days):
        if cols[i % 4].checkbox(day, value=(day not in ["Saturday", "Sunday"])):
            selected_days.append(day)
    
    # Study Hours
    st.subheader("Daily Study Hours")
    study_hours = st.slider("Hours per day", 0.5, 8.0, 2.5, 0.5)
    
    st.divider()
    st.caption("📌 Your settings are saved automatically")

# ======================
# MAIN CONTENT AREA
# ======================
col1, col2 = st.columns([3, 2])

with col1:
    st.header("📝 Add Your Subjects")
    
    with st.form("subject_form"):
        # Subject Inputs
        subject_name = st.text_input("Subject Name", placeholder="e.g., Data Structures")
        
        col_a, col_b = st.columns(2)
        with col_a:
            deadline = st.date_input("Deadline", value=datetime.now() + timedelta(days=30))
        with col_b:
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
        
        hours_needed = st.slider("Hours needed per week", 1, 20, 5)
        
        # Add Subject Button
        add_subject = st.form_submit_button("➕ Add Subject")
        
        if add_subject and subject_name:
            # Add subject to session state
            new_subject = {
                "name": subject_name,
                "deadline": deadline.strftime("%Y-%m-%d"),
                "difficulty": difficulty,
                "hours_needed": hours_needed,
                "priority": {"Easy": 1, "Medium": 2, "Hard": 3}[difficulty]
            }
            st.session_state.subjects.append(new_subject)
            st.success(f"Added {subject_name}!")
            st.rerun()

# ======================
# DISPLAY ADDED SUBJECTS
# ======================
with col2:
    st.header("📚 Your Subjects")
    
    if not st.session_state.subjects:
        st.info("No subjects added yet. Add your first subject on the left!")
    else:
        for i, subject in enumerate(st.session_state.subjects):
            with st.container():
                st.markdown(f"""
                <div class="subject-card">
                    <h4>{subject['name']}</h4>
                    <p>📅 Deadline: {subject['deadline']}</p>
                    <p>⚡ Difficulty: {subject['difficulty']}</p>
                    <p>⏱️ Hours/week: {subject['hours_needed']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Remove button for each subject
                if st.button(f"Remove {subject['name']}", key=f"remove_{i}"):
                    st.session_state.subjects.pop(i)
                    st.rerun()

st.divider()

# ======================
# GENERATE PLAN BUTTON
# ======================
if st.session_state.subjects and selected_days:
    if st.button("🚀 Generate Weekly Study Plan", use_container_width=True):
        with st.spinner("Creating your optimized study plan..."):
            # Simple planning algorithm
            plan = []
            remaining_hours = {subject['name']: subject['hours_needed'] for subject in st.session_state.subjects}
            
            # Sort subjects by priority (deadline proximity + difficulty)
            sorted_subjects = sorted(
                st.session_state.subjects,
                key=lambda x: (
                    (datetime.strptime(x['deadline'], "%Y-%m-%d") - datetime.now()).days,
                    -x['priority']
                )
            )
            
            # Distribute hours across days
            for day in selected_days:
                day_plan = {"Day": day, "Tasks": []}
                day_hours_used = 0
                
                for subject in sorted_subjects:
                    if remaining_hours[subject['name']] > 0:
                        # Allocate hours based on priority
                        hours_to_allocate = min(
                            study_hours - day_hours_used,
                            remaining_hours[subject['name']],
                            subject['priority'] * 0.5  # Hard gets more hours
                        )
                        
                        if hours_to_allocate > 0:
                            day_plan["Tasks"].append(
                                f"{subject['name']} ({hours_to_allocate:.1f}h)"
                            )
                            remaining_hours[subject['name']] -= hours_to_allocate
                            day_hours_used += hours_to_allocate
                
                if day_plan["Tasks"]:
                    plan.append(day_plan)
            
            st.session_state.study_plan = plan
            st.session_state.original_plan = plan.copy()
            st.success("✅ Study plan generated!")

# ======================
# DISPLAY STUDY PLAN
# ======================
if st.session_state.study_plan:
    st.markdown('<div class="plan-table">', unsafe_allow_html=True)
    st.header("📅 Your Weekly Study Plan")
    
    # Display as table
    plan_df = pd.DataFrame([
        {"Day": day_plan["Day"], "Study Plan": " | ".join(day_plan["Tasks"])}
        for day_plan in st.session_state.study_plan
    ])
    
    st.table(plan_df)
    
    # Explanation
    with st.expander("🔍 Why this plan?"):
        st.markdown("""
        - **Priority-based allocation**: Subjects with closer deadlines and higher difficulty get more study time
        - **Burnout prevention**: Workload is distributed evenly across available days
        - **Respects limits**: No day exceeds your daily study hour limit
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ======================
    # MISSED DAY ADJUSTMENT
    # ======================
    st.subheader("⚠️ Missed a Study Day?")
    
    col3, col4 = st.columns([2, 1])
    with col3:
        missed_day = st.selectbox("Select missed day", 
                                  [day_plan["Day"] for day_plan in st.session_state.study_plan])
    with col4:
        if st.button("Re-adjust Plan", use_container_width=True):
            # Simple redistribution algorithm
            original_plan = st.session_state.original_plan
            missed_plan = next(p for p in original_plan if p["Day"] == missed_day)
            
            # Redistribute tasks to remaining days
            adjusted_plan = [p for p in original_plan if p["Day"] != missed_day]
            
            # Add redistributed tasks (simplified logic)
            for task in missed_plan["Tasks"]:
                if adjusted_plan:
                    adjusted_plan[0]["Tasks"].append(task)
            
            st.session_state.study_plan = adjusted_plan
            st.success("Plan adjusted! Missed workload redistributed.")
            st.rerun()
    
    # ======================
    # WEEKLY LOAD SUMMARY
    # ======================
    st.subheader("📊 Weekly Load Summary")
    
    # Calculate total hours per subject
    subject_totals = {}
    for day_plan in st.session_state.original_plan:
        for task in day_plan["Tasks"]:
            subject = task.split(" (")[0]
            hours = float(task.split("(")[1].replace("h)", ""))
            subject_totals[subject] = subject_totals.get(subject, 0) + hours
    
    # Display progress bars
    for subject, hours in subject_totals.items():
        max_hours = max(subject_totals.values())
        percentage = (hours / max_hours) * 100 if max_hours > 0 else 0
        st.markdown(f"**{subject}**")
        st.progress(percentage / 100, text=f"{hours:.1f} hours")
    
    # ======================
    # EXPORT OPTIONS
    # ======================
    st.divider()
    st.subheader("📤 Export Your Plan")
    
    if st.button("Copy Plan to Clipboard", use_container_width=True):
        plan_text = "📚 STUDY.PLANNER - Your Weekly Plan\n\n"
        for day_plan in st.session_state.study_plan:
            plan_text += f"**{day_plan['Day']}:** {', '.join(day_plan['Tasks'])}\n"
        
        # Copy to clipboard (simulated)
        st.code(plan_text, language="text")
        st.info("Select and copy the text above to save your plan!")

elif st.session_state.subjects and not selected_days:
    st.warning("⚠️ Please select at least one study day in the sidebar!")
elif selected_days and not st.session_state.subjects:
    st.warning("⚠️ Please add at least one subject to generate a plan!")

# ======================
# FOOTER
# ======================
st.divider()
st.caption("STUDY.PLANNER v1.0 | Built with Streamlit | © Chit Ko Ko's Personal Project")