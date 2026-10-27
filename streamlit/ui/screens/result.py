import time

import streamlit as st

from core.data import DIFFICULTY_LABEL, exam_label
from core.nav import go
from ui.review import render_review
from ui.screens.category import restart
from ui.text import md_escape, md_lines

ICON = {"correct": "⭕", "partial": "🔺", "wrong": "❌"}


def render() -> None:
    session = st.session_state["session"]
    if not session:
        go("home")
    items = session["items"]
    total = len(items)
    correct = sum(1 for it in items if (it["result"] or {}).get("verdict") == "correct")
    pct = round(correct / total * 100)
    secs = round((session.get("finished_at") or time.time()) - session["started_at"])
    message = "합격권! 🏆" if pct >= 90 else "조금만 더! 💪" if pct >= 60 else "복습 가자! 📒"

    st.caption(f"{session['label']} · 난이도 {DIFFICULTY_LABEL[session['difficulty']]}")
    st.header(f"{correct} / {total}")
    st.subheader(message)
    st.caption(f"{pct}% · 소요 시간 {secs // 60}분 {secs % 60}초")

    for i, it in enumerate(items):
        q, result = it["question"], it["result"] or {"verdict": "wrong", "user_answer": "(풀지 않음)"}
        first_line = q["question"].splitlines()[0]
        with st.expander(f"{ICON[result['verdict']]} {i + 1:02d} · {exam_label(q)} · {md_escape(first_line)}"):
            st.markdown(f"**내 답:** {md_lines(md_escape(result['user_answer']))}")
            render_review(q, key=f"res{session['id']}_{i}")

    if st.button("📒 오답노트 보기", type="primary", width="stretch"):
        go("wrong_notes")
    if st.button("🔁 다시 풀기", width="stretch"):
        restart(session["source"])
    if st.button("홈으로", width="stretch"):
        go("home")
