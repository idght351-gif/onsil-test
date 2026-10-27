import time

import streamlit as st

from core.nav import go

SEQUENCE = ["3", "2", "1", "START!"]


def render() -> None:
    slot = st.empty()
    for i, text in enumerate(SEQUENCE):
        slot.markdown(f"<h1 style='text-align:center;font-size:8rem'>{text}</h1>", unsafe_allow_html=True)
        time.sleep(0.6 if i == len(SEQUENCE) - 1 else 1)
    go("quiz")
