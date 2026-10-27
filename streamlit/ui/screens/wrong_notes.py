import streamlit as st

from core import storage
from core.data import exam_label, find_question, load_categories
from core.nav import go
from ui.review import render_review
from ui.text import md_escape, md_lines

TAB_ACTIVE, TAB_DONE, TAB_TIPS = "복습 중", "🎓 졸업", "⭐ 꿀팁"
SORT_RECENT, SORT_COUNT = "최근 틀린 순", "많이 틀린 순"


def render() -> None:
    if st.button("← 뒤로"):
        go("home")
    st.header("오답노트")

    tab = st.segmented_control("보기", [TAB_ACTIVE, TAB_DONE, TAB_TIPS], default=TAB_ACTIVE, key="wn_tab", label_visibility="collapsed") or TAB_ACTIVE
    data = storage.store()

    if tab == TAB_TIPS:
        favs = [q for q in (find_question(i) for i in data["favTips"]) if q]
        if not favs:
            st.caption("해설 화면에서 ☆를 눌러 꿀팁을 모아보세요")
        for q in favs:
            st.info(f"{exam_label(q)} · {md_escape(q['question'].splitlines()[0])}  \n💡 **{md_escape(q['tip'])}**")
        return

    categories = load_categories()
    cat_names = {c["id"]: f"{c['icon']} {c['name']}" for c in categories}
    left, right = st.columns([3, 2])
    cat = left.selectbox("카테고리", ["ALL", *cat_names], format_func=lambda c: "전체 카테고리" if c == "ALL" else cat_names[c], key="wn_cat")
    sort = right.selectbox("정렬", [SORT_RECENT, SORT_COUNT], key="wn_sort")

    notes = [(n, find_question(n["questionId"])) for n in data["wrongNotes"].values()]
    notes = [(n, q) for n, q in notes if q and (cat == "ALL" or q["category"] == cat)]
    active_ids = [q["id"] for n, q in notes if not n["graduated"]]
    shown = [(n, q) for n, q in notes if n["graduated"] == (tab == TAB_DONE)]
    if sort == SORT_COUNT:
        shown.sort(key=lambda x: x[0]["wrongCount"], reverse=True)
    else:
        shown.sort(key=lambda x: x[0]["lastWrongAt"], reverse=True)

    if tab == TAB_ACTIVE:
        if active_ids and st.button(f"🔁 오답만 다시 풀기 ({len(active_ids)})", type="primary", width="stretch"):
            go("difficulty", pending_wrong_ids=active_ids)
        st.caption(f"연속 {storage.GRADUATE_STREAK}번 맞히면 자동으로 졸업해요")

    if not shown:
        st.caption("복습할 오답이 없어요 🎉" if tab == TAB_ACTIVE else "아직 졸업한 문제가 없어요")

    for note, q in shown:
        streak = f" · 연속 정답 {note['consecutiveCorrect']}" if note["consecutiveCorrect"] and not note["graduated"] else ""
        photo = " 📷" if note.get("photo") else ""
        with st.expander(f"✕{note['wrongCount']} · {md_escape(q['question'].splitlines()[0])}{photo}"):
            st.caption(f"{exam_label(q)} · {cat_names.get(q['category'], '')}{streak}")
            st.markdown(f"**{md_lines(md_escape(q['question']))}**")
            st.markdown(f":red[마지막 내 답:] {md_lines(md_escape(note['lastUserAnswer']))}")
            if note.get("photo"):
                st.image(storage.data_url_bytes(note["photo"]), width="stretch")
            render_review(q, key=f"wn_{q['id']}")

            left, right = st.columns(2)
            if left.button("↩️ 복습으로" if note["graduated"] else "🎓 졸업 처리", key=f"wn_grad_{q['id']}", width="stretch"):
                storage.set_graduated(q["id"], not note["graduated"])
                st.rerun()
            with right.popover("🗑️ 삭제", width="stretch"):
                st.caption("오답노트에서 삭제할까요?")
                if st.button("삭제", key=f"wn_del_{q['id']}", type="primary"):
                    storage.remove_wrong_note(q["id"])
                    st.rerun()
