"""Private student performance dashboard."""
import pandas as pd
import streamlit as st

from core import ui
from db import queries

st.set_page_config(page_title="Marks · TutorLens", page_icon="📊", layout="wide")
ui.init()
student_id = ui.sidebar_student()
if student_id is None:
    st.stop()

st.markdown("""
<div class="tl-hero">
<div class="tl-eyebrow">TUTORLENS · STUDENT PERFORMANCE</div>
<div class="tl-hero-title">My <span class="tl-hero-accent">Performance</span></div>
<div class="tl-hero-description">Track your quiz results, review feedback and monitor your learning progress.</div>
</div>
""", unsafe_allow_html=True)

summary = queries.get_quiz_summary(student_id)
attempts = queries.get_attempts(student_id)
if not summary:
    st.info("No marks yet. Complete a quiz to see your performance here.")
    if st.button("Take a quiz", type="primary"):
        st.switch_page("pages/3_Quiz.py")
    st.stop()

courses = sorted({row['pdf'] for row in summary})
selected = st.selectbox("Filter by course PDF", [None] + courses,
                        format_func=lambda value: "All courses" if value is None else value)
if selected is not None:
    summary = [row for row in summary if row['pdf'] == selected]
    attempts = [row for row in attempts if row['pdf'] == selected]

def percent(row):
    return 100 * row['points'] / row['max_points'] if row['max_points'] else 0.0

total_points = sum(row['points'] for row in summary)
total_max = sum(row['max_points'] for row in summary)
overall = 100 * total_points / total_max if total_max else 0.0
cols = st.columns(4)
cols[0].metric("Completed quizzes", len(summary))
cols[1].metric("Overall score", f"{overall:.1f}%")
cols[2].metric("Highest quiz score", f"{max(map(percent, summary), default=0):.1f}%")
cols[3].metric("Questions answered", sum(row['questions'] for row in summary))
st.caption("Overall score = total earned points divided by total possible points. Metrics reflect the selected course filter.")

st.subheader("Learning progress")

import altair as alt

progress = pd.DataFrame({
    "Completed quiz": range(1, len(summary) + 1),
    "Score (%)": [
        percent(row) for row in reversed(summary)
    ],
})

chart = (
    alt.Chart(progress)
    .mark_line(
        color="#10746D",
        strokeWidth=3,
        point=alt.OverlayMarkDef(
            filled=True,
            size=100,
            color="#10746D",
        ),
    )
    .encode(
        x=alt.X(
            "Completed quiz:O",
            title="Completed quiz",
        ),
        y=alt.Y(
            "Score (%):Q",
            title="Score (%)",
            scale=alt.Scale(domain=[0, 100]),
            axis=alt.Axis(values=[0, 25, 50, 75, 100]),
        ),
        tooltip=["Completed quiz", "Score (%)"],
    )
    .properties(height=260)
)

st.altair_chart(chart, use_container_width=True)

if len(summary) == 1:
    st.caption(
        "Complete more quizzes to track your learning progress."
    )
else:
    st.caption(
        "Your quiz performance from oldest to newest."
    )

st.subheader("Quiz history")
quiz_table = pd.DataFrame([{
    "Course PDF": row['pdf'], "Quiz": f"Quiz {row['quiz_no']}",
    "Questions": row['questions'], "Score": f"{row['points']} / {row['max_points']}",
    "Percent": round(percent(row), 1),
    "Date": row['date'].strftime('%Y-%m-%d %H:%M') if row['date'] else ''
} for row in summary])
st.dataframe(quiz_table, hide_index=True, use_container_width=True,
             column_config={"Percent": st.column_config.ProgressColumn("Score (%)", min_value=0, max_value=100, format="%.1f%%")})

st.subheader("Answer history and feedback")
review = st.selectbox("Review answers", ["All answers", "Needs improvement", "Full marks"])
visible = [a for a in attempts if review == "All answers" or
           (review == "Needs improvement" and a['points'] < a['max_points']) or
           (review == "Full marks" and a['points'] == a['max_points'])]
if not visible:
    st.info("No answers match this filter.")
for i, a in enumerate(visible, 1):
    with st.expander(f"{i}. {a['pdf']} · Quiz {a['quiz_no']} · {a['points']}/{a['max_points']} points"):
        st.caption(f"{a['type']} · {a['difficulty']}")
        st.write(a['question'])
        st.markdown("**Your answer**")
        st.write(a['answer_text'] or '(no answer)')
        st.markdown("**Feedback**")
        st.write(a['feedback'] or 'No feedback available.')

detail = pd.DataFrame([{
    "PDF": a['pdf'], "Quiz": f"Quiz {a['quiz_no']}", "Type": a['type'],
    "Difficulty": a['difficulty'], "Question": a['question'],
    "Your answer": a['answer_text'], "Points": a['points'],
    "Maximum points": a['max_points'], "Feedback": a['feedback']
} for a in attempts])
# Prevent spreadsheet formula interpretation of exported text fields.
for column in detail.select_dtypes(include='object').columns:
    detail[column] = detail[column].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')) else v)
left, right = st.columns(2)
left.download_button("Download my marks (CSV)", data=detail.to_csv(index=False).encode('utf-8-sig'),
                     file_name="tutorlens_marks.csv", mime="text/csv")
if right.button("Start a new quiz", type="primary"):
    st.session_state.pop('quiz', None)
    st.switch_page("pages/3_Quiz.py")
