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

# ====================== SESSION STATE ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.name = None

if "errors" not in st.session_state:
    st.session_state.errors = []

# ====================== LOGIN PAGE ======================
def login_page():
    st.title("📘 CELTA Tutor Desk")
    st.subheader("Login")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary", use_container_width=True):
            # Teacher login
            if username == data["teacher"]["username"] and hash_password(password) == data["teacher"]["password"]:
                st.session_state.logged_in = True
                st.session_state.role = "teacher"
                st.session_state.name = "Teacher"
                st.rerun()

            # Student login
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
        st.caption("Logged in as Teacher")
        st.divider()
        menu = st.radio("Menu", ["Students", "Live Lesson", "History", "Create Student Login", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.errors = []
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
                    st.success(f"Student '{name}' created successfully! Username: {username}")
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
                        st.caption(student["goals"][:120])

    # ---------- LIVE LESSON ----------
    elif menu == "Live Lesson":
        st.header("Live Lesson")

        if not data["students"]:
            st.warning
