"""Student examination portal with an instructor analytics dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st
import altair as alt

import database


st.set_page_config(page_title="Exam Portal", page_icon="✳", layout="wide")
database.initialize_database()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600&display=swap');
    :root {
        --ink: #19312d;
        --muted: #61736c;
        --green: #176b52;
        --green-dark: #10503f;
        --mint: #e8f1eb;
        --paper: #f4f7f3;
        --line: #d9e3dc;
        --amber: #bd7046;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    .block-container { max-width: 1160px; padding-top: 5rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); }
    h1, h2 { font-family: 'Fraunces', Georgia, serif; letter-spacing: 0; }
    h1 { line-height: 1.12; }
    h2, h3 { line-height: 1.2; }
    .eyebrow { display: block; margin: 0 0 1rem; padding-block: .1em; color: var(--green); font-size: .76rem; font-weight: 700; line-height: 1.5; letter-spacing: .09em; text-transform: uppercase; overflow: visible; }
    .subtle { color: var(--muted); }
    .login-intro { max-width: 35rem; padding: 1.25rem 0 1.5rem; border-top: 4px solid var(--green); }
    .login-intro h1 { max-width: 11ch; margin: 0 0 1.25rem; font-size: 3rem; line-height: 1.08; }
    .login-intro > p:not(.eyebrow) { max-width: 31rem; color: var(--muted); font-size: 1.05rem; line-height: 1.65; }
    .login-note { margin-top: 2rem; padding-left: .9rem; border-left: 2px solid var(--amber); color: var(--muted); font-size: .82rem; font-weight: 700; letter-spacing: .04em; }
    [data-testid="stMetric"] { background: white; border: 1px solid var(--line); padding: 1.1rem 1.2rem; border-radius: 8px; box-shadow: 0 2px 8px rgb(25 49 45 / 4%); }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--ink); font-weight: 700; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line); border-radius: 8px; background: white; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }
    label { color: var(--ink); font-weight: 500; }
    [data-testid="stCaptionContainer"] { color: var(--muted); }
    div[data-testid="stForm"] { border: 0; padding: 0; }
    div.stButton > button[kind="primary"], button[kind="primaryFormSubmit"] { background: var(--green); border-color: var(--green); color: white; font-weight: 600; }
    div.stButton > button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { background: var(--green-dark); border-color: var(--green-dark); color: white; }
    div.stButton > button, button[kind="primaryFormSubmit"] { min-height: 2.75rem; border-radius: 5px; transition: background-color .15s ease, border-color .15s ease; }
    [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, [data-baseweb="select"] > div { background: white; border-color: var(--line); border-radius: 5px; }
    [data-baseweb="input"]:focus-within > div, [data-baseweb="textarea"]:focus-within > div { border-color: var(--green); box-shadow: 0 0 0 1px var(--green); }
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .4rem; border-bottom: 1px solid var(--line); }
    [data-testid="stTabs"] [data-baseweb="tab"] { min-height: 3rem; color: var(--muted); font-weight: 600; }
    [data-testid="stTabs"] [aria-selected="true"] { color: var(--green); }
    section[data-testid="stSidebar"] { background: #eaf1ec; border-right: 1px solid var(--line); }
    section[data-testid="stSidebar"] .eyebrow { padding-top: .5rem; }
    @media (max-width: 760px) {
        .block-container { padding-top: 4.5rem; padding-bottom: 2rem; }
        .login-intro { padding-top: .5rem; }
        .login-intro h1 { font-size: 2.35rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def show_login() -> None:
    intro, access = st.columns([1.1, 0.9], gap="large")
    with intro:
        st.markdown(
            '<section class="login-intro">'
            '<p class="eyebrow">PDS · EXAMINATION PORTAL</p>'
            '<h1>Assessment with clarity.</h1>'
            '<p>One focused workspace for student assessments, results, and course insights.</p>'
            '<div class="login-note">STUDENT &amp; INSTRUCTOR ACCESS</div>'
            '</section>',
            unsafe_allow_html=True,
        )
    with access:
        with st.container(border=True):
            st.markdown('<p class="eyebrow">ACCOUNT ACCESS</p>', unsafe_allow_html=True)
            st.subheader("Sign in")
            st.caption("Use your assigned account credentials.")
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
    st.caption("Choose an assessment to begin, or review your previous results.")
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
        exam_labels = {
            f"{exam['title']}  ·  {exam['subject']}  ·  {exam['question_count']} questions  ·  #{exam['id']}": exam
            for exam in available
        }
        selected_label = st.selectbox("Choose an assessment", list(exam_labels))
        exam = exam_labels[selected_label]
        st.caption(exam["description"])
        questions = database.get_questions(exam["id"])
        with st.form(f"exam_{exam['id']}"):
            answers = {}
            for index, question in enumerate(questions, start=1):
                with st.container(border=True):
                    st.markdown(f"**Question {index:02}**")
                    st.write(question["prompt"])
                    answers[question["id"]] = st.radio(
                        "Select one answer",
                        question["options"],
                        index=None,
                        key=f"answer_{exam['id']}_{question['id']}",
                        label_visibility="collapsed",
                    )
            submitted = st.form_submit_button("Submit assessment", type="primary")
        if submitted:
            unanswered = len(questions) - sum(answer is not None for answer in answers.values())
            if unanswered:
                st.error(f"Answer all questions before submitting. {unanswered} question(s) remain.")
            else:
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
        subject_data = subject_scores.rename_axis("subject").reset_index(name="average_score")
        subject_chart = (
            alt.Chart(subject_data)
            .mark_bar(color="#176b52", cornerRadiusEnd=3)
            .encode(
                x=alt.X("average_score:Q", title="Average score (%)", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("subject:N", sort="-x", title=None),
                tooltip=[
                    alt.Tooltip("subject:N", title="Subject"),
                    alt.Tooltip("average_score:Q", title="Average", format=".1f"),
                ],
            )
            .properties(height=max(150, len(subject_data) * 38))
        )
        st.altair_chart(subject_chart, use_container_width=True)
    with table_col:
        st.subheader("Recent submissions")
        display = frame[["full_name", "exam_title", "score", "total", "percentage", "submitted_at"]].copy()
        display["Score"] = display.apply(lambda row: f"{row['score']} / {row['total']} ({row['percentage']:.0f}%)", axis=1)
        display = display.rename(columns={"full_name": "Student", "exam_title": "Assessment", "submitted_at": "Submitted"})
        st.dataframe(display[["Student", "Assessment", "Score", "Submitted"]], use_container_width=True, hide_index=True)
    st.subheader("Score distribution")
    distribution_chart = (
        alt.Chart(frame)
        .mark_bar(color="#bd7046", cornerRadiusEnd=3)
        .encode(
            x=alt.X("percentage:Q", bin=alt.Bin(step=10), title="Score (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("count():Q", title="Submissions", scale=alt.Scale(domainMin=0), axis=alt.Axis(tickMinStep=1)),
            tooltip=[
                alt.Tooltip("percentage:Q", bin=alt.Bin(step=10), title="Score band"),
                alt.Tooltip("count():Q", title="Submissions"),
            ],
        )
        .properties(height=230)
    )
    st.altair_chart(distribution_chart, use_container_width=True)


def show_exam_management() -> None:
    st.markdown('<p class="eyebrow">ASSESSMENT BUILDER</p>', unsafe_allow_html=True)
    st.title("Manage assessments")
    st.caption("Create an assessment, then add questions before students can take it.")
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
            exam_labels = {f"{exam['title']} · {exam['subject']} · #{exam['id']}": exam for exam in exams}
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
                    try:
                        database.add_question(exam["id"], prompt, clean_options, clean_options[selected_index])
                        st.success("Question added.")
                    except ValueError as exc:
                        st.error(str(exc))
            current_questions = database.get_questions(exam["id"])
            if current_questions:
                st.caption(f"{len(current_questions)} question(s) in this assessment")
                for index, question in enumerate(current_questions, start=1):
                    st.write(f"{index}. {question['prompt']}")


def show_student_management() -> None:
    st.markdown('<p class="eyebrow">STUDENT DIRECTORY</p>', unsafe_allow_html=True)
    st.title("Manage students")
    st.caption("Add learner accounts or update existing student details.")

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

    confirm_delete = st.checkbox("I understand this permanently deletes the student and their submissions.")
    if st.button("Delete student", type="secondary", disabled=not confirm_delete):
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