"""온실가스관리기사 실기 준비 - Streamlit 진입점.

화면 이동은 st.session_state["screen"] 값으로 결정한다 (URL 라우팅 없음).
각 화면은 ui/screens/ 의 render() 함수 하나로 구현한다.
학습 기록은 core/storage 가 브라우저 localStorage 와 주고받는다.

실행: streamlit 폴더에서 `streamlit run app.py`
"""

import streamlit as st

from core import storage
from core.nav import init_state
from ui.screens import category, countdown, difficulty, home, quiz, result, settings, wrong_notes

st.set_page_config(
    page_title="온실가스관리기사 실기 준비",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

SCREENS = {
    "home": home.render,
    "difficulty": difficulty.render,
    "category": category.render,
    "countdown": countdown.render,
    "quiz": quiz.render,
    "result": result.render,
    "wrong_notes": wrong_notes.render,
    "settings": settings.render,
}


def main() -> None:
    init_state()
    storage.init_store()  # 브라우저 기록을 받을 때까지 여기서 멈춤
    screen = st.session_state["screen"]
    SCREENS.get(screen, home.render)()
    # 화면이 st.rerun() 으로 중간에 끝나면 다음 실행에서 저장됨
    storage.persist()


main()
