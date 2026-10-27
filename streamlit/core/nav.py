"""화면 이동과 세션 상태 기본값."""

from typing import Any

import streamlit as st

DEFAULTS: dict[str, Any] = {
    "screen": "home",
    "difficulty": "easy",
    # 진행 중인 세트: {"id", "label", "difficulty", "items", "index", "started_at", "finished_at", "source"}
    # items: [{"question", "result", "phase", "bq", "choices", "photo", "final_input", "saved"}]
    "session": None,
    "pending_wrong_ids": None,  # 오답 다시 풀기 대상 문제 ID 목록
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(screen: str, **state: Any) -> None:
    """상태를 바꾸고 다른 화면으로 이동."""
    for key, value in state.items():
        st.session_state[key] = value
    st.session_state["screen"] = screen
    st.rerun()
