import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import io

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
    .time-slot {
        background-color: #E0F2FE;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
    }
    .prayer-time {
        background-color: #FEF3C7;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.9rem;
    }
    .day-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# ======================
# ISLAMIC PRAYER TIMES (Alor Setar, Malaysia - 24 Dec 2025)
# ======================
ISLAMIC_PRAYER_TIMES = {
    "Fajr": "06:12 AM",
    "Sunrise": "07:25 AM",
    "Dhuhr": "01:19 PM",
    "Asr": "04:41 PM",
    "Maghrib": "07:12 PM",
    "Isha": "08:27 PM"
}

# Break times (lunch, dinner, snacks)
BREAK_TIMES = {
    "Lunch Break": "12:00 PM - 01:00 PM",
    "Dinner Break": "06:30 PM - 07:30 PM",
    "Snack Break (Morning)": "10:30 AM - 10:45 AM",
    "Snack Break (Afternoon)": "03:30 PM - 03:45 PM"
}

# ======================
# HELPER FUNCTIONS
# ======================
def create_pdf(study_plan, subjects, study_hours, selected_days):
    """Create a PDF document from the study plan"""
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1E3A8A')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2563EB')
    )
    
    # Title
    elements.append(Paragraph("STUDY.PLANNER - Weekly Study Plan", title_style))
    elements.append(Spacer(1, 20))
    
    # Study Settings Summary
    elements.append(Paragraph("Study Settings Summary", heading_style))
    settings_data = [
        ["Study Days", ", ".join(selected_days)],
        ["Daily Study Hours", f"{study_hours} hours"],
        ["Total Subjects", str(len(subjects))],
        ["Generated On", datetime.now().strftime("%Y-%m-%d %H:%M")]
    ]
    
    settings_table = Table(settings_data, colWidths=[2.5*inch, 3.5*inch])
    settings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(settings_table)
    elements.append(Spacer(1, 30))
    
    # Weekly Study Plan
    elements.append(Paragraph("Weekly Study Plan", heading_style))
    
    plan_data = [["Day", "Study Plan"]]
    for day_plan in study_plan:
        # Clean day name - remove duplicate "Day X: " prefix
        day_name = day_plan["Day"]
        if day_name.startswith("Day "):
            parts = day_name.split(": ", 1)
            if len(parts) == 2:
                day_display = parts[1]
            else:
                day_display = day_name
        else:
            day_display = day_name
        
        # Format tasks
        tasks_text = ", ".join(day_plan["Tasks"])
        # Wrap text for better PDF display
        wrapped_tasks = []
        current_line = ""
        for task in day_plan["Tasks"]:
            if len(current_line) + len(task) + 2 > 60:  # Approximate line length
                wrapped_tasks.append(current_line)
                current_line = task
            else:
                if current_line:
                    current_line += ", " + task
                else:
                    current_line = task
        if current_line:
            wrapped_tasks.append(current_line)
        
        tasks_display = "<br/>".join(wrapped_tasks)
        plan_data.append([day_display, Paragraph(tasks_display, styles["Normal"])])
    
    plan_table = Table(plan_data, colWidths=[2*inch, 4.5*inch])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))
    elements.append(plan_table)
    elements.append(Spacer(1, 30))
    
    # Subjects Summary
    elements.append(Paragraph("Subjects Summary", heading_style))
    
    subject_data = [["Subject", "Deadline", "Difficulty", "Hours/Week"]]
    for subject in subjects:
        subject_data.append([
            subject['name'],
            subject['deadline'],
            subject['difficulty'],
            str(subject['hours_needed'])
        ])
    
    subject_table = Table(subject_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch])
    subject_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(subject_table)
    
    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Generated by STUDY.PLANNER - Smart Weekly Study Planning for Students", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                                          textColor=colors.grey, alignment=1)))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

def is_time_conflict(time_str, prayer_times, break_times):
    """Check if a time slot conflicts with prayer or break times"""
    slot_start_str = time_str.split(" - ")[0]
    slot_end_str = time_str.split(" - ")[1]
    
    # Convert to datetime for comparison
    def to_datetime(time_str):
        return datetime.strptime(time_str.strip(), "%I:%M %p")
    
    slot_start = to_datetime(slot_start_str)
    slot_end = to_datetime(slot_end_str)
    
    # Check prayer times (10 minutes for each prayer)
    for prayer, prayer_time in prayer_times.items():
        prayer_start = to_datetime(prayer_time)
        prayer_end = prayer_start + timedelta(minutes=10)
        
        if not (slot_end <= prayer_start or slot_start >= prayer_end):
            return True
    
    # Check break times
    for break_name, break_range in break_times.items():
        break_start_str, break_end_str = break_range.split(" - ")
        break_start = to_datetime(break_start_str)
        break_end = to_datetime(break_end_str)
        
        if not (slot_end <= break_start or slot_start >= break_end):
            return True
    
    return False

