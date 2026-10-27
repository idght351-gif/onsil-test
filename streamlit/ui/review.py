"""모범답안 + 해설 + 암기 꿀팁 (해설 화면·결과·오답노트 공용)."""

from typing import Any

import streamlit as st

from core import storage
from core.grading import format_number
from core.quiz import fill_template
from ui.text import md_escape, md_lines


def render_review(q: dict[str, Any], key: str) -> None:
    st.markdown("**✅ 모범답안**")
    if q["type"] == "text":
        answer = fill_template(md_escape(q["template"]), lambda i: f"**{md_escape(q['blanks'][i]['answer'])}**")
        st.markdown(md_lines(answer))
    else:
        lines = [
            f"{i + 1}. {md_escape(s['label'])}  \n"
            f"{md_escape(s['expr'])} = **{format_number(s['value'], s.get('digits', 0))}** {md_escape(s['unit'])}"
            for i, s in enumerate(q["steps"])
        ]
        st.markdown("\n".join(lines))

    st.markdown("**📖 해설**")
    st.markdown(md_escape(q["explanation"]))

    fav = q["id"] in storage.store()["favTips"]
    tip_col, fav_col = st.columns([6, 1], vertical_alignment="center")
    tip_col.info(f"💡 **암기 꿀팁**  \n{md_escape(q['tip'])}")
    if fav_col.button("⭐" if fav else "☆", key=f"{key}_fav", help="꿀팁 즐겨찾기"):
        storage.toggle_fav_tip(q["id"])
        st.rerun()
