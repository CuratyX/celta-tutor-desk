import streamlit as st
import json
import os
from datetime import datetime
import hashlib

st.set_page_config(
    page_title="CELTA Tutor Desk",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "data.json"

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None

if "errors" not in st.session_state:
    st.session_state.errors = []

def login_page():
    st.title("📘 CELTA Tutor Desk")
    st.write("Please login to continue")
    st.write("")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if username == data["teacher"]["username"] and hash_password(password) == data["teacher"]["password"]:
            st.session_state.logged_in = True
            st.session_state.role = "teacher"
            st.rerun()

        for sid, student in data["students"].items():
            if student.get("username") == username and student.get("password") == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.role = "student"
                st.session_state.user_id = sid
                st.rerun()

        st.error("Incorrect username or password")

def teacher_dashboard():
    with st.sidebar:
        st.title("Teacher Panel")
        st.caption("Logged in as Teacher")
        menu = st.radio("Menu", ["Students", "Live Lesson", "History", "Create Student Login", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.errors = []
        st.rerun()

    if menu == "Create Student Login":
        st.header("Create Student Login")

        with st.form("create_student"):
            name = st.text_input("Student Full Name")
            level = st.selectbox("CEFR Level", ["A1", "A2", "B1", "B2", "C1", "C2"])
            goals = st.text_area("Learning Goals")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create Student")

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
                    st.success("Student created successfully! Username: " + username)
                else:
                    st.warning("Please fill all fields")

    elif menu == "Students":
        st.header("Students")
        if not data["students"]:
            st.info("No students yet. Create one from 'Create Student Login'.")
        else:
            for sid, student in data["students"].items():
                st.markdown("**" + student["name"] + "** — " + student["level"])
                st.caption("Username: " + student["username"])
                st.write("---")

    elif menu == "Live Lesson":
        st.header("Live Lesson")

        if not data["students"]:
            st.warning("Please create a student first.")
        else:
            student_options = {sid: s["name"] + " (" + s["level"] + ")" for sid, s in data["students"].items()}
            selected_id = st.selectbox("Select Student", list(student_options.keys()), format_func=lambda x: student_options[x])
            student = data["students"][selected_id]

            st.subheader(student["name"] + " (" + student["level"] + ")")
            if student.get("goals"):
                st.caption("Goals: " + student["goals"])

            st.write("---")

            focus = st.selectbox("Today's Focus", ["Grammar", "Vocabulary", "Speaking Fluency", "Listening", "Reading", "Writing", "Pronunciation", "Mixed Skills"])
            topic = st.text_input("Topic / Context")

            st.write("---")
            st.subheader("Live Error Log")

            with st.form("error_form", clear_on_submit=True):
                error_input = st.text_input("Type student error")
                add_error = st.form_submit_button("Add Error")
                if add_error and error_input.strip():
                    st.session_state.errors.append(error_input.strip())

            if st.session_state.errors:
                for i, err in enumerate(st.session_state.errors):
                    col1, col2 = st.columns([6, 1])
                    with col1:
                        st.write(str(i+1) + ". " + err)
                    with col2:
                        if st.button("X", key="del" + str(i)):
                            st.session_state.errors.pop(i)
                            st.rerun()

            st.write("---")
            notes = st.text_area("Session Notes")

            if st.button("Save Lesson", type="primary"):
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

    elif menu == "History":
        st.header("Student History")
        if not data["students"]:
            st.info("No students yet.")
        else:
            student_options = {sid: s["name"] + " (" + s["level"] + ")" for sid, s in data["students"].items()}
            selected_id = st.selectbox("Select Student", list(student_options.keys()), format_func=lambda x: student_options[x])
            student = data["students"][selected_id]

            if not student["sessions"]:
                st.info("No lessons recorded yet.")
            else:
                for session in reversed(student["sessions"]):
                    with st.expander(session["date"] + " | " + session["focus"]):
                        notes_text = session.get("notes", "-")
                        st.write("**Notes:** " + str(notes_text))
                        if session.get("errors"):
                            st.write("**Errors:**")
                            for e in session["errors"]:
                                st.write("- " + e)

def student_dashboard():
    student = data["students"][st.session_state.user_id]

    with st.sidebar:
        st.title("My Progress")
        st.caption("Hello, " + student["name"])
        menu = st.radio("Menu", ["My Lessons", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    st.header("Welcome, " + student["name"])
    st.caption("Level: " + student["level"])
    if student.get("goals"):
        st.info("Your Goals: " + student["goals"])

    st.write("---")
    st.subheader("Your Past Lessons")

    if not student["sessions"]:
        st.info("No lessons recorded yet.")
    else:
        for session in reversed(student["sessions"]):
            with st.expander(session["date"] + " | " + session["focus"]):
                notes_text = session.get("notes", "-")
                st.write("**Teacher Notes:** " + str(notes_text))
                if session.get("errors"):
                    st.write("**Errors:**")
                    for e in session["errors"]:
                        st.write("- " + e)

# ====================== MAIN ======================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.role == "teacher":
        teacher_dashboard()
    elif st.session_state.role == "student":
        student_dashboard()