def assign_study_times(tasks, preferred_times, study_hours_per_day, prayer_times=None, break_times=None):
    """Assign specific time slots to study tasks based on preferences, avoiding prayer and break times"""
    if not preferred_times:
        return []
    
    if prayer_times is None:
        prayer_times = ISLAMIC_PRAYER_TIMES
    if break_times is None:
        break_times = BREAK_TIMES
    
    time_slots = []
    
    # Create time slots based on preferred times
    for time_range in preferred_times:
        start_time_str, end_time_str = time_range.split(" - ")
        start_time = datetime.strptime(start_time_str.strip(), "%I:%M %p")
        end_time = datetime.strptime(end_time_str.strip(), "%I:%M %p")
        
        # Calculate duration in hours
        duration = (end_time - start_time).seconds / 3600
        
        # Divide into slots (each slot = 30 minutes)
        num_slots = int(duration * 2)
        for i in range(num_slots):
            slot_start = start_time + timedelta(minutes=30 * i)
            slot_end = slot_start + timedelta(minutes=30)
            slot_time_str = f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
            
            # Check if this slot conflicts with prayer or break times
            if not is_time_conflict(slot_time_str, prayer_times, break_times):
                time_slots.append({
                    'time': slot_time_str,
                    'available': True,
                    'task': None,
                    'duration': 0.5  # 30 minutes = 0.5 hours
                })
    
    if not time_slots:
        return []
    
    # Sort tasks by hours (descending)
    sorted_tasks = []
    for task_str in tasks:
        task_name = task_str.split(" (")[0]
        task_hours = float(task_str.split("(")[1].replace("h)", ""))
        sorted_tasks.append((task_name, task_hours))
    
    sorted_tasks.sort(key=lambda x: x[1], reverse=True)
    
    # Assign tasks to time slots
    task_index = 0
    slot_index = 0
    
    while task_index < len(sorted_tasks) and slot_index < len(time_slots):
        task_name, task_hours = sorted_tasks[task_index]
        
        # Find consecutive available slots for this task
        slots_needed = int(task_hours * 2)  # Convert hours to 30-min slots
        
        # Check if we have enough consecutive available slots
        consecutive_slots = 0
        available_start_index = -1
        
        for i in range(slot_index, len(time_slots)):
            if time_slots[i]['available']:
                if available_start_index == -1:
                    available_start_index = i
                consecutive_slots += 1
                if consecutive_slots >= slots_needed:
                    break
            else:
                consecutive_slots = 0
                available_start_index = -1
        
        # If we have enough slots, assign the task
        if consecutive_slots >= slots_needed:
            for i in range(slots_needed):
                time_slots[available_start_index + i]['task'] = task_name
                time_slots[available_start_index + i]['available'] = False
            
            task_index += 1
            slot_index = available_start_index + slots_needed
        else:
            # Move to next slot if current one isn't available
            slot_index += 1
    
    # Filter out only slots with assigned tasks
    assigned_slots = [slot for slot in time_slots if slot['task'] is not None]
    
    return assigned_slots

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
if 'preferred_times' not in st.session_state:
    st.session_state.preferred_times = ["08:00 AM - 10:00 AM", "02:00 PM - 04:00 PM"]
if 'study_hours' not in st.session_state:
    st.session_state.study_hours = 2.5
