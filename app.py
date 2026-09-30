"""Student examination portal with an instructor analytics dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import database


st.set_page_config(page_title="Exam Portal", page_icon="✳", layout="wide")
database.initialize_database()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');
    :root { --ink: #172c27; --muted: #65766f; --green: #176b52; --mint: #e6f1e9; --line: #dce5de; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: #f7f8f3; }
    .block-container { max-width: 1180px; padding-top: 5rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); }
    h1, h2 { font-family: 'Fraunces', Georgia, serif; letter-spacing: 0; }
    [data-testid="stMetric"] { background: white; border: 1px solid var(--line); padding: 1rem 1.15rem; border-radius: 6px; }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    .eyebrow { display: block; margin: 0 0 1rem; padding-block: .1em; color: var(--green); font-size: .76rem; font-weight: 700; line-height: 1.5; letter-spacing: .09em; text-transform: uppercase; overflow: visible; }
    .subtle { color: var(--muted); }
    div.stButton > button[kind="primary"] { background: var(--green); border-color: var(--green); }
    div.stButton > button { border-radius: 4px; }
    div[data-testid="stForm"] { border-color: var(--line); border-radius: 6px; }
    section[data-testid="stSidebar"] { background: #edf3ed; border-right: 1px solid var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_login() -> None:
    left, center, right = st.columns([1, 1.1, 1])
    with center:
        st.markdown('<p class="eyebrow">PDS · EXAMINATION PORTAL</p>', unsafe_allow_html=True)
        st.title("A quieter way to test what you know.")
        st.markdown('<p class="subtle">Sign in to take an assessment or review class performance.</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. alice")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            user = database.authenticate(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            st.error("That username and password don't match.")
        with st.expander("Demo sign-in details"):
            st.write("Student: `alice` / `alice123` or `sam` / `sam123`")
            st.write("Instructor: `admin` / `admin123`")


def show_student_home(user: dict) -> None:
    st.markdown('<p class="eyebrow">STUDENT WORKSPACE</p>', unsafe_allow_html=True)
    st.title(f"Good to see you, {user['full_name'].split()[0]}.")
    exams = database.list_exams()
    attempts = database.get_attempts(user["id"])
    average = round(sum(item["score"] / item["total"] * 100 for item in attempts) / len(attempts)) if attempts else 0
    metric_columns = st.columns(3)
    metric_columns[0].metric("Available assessments", len([exam for exam in exams if exam["question_count"]]))
    metric_columns[1].metric("Completed attempts", len(attempts))
    metric_columns[2].metric("Average score", f"{average}%" if attempts else "—")
    st.divider()
    take_tab, results_tab = st.tabs(["Take an exam", "My results"])
    with take_tab:
        available = [exam for exam in exams if exam["question_count"]]
        if not available:
            st.info("There are no assessments available yet.")
            return
        exam_labels = {f"{exam['title']}  ·  {exam['subject']}  ·  {exam['question_count']} questions": exam for exam in available}
        selected_label = st.selectbox("Choose an assessment", list(exam_labels))
        exam = exam_labels[selected_label]
        st.caption(exam["description"])
        questions = database.get_questions(exam["id"])
        with st.form(f"exam_{exam['id']}"):
            answers = {}
            for index, question in enumerate(questions, start=1):
                st.markdown(f"**{index:02}. {question['prompt']}**")
                answers[question["id"]] = st.radio(
                    "Select one answer",
                    question["options"],
                    index=None,
                    key=f"answer_{exam['id']}_{question['id']}",
                    label_visibility="collapsed",
                )
            submitted = st.form_submit_button("Submit assessment", type="primary")
        if submitted:
            result = database.submit_attempt(user["id"], exam["id"], answers)
            percentage = round(result["score"] / result["total"] * 100)
            st.session_state.last_result = {"exam": exam["title"], **result, "percentage": percentage}
            st.rerun()
        last_result = st.session_state.get("last_result")
        if last_result:
            st.success(f"{last_result['exam']} submitted · {last_result['score']} of {last_result['total']} correct ({last_result['percentage']}%).")
    with results_tab:
        if attempts:
            frame = pd.DataFrame(attempts)
            frame["Result"] = frame.apply(lambda row: f"{row['score']} / {row['total']} ({round(row['score'] / row['total'] * 100)}%)", axis=1)
            st.dataframe(frame[["exam_title", "subject", "Result", "submitted_at"]].rename(columns={"exam_title": "Assessment", "subject": "Subject", "submitted_at": "Submitted"}), use_container_width=True, hide_index=True)
        else:
            st.info("Your submitted assessments will appear here.")


def show_admin_overview() -> None:
    st.markdown('<p class="eyebrow">COURSE INSIGHTS</p>', unsafe_allow_html=True)
    st.title("Class performance")
    attempts = database.get_attempts()
    exams = database.list_exams()
    col1, col2, col3 = st.columns(3)
    col1.metric("Assessments", len(exams))
    col2.metric("Questions", sum(exam["question_count"] for exam in exams))
    col3.metric("Submissions", len(attempts))
    if not attempts:
        st.info("Performance charts will appear after students submit an assessment.")
        return
    frame = pd.DataFrame(attempts)
    frame["percentage"] = frame["score"] / frame["total"] * 100
    chart_col, table_col = st.columns([1, 1.35])
    with chart_col:
        st.subheader("Average score by subject")
        subject_scores = frame.groupby("subject")["percentage"].mean().round(1).sort_values(ascending=False)
        st.bar_chart(subject_scores, horizontal=True, color="#176b52", x_label="Average score (%)")
    with table_col:
        st.subheader("Recent submissions")
        display = frame[["full_name", "exam_title", "score", "total", "percentage", "submitted_at"]].copy()
        display["Score"] = display.apply(lambda row: f"{row['score']} / {row['total']} ({row['percentage']:.0f}%)", axis=1)
        display = display.rename(columns={"full_name": "Student", "exam_title": "Assessment", "submitted_at": "Submitted"})
        st.dataframe(display[["Student", "Assessment", "Score", "Submitted"]], use_container_width=True, hide_index=True)
    st.subheader("Score distribution")
    st.bar_chart(frame["percentage"].round(0).value_counts().sort_index(), color="#b7773d", x_label="Score (%)", y_label="Submissions")


def show_exam_management() -> None:
    st.markdown('<p class="eyebrow">ASSESSMENT BUILDER</p>', unsafe_allow_html=True)
    st.title("Manage assessments")
    create_tab, questions_tab = st.tabs(["Create assessment", "Add questions"])
    with create_tab:
        with st.form("create_exam"):
            title = st.text_input("Assessment title")
            subject = st.text_input("Subject")
            description = st.text_area("Short description", height=90)
            submitted = st.form_submit_button("Create assessment", type="primary")
        if submitted:
            if not title.strip() or not subject.strip():
                st.error("Enter both a title and a subject.")
            else:
                database.add_exam(title, subject, description)
                st.success(f"'{title.strip()}' created. Add at least one question before students can take it.")
    with questions_tab:
        exams = database.list_exams()
        if not exams:
            st.info("Create an assessment first.")
        else:
            exam_labels = {f"{exam['title']} · {exam['subject']}": exam for exam in exams}
            selected = st.selectbox("Assessment", list(exam_labels), key="question_exam")
            exam = exam_labels[selected]
            with st.form("add_question"):
                prompt = st.text_area("Question")
                option_columns = st.columns(2)
                options = [option_columns[index % 2].text_input(f"Option {index + 1}", key=f"option_{index}") for index in range(4)]
                correct_answer = st.selectbox("Correct answer", ["Choose an option", *[f"Option {index + 1}" for index in range(4)]])
                submitted = st.form_submit_button("Add question", type="primary")
            if submitted:
                selected_index = ["Option 1", "Option 2", "Option 3", "Option 4"].index(correct_answer) if correct_answer != "Choose an option" else -1
                clean_options = [option.strip() for option in options]
                if not prompt.strip() or selected_index < 0 or not all(clean_options):
                    st.error("Complete the question, all four options, and choose the correct answer.")
                else:
                    database.add_question(exam["id"], prompt, clean_options, clean_options[selected_index])
                    st.success("Question added.")
            current_questions = database.get_questions(exam["id"])
            if current_questions:
                st.caption(f"{len(current_questions)} question(s) in this assessment")
                for index, question in enumerate(current_questions, start=1):
                    st.write(f"{index}. {question['prompt']}")


def show_student_management() -> None:
    st.markdown('<p class="eyebrow">STUDENT DIRECTORY</p>', unsafe_allow_html=True)
    st.title("Manage students")

    with st.form("add_student"):
        username = st.text_input("Username")
        full_name = st.text_input("Full name")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Add student", type="primary")

    if submitted:
        try:
            database.add_student(username, full_name, password)
            st.success(f"Student '{full_name.strip()}' created.")
        except ValueError as exc:
            st.error(str(exc))

    students = database.list_students()
    if not students:
        st.info("No students have been added yet.")
        return

    student_names = {f"{student['full_name']} ({student['username']})": student for student in students}
    selected_label = st.selectbox("Edit student", list(student_names), key="student_edit_select")
    selected_student = student_names[selected_label]

    with st.form("update_student"):
        updated_username = st.text_input("Username", value=selected_student["username"])
        updated_full_name = st.text_input("Full name", value=selected_student["full_name"])
        updated_password = st.text_input("New password", type="password", placeholder="Leave blank to keep existing password")
        save = st.form_submit_button("Save changes", type="primary")

    if save:
        try:
            database.update_student(
                selected_student["id"],
                username=updated_username,
                full_name=updated_full_name,
                password=updated_password if updated_password.strip() else None,
            )
            st.success("Student details updated.")
        except ValueError as exc:
            st.error(str(exc))

    if st.button("Delete student", type="secondary"):
        try:
            database.delete_student(selected_student["id"])
            st.success(f"Student '{selected_student['full_name']}' deleted.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("Student list")
    st.dataframe(pd.DataFrame(students)[["username", "full_name"]].rename(columns={"username": "Username", "full_name": "Full name"}), use_container_width=True, hide_index=True)


def main() -> None:
    if "user" not in st.session_state:
        show_login()
        return
    user = st.session_state.user
    with st.sidebar:
        st.markdown('<p class="eyebrow">PDS · EXAM PORTAL</p>', unsafe_allow_html=True)
        st.write(f"Signed in as **{user['full_name']}**")
        st.caption("Instructor" if user["role"] == "admin" else "Student")
        st.divider()
        if st.button("Sign out", use_container_width=True):
            for key in ("user", "last_result"):
                st.session_state.pop(key, None)
            st.rerun()
    if user["role"] == "admin":
        overview_tab, assess_tab, student_tab = st.tabs(["Overview", "Manage assessments", "Manage students"])
        with overview_tab:
            show_admin_overview()
        with assess_tab:
            show_exam_management()
        with student_tab:
            show_student_management()
    else:
        show_student_home(user)


if __name__ == "__main__":
    main()