import streamlit as st
import json
import os
from datetime import datetime
import hashlib

# ====================== CONFIG ======================
st.set_page_config(
    page_title="CELTA Tutor Desk",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "data.json"

# ====================== HELPERS ======================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Default structure
    return {
        "teacher": {
            "username": "teacher",
            "password": hash_password("CeltaDesk#2026")
        },
        "students": {}
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# ====================== LOGIN ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.name = None

def login_page():
    st.title("📘 CELTA Tutor Desk")
    st.subheader("Login")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary", use_container_width=True):
            # Check Teacher
            if username == data["teacher"]["username"] and hash_password(password) == data["teacher"]["password"]:
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.session_state.name = "Teacher"
                st.rerun()

            # Check Students
            for sid, student in data["students"].items():
                if student.get("username") == username and student.get("password") == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.role = "student"
                    st.session_state.user_id = sid
                    st.session_state.name = student["name"]
                    st.rerun()

            st.error("Incorrect username or password")

# ====================== TEACHER DASHBOARD ======================
def teacher_dashboard():
    with st.sidebar:
        st.title("📘 Teacher Panel")
        st.caption(f"Logged in as Teacher")
        st.divider()
        menu = st.radio("Menu", ["Students", "Live Lesson", "History", "Create Student Login", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    # ---------- CREATE STUDENT LOGIN ----------
    if menu == "Create Student Login":
        st.header("Create Student Login")
        st.info("Create a username and password so the student can log in and see their progress.")

        with st.form("create_student"):
            name = st.text_input("Student Full Name")
            level = st.selectbox("CEFR Level", ["A1", "A2", "B1", "B2", "C1", "C2"])
            goals = st.text_area("Learning Goals")
            username = st.text_input("Username (for student login)")
            password = st.text_input("Password (for student login)", type="password")

            submitted = st.form_submit_button("Create Student", type="primary")

            if submitted:
                if name and username and password:
                    student_id = name.lower().replace(" ", "_") + "_" + str(int(datetime.now().timestamp()))
                    data["students"][student_id] = {
                        "name": name,
                        "username": username,
                        "password": hash_password(password),
                        "level": level,
                        "goals": goals,
                        "sessions": [],
                        "homework": []
                    }
                    save_data(data)
                    st.success(f"Student '{name}' created successfully!\nUsername: {username}")
                else:
                    st.warning("Please fill all required fields.")

    # ---------- STUDENTS LIST ----------
    elif menu == "Students":
        st.header("Students")
        if not data["students"]:
            st.info("No students yet. Create one from 'Create Student Login'.")
        else:
            for sid, student in data["students"].items():
                with st.container(border=True):
                    st.markdown(f"**{student['name']}** · `{student['level']}`")
                    st.caption(f"Username: `{student['username']}`")
                    if student.get("goals"):
                        st.caption(student["goals"][:100])

    # ---------- LIVE LESSON ----------
    elif menu == "Live Lesson":
        st.header("Live Lesson")

        if not data["students"]:
            st.warning("Please create a student first.")
        else:
            student_options = {sid: f"{s['name']} ({s['level']})" for sid, s in data["students"].items()}
            selected_id = st.selectbox("Select Student", options=list(student_options.keys()),
                                       format_func=lambda x: student_options[x])
            student = data["students"][selected_id]

            st.markdown(f"### 👤 {student['name']} · {student['level']}")
            if student.get("goals"):
                st.caption(f"**Goals:** {student['goals']}")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                focus = st.selectbox("Today's Focus",
                                     ["Grammar", "Vocabulary", "Speaking Fluency", "Listening",
                                      "Reading", "Writing", "Pronunciation", "Mixed Skills"])
            with col2:
                topic = st.text_input("Topic / Context")

            st.divider()
            st.subheader("🔴 Live Error Log")

            if "errors" not in st.session_state:
                st.session_state.errors = []

            error_input = st.text_input("Type student error and press Enter", key="error_input")
            if error_input and error_input.strip():
                st.session_state.errors.append(error_input.strip())
                st.session_state.error_input = ""
                st.rerun()

            if st.session_state.errors:
                for i, err in enumerate(st.session_state.errors):
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        st.write(f"{i+1}. {err}")
                    with c2:
                        if st.button("❌", key=f"rm_{i}"):
                            st.session_state.errors.pop(i)
                            st.rerun()

            st.divider()
            notes = st.text_area("Session Notes")

            if st.button("💾 Save Lesson", type="primary"):
                session = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "focus": focus,
                    "topic": topic,
                    "errors": st.session_state.errors.copy(),
                    "notes": notes
                }
                data["students"][selected_id]["sessions"].append(session)
                save_data(data)
                st.session_state.errors = []
                st.success("Lesson saved!")
                st.balloons()

    # ---------- HISTORY ----------
    elif menu == "History":
        st.header("Student History")
        if not data["students"]:
            st.info("No students yet.")
        else:
            student_options = {sid: f"{s['name']} ({s['level']})" for sid, s in data["students"].items()}
            selected_id = st.selectbox("Select Student", options=list(student_options.keys()),
                                       format_func=lambda x: student_options[x])
            student = data["students"][selected_id]

            if not student["sessions"]:
                st.info("No lessons recorded yet.")
            else:
                for session in reversed(student["sessions"]):
                    with st.expander(f"{session['date']} · {session['focus']}"):
                        st.write(f"**Notes:** {session.get('notes', '—')}")
                        if session.get("errors"):
                            st.write("**Errors:**")
                            for e in session["errors"]:
                                st.write(f"• {e}")

# ====================== STUDENT DASHBOARD ======================
def student_dashboard():
    student = data["students"][st.session_state.user_id]

    with st.sidebar:
        st.title("📘 My Progress")
        st.caption(f"Hello, {student['name']}")
        st.divider()
        menu = st.radio("Menu", ["My Lessons", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    st.header(f"Welcome, {student['name']}")
    st.caption(f"Level: {student['level']}")
    if student.get("goals"):
        st.info(f"**Your Goals:** {student['goals']}")

    st.divider()
    st.subheader("Your Past Lessons")

    if not student["sessions"]:
        st.info("No lessons recorded yet.")
    else:
        for session in reversed(student["sessions"]):
            with st.expander(f"{session['date']} · {session['focus']} · {session.get('topic', '')}"):
                st.write(f"**Teacher Notes:** {session.get('notes', '—')}")
                if session.get("errors"):
                    st.write("**Errors from that lesson:**")
                    for e in session["errors"]:
                        st.write(f"• {e}")
                else:
                    st.caption("No errors recorded.")

# ====================== MAIN ======================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "teacher":
        teacher_dashboard()
    elif st.session_state.role == "student":
        student_dashboard()
