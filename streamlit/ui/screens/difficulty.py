import streamlit as st

from core.nav import go

OPTIONS = [
    ("easy", "하", "보기 중에서 빈칸에 맞는 답을 골라요"),
    ("normal", "중", "빈칸에 들어갈 답을 직접 입력해요"),
    ("hard", "상", "실전처럼 답안 전체를 작성해요 · 계산은 사진 풀이도 OK"),
]


def render() -> None:
    if st.button("← 뒤로"):
        go("wrong_notes" if st.session_state["pending_wrong_ids"] else "home")
    st.header("난이도 선택")

    for key, label, desc in OPTIONS:
        if st.button(f"{label} — {desc}", key=f"diff_{key}", width="stretch"):
            st.session_state["difficulty"] = key
            # 오답 다시 풀기는 카테고리 선택 없이 바로 시작
            if st.session_state["pending_wrong_ids"]:
                from ui.screens.category import start_wrong_retry

                start_wrong_retry()
            go("category")