if 'selected_days' not in st.session_state:
    st.session_state.selected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

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
        if cols[i % 4].checkbox(day, value=(day in st.session_state.selected_days), key=f"day_{day}"):
            selected_days.append(day)
    
    # Study Hours
    st.subheader("Daily Study Hours")
    study_hours = st.slider("Hours per day", 0.5, 8.0, st.session_state.study_hours, 0.5, key="daily_hours")
    
    # Maximum subjects per day
    st.subheader("📊 Study Limits")
    max_subjects_per_day = st.slider(
        "Maximum subjects per day", 
        1, 10, 5,
        help="Limit how many different subjects you study each day to avoid overload"
    )
    
    # Minimum study session length
    min_session_hours = st.slider(
        "Minimum study session (hours)",
        0.5, 3.0, 1.0, 0.5,
        help="Minimum continuous time to allocate for each subject"
    )
    
    # Preferred Study Times
    st.subheader("⏰ Preferred Study Times")
    st.markdown("Select your preferred study time slots:")
    
    # Time slots selection
    time_slots_options = [
        "06:00 AM - 08:00 AM",
        "08:00 AM - 10:00 AM", 
        "10:00 AM - 12:00 PM",
        "12:00 PM - 02:00 PM",
        "02:00 PM - 04:00 PM",
        "04:00 PM - 06:00 PM",
        "06:00 PM - 08:00 PM",
        "08:00 PM - 10:00 PM"
    ]
    
    preferred_times = st.multiselect(
        "Choose your preferred time slots:",
        time_slots_options,
        default=st.session_state.preferred_times,
        help="Select time windows when you prefer to study"
    )
    
    # Islamic Prayer Times & Breaks
    st.subheader("🕌 Prayer Times & Breaks")
    with st.expander("View/Customize Schedule Conflicts"):
        st.info("These times are automatically excluded from your study schedule")
        
        st.markdown("**Islamic Prayer Times (Alor Setar):**")
        for prayer, time in ISLAMIC_PRAYER_TIMES.items():
            st.markdown(f"- **{prayer}:** {time} (10 minutes)")
        
        st.markdown("**Break Times:**")
        for break_name, time_range in BREAK_TIMES.items():
            st.markdown(f"- **{break_name}:** {time_range}")
    
    # Save to session state
    st.session_state.selected_days = selected_days
    st.session_state.study_hours = study_hours
    st.session_state.preferred_times = preferred_times
    
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
        
        hours_needed = st.slider("Hours needed per week", 1, 30, 5)
        
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
        # Create a scrollable container for subjects
        with st.container():
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
            # Improved planning algorithm
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
            
            # Calculate total weekly hours needed
            total_weekly_hours_needed = sum(subject['hours_needed'] for subject in st.session_state.subjects)
            total_available_hours = len(selected_days) * study_hours
            
            if total_weekly_hours_needed > total_available_hours:
                st.warning(f"⚠️ Warning: You need {total_weekly_hours_needed} hours/week but only have {total_available_hours} available. Consider reducing study hours or adding more days.")
            
            # Distribute hours across days (starting from Day 1)
            day_number = 1
            for day in selected_days:
                # Clean day name
                clean_day_name = day.split(": ")[-1] if ": " in day else day
                day_plan = {"Day": f"Day {day_number}: {clean_day_name}", "Tasks": [], "TimeSlots": []}
                day_hours_used = 0
                
                # Calculate how many subjects we can reasonably fit today
                subjects_today = min(max_subjects_per_day, len(sorted_subjects))
                
                # Round-robin allocation for multiple subjects
                for subject in sorted_subjects:
                    if remaining_hours[subject['name']] > 0 and len(day_plan["Tasks"]) < subjects_today:
                        # Calculate allocation based on priority and minimum session
                        hours_to_allocate = min(
                            study_hours - day_hours_used,
                            remaining_hours[subject['name']],
                            max(min_session_hours, subject['priority'] * 0.75)  # Adjusted multiplier
                        )
                        
                        if hours_to_allocate >= min_session_hours:  # Only allocate if meets minimum
                            day_plan["Tasks"].append(
                                f"{subject['name']} ({hours_to_allocate:.1f}h)"
                            )
                            remaining_hours[subject['name']] -= hours_to_allocate
                            day_hours_used += hours_to_allocate
                
                if day_plan["Tasks"]:
                    # Assign time slots if preferred times are selected
                    if st.session_state.preferred_times:
                        time_slots = assign_study_times(
                            day_plan["Tasks"], 
                            st.session_state.preferred_times, 
                            study_hours
                        )
                        day_plan["TimeSlots"] = time_slots
                    
                    plan.append(day_plan)
                    day_number += 1
            
            # If there are still remaining hours, redistribute
            if any(hours > 0 for hours in remaining_hours.values()):
                # Add extra study sessions on existing days
                for day_plan in plan:
                    if day_plan["Tasks"]:
                        day_hours_used = sum(float(task.split("(")[1].replace("h)", "")) for task in day_plan["Tasks"])
                        remaining_day_capacity = study_hours - day_hours_used
                        
                        if remaining_day_capacity > min_session_hours:
                            # Try to add more hours to existing subjects in this day
                            for subject_name, hours_left in remaining_hours.items():
                                if hours_left > 0 and remaining_day_capacity >= min_session_hours:
                                    # Find if this subject is already in today's tasks
                                    subject_in_today = any(subject_name in task for task in day_plan["Tasks"])
                                    
                                    if subject_in_today and len(day_plan["Tasks"]) < max_subjects_per_day:
                                        hours_to_add = min(remaining_day_capacity, hours_left, min_session_hours * 2)
                                        day_plan["Tasks"].append(f"{subject_name} (+{hours_to_add:.1f}h)")
                                        remaining_hours[subject_name] -= hours_to_add
                                        remaining_day_capacity -= hours_to_add
            
            st.session_state.study_plan = plan
            st.session_state.original_plan = plan.copy()
            st.success("✅ Study plan generated!")

# ======================
# DISPLAY STUDY PLAN
# ======================
if st.session_state.study_plan:
    st.markdown('<div class="plan-table">', unsafe_allow_html=True)
    st.header("📅 Your Weekly Study Plan")
    
    # Display summary statistics
    total_planned_hours = 0
    total_days = len(st.session_state.study_plan)
    subjects_per_day_stats = []
    
    for day_plan in st.session_state.study_plan:
        day_hours = sum(float(task.split("(")[1].replace("h)", "")) for task in day_plan["Tasks"])
        total_planned_hours += day_hours
        subjects_per_day_stats.append(len(day_plan["Tasks"]))
    
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Days", total_days)
    with col_stats2:
        avg_subjects = sum(subjects_per_day_stats) / len(subjects_per_day_stats) if subjects_per_day_stats else 0
        st.metric("Avg Subjects/Day", f"{avg_subjects:.1f}")
    with col_stats3:
        st.metric("Total Planned Hours", f"{total_planned_hours:.1f}h")
    
    # Display prayer times and breaks
    with st.expander("🕌 Today's Prayer & Break Times"):
        col_prayer1, col_prayer2 = st.columns(2)
        with col_prayer1:
            st.markdown("**Islamic Prayer Times:**")
            for prayer, time in ISLAMIC_PRAYER_TIMES.items():
                st.markdown(f'<div class="prayer-time">{prayer}: {time}</div>', unsafe_allow_html=True)
        
        with col_prayer2:
            st.markdown("**Break Times:**")
            for break_name, time_range in BREAK_TIMES.items():
                st.markdown(f'<div class="prayer-time">{break_name}: {time_range}</div>', unsafe_allow_html=True)
    
    # Display with time slots if available - using a scrollable container
    for day_plan in st.session_state.study_plan:
        with st.expander(f"📌 {day_plan['Day']}", expanded=False):
            st.markdown(f"**Total Study Time: {sum(float(task.split('(')[1].replace('h)', '')) for task in day_plan['Tasks']):.1f}h**")
            st.markdown("**Study Tasks:**")
            
            # Group tasks by subject (in case of multiple sessions)
            task_groups = {}
            for task in day_plan["Tasks"]:
                subject = task.split(" (")[0]
                hours = float(task.split("(")[1].replace("h)", ""))
                if subject not in task_groups:
                    task_groups[subject] = 0
                task_groups[subject] += hours
            
            for subject, total_hours in task_groups.items():
                st.markdown(f"- **{subject}:** {total_hours:.1f}h")
            
            # Display time slots if available
            if day_plan.get('TimeSlots'):
                st.markdown("**📅 Time Schedule:**")
                
                # Group time slots by task
                task_slots = {}
                for slot in day_plan['TimeSlots']:
                    if slot['task'] not in task_slots:
                        task_slots[slot['task']] = []
                    task_slots[slot['task']].append(slot['time'])
                
                # Display grouped time slots
                for task_name, times in task_slots.items():
                    if times:
                        # Combine consecutive times
                        start_time = times[0].split(" - ")[0]
                        end_time = times[-1].split(" - ")[1]
                        duration_hours = len(times) * 0.5  # 30 min slots
                        st.markdown(f"<div class='time-slot'>{start_time} - {end_time}: {task_name} ({duration_hours:.1f}h)</div>", 
                                  unsafe_allow_html=True)
            else:
                if st.session_state.preferred_times:
                    st.info("⚠️ No available time slots that don't conflict with prayer/break times. Try selecting different preferred times.")
                else:
                    st.info("No specific time slots assigned. Add preferred study times in the sidebar!")
    
    # Explanation
    with st.expander("🔍 Plan Details & Tips"):
        st.markdown(f"""
        - **Priority-based allocation**: Subjects with closer deadlines and higher difficulty get more study time
        - **Burnout prevention**: Limited to {max_subjects_per_day} subjects/day maximum
        - **Effective sessions**: Minimum {min_session_hours}h per subject for focused learning
        - **Respects limits**: No day exceeds your {study_hours}h daily study limit
        - **Time preferences**: Schedule respects your preferred study times
        - **Prayer & break times**: Automatically excludes Islamic prayer times (10 min each) and meal breaks
        
        **📊 Distribution:**
        - Average subjects per day: {sum(subjects_per_day_stats)/len(subjects_per_day_stats):.1f}
        - Total weekly study hours: {total_planned_hours:.1f}h
        - Study days this week: {total_days}
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ======================
    # MISSED DAY ADJUSTMENT
    # ======================
    st.subheader("⚠️ Missed a Study Day?")
    
    col3, col4 = st.columns([2, 1])
    with col3:
        available_days = [day_plan["Day"] for day_plan in st.session_state.study_plan]
        if available_days:
            missed_day = st.selectbox("Select missed day", available_days)
        else:
            missed_day = None
            st.warning("No study days available")
    with col4:
        if missed_day and st.button("Re-adjust Plan", use_container_width=True):
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
            subject = task.split(" (")[0].replace(" (+", "")  # Handle extra sessions
            hours = float(task.split("(")[1].replace("h)", "").replace("+", ""))
            subject_totals[subject] = subject_totals.get(subject, 0) + hours
    
    # Display progress bars
    if subject_totals:
        max_hours = max(subject_totals.values())
        for subject, hours in subject_totals.items():
            percentage = (hours / max_hours) * 100 if max_hours > 0 else 0
            col_prog1, col_prog2 = st.columns([1, 4])
            with col_prog1:
                st.markdown(f"**{subject}**")
            with col_prog2:
                st.progress(percentage / 100, text=f"{hours:.1f} hours")
    
    # ======================
    # EXPORT OPTIONS
    # ======================
    st.divider()
    st.subheader("📤 Export Your Plan")
    
    col_export1, col_export2 = st.columns(2)
    
    with col_export1:
        if st.button("📋 Copy Plan to Clipboard", use_container_width=True):
            plan_text = "📚 STUDY.PLANNER - Your Weekly Plan\n\n"
            plan_text += f"Settings: {max_subjects_per_day} subjects/day max, {min_session_hours}h min sessions\n\n"
            plan_text += "🕌 Prayer Times (10 min each):\n"
            for prayer, time in ISLAMIC_PRAYER_TIMES.items():
                plan_text += f"  - {prayer}: {time}\n"
            
            plan_text += "\n🍽️ Break Times:\n"
            for break_name, time_range in BREAK_TIMES.items():
                plan_text += f"  - {break_name}: {time_range}\n"
            
            plan_text += "\n📅 Study Schedule:\n"
            for day_plan in st.session_state.study_plan:
                plan_text += f"\n**{day_plan['Day']}:**\n"
                for task in day_plan['Tasks']:
                    plan_text += f"  - {task}\n"
                if day_plan.get('TimeSlots'):
                    plan_text += "  Time Schedule:\n"
                    for slot in day_plan['TimeSlots']:
                        plan_text += f"    - {slot['time']}: {slot['task']}\n"
            
            # Copy to clipboard (simulated)
            st.code(plan_text, language="text")
            st.info("Select and copy the text above to save your plan!")
    
    with col_export2:
        # PDF Export
        if st.button("📄 Export to PDF", use_container_width=True):
            with st.spinner("Generating PDF..."):
                # Clean day names for PDF
                clean_selected_days = []
                for day in selected_days:
                    clean_day = day.split(": ")[-1] if ": " in day else day
                    clean_selected_days.append(clean_day)
                
                pdf_buffer = create_pdf(
                    st.session_state.study_plan,
                    st.session_state.subjects,
                    st.session_state.study_hours,
                    clean_selected_days
                )
                
                # Provide download button
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_buffer,
                    file_name=f"study_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("PDF generated! Click download to save.")

elif st.session_state.subjects and not selected_days:
    st.warning("⚠️ Please select at least one study day in the sidebar!")
elif selected_days and not st.session_state.subjects:
    st.warning("⚠️ Please add at least one subject to generate a plan!")

# ======================
# FOOTER
# ======================
st.divider()
st.caption("STUDY.PLANNER v2.2 | Built with Streamlit | © Chit Ko Ko's Personal Project")
