from datetime import datetime, timezone

import streamlit as st

from core import storage
from core.data import load_questions
from core.nav import go


def render() -> None:
    data = storage.store()
    stats = list(data["stats"].values())
    tries = sum(s["tries"] for s in stats)
    correct = sum(s["correct"] for s in stats)
    today = datetime.now(timezone.utc).astimezone().date()
    today_count = sum(1 for s in stats if datetime.fromisoformat(s["last"]).astimezone().date() == today)
    wrong_count = sum(1 for n in data["wrongNotes"].values() if not n["graduated"])
    total = len(load_questions())

    st.title("온실가스관리기사 실기 준비")
    st.caption(f"기출 2020~2023 · {total}문항")

    cols = st.columns(4)
    cols[0].metric("정답률", f"{round(correct / tries * 100)}%" if tries else "-")
    cols[1].metric("오늘", today_count)
    cols[2].metric("풀어봄", f"{len(stats)}/{total}")
    cols[3].metric("복습할 오답", wrong_count)

    if st.button("학습 시작!", type="primary", width="stretch"):
        go("difficulty", pending_wrong_ids=None)
    if st.button(f"📒 오답노트{f' ({wrong_count})' if wrong_count else ''}", width="stretch"):
        go("wrong_notes")
    if st.button("⚙️ 설정", width="stretch"):
        go("settings")

    st.caption("모범답안·해설은 자체 작성본입니다. 최신 지침과 함께 확인하세요.")
