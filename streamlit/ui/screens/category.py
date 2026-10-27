import time

import streamlit as st

from core import storage
from core.data import DIFFICULTY_LABEL, build_set, find_question, load_categories, questions_by_category
from core.nav import go


def _start(label: str, questions: list[dict], source: dict) -> None:
    now = time.time()
    st.session_state["session"] = {
        "id": int(now * 1000),
        "label": label,
        "difficulty": st.session_state["difficulty"],
        "items": [{"question": q, "result": None} for q in questions],
        "index": 0,
        "started_at": now,
        "finished_at": None,
        "source": source,
    }
    go("countdown")


def start_category(category_id: str) -> None:
    name = "전체 랜덤" if category_id == "ALL" else next(c["name"] for c in load_categories() if c["id"] == category_id)
    pool = questions_by_category(category_id)
    _start(name, build_set(pool, storage.store()["settings"]["count"]), {"kind": "category", "category": category_id})


def start_wrong_retry() -> None:
    ids = st.session_state["pending_wrong_ids"] or []
    questions = [q for q in (find_question(i) for i in ids) if q]
    _start("오답 다시 풀기", build_set(questions, len(questions)), {"kind": "wrong", "ids": ids})


def restart(source: dict) -> None:
    """결과 화면의 '다시 풀기': 같은 카테고리(또는 같은 오답 목록)로 새 세트."""
    if source["kind"] == "category":
        start_category(source["category"])
    else:
        st.session_state["pending_wrong_ids"] = source["ids"]
        start_wrong_retry()


def summary(category_id: str) -> dict:
    data = storage.store()
    qs = questions_by_category(category_id)
    tries = sum(data["stats"].get(q["id"], {}).get("tries", 0) for q in qs)
    correct = sum(data["stats"].get(q["id"], {}).get("correct", 0) for q in qs)
    notes = data["wrongNotes"]
    wrong = sum(1 for q in qs if q["id"] in notes and not notes[q["id"]]["graduated"])
    return {"count": len(qs), "rate": round(correct / tries * 100) if tries else None, "wrong": wrong}


def render() -> None:
    if st.button("← 뒤로"):
        go("difficulty")
    st.header("카테고리")
    st.caption(f"난이도 {DIFFICULTY_LABEL[st.session_state['difficulty']]} · 고르면 3·2·1 후 시작해요")

    cards = [{"id": "ALL", "name": "전체 랜덤", "icon": "🎲", "desc": "모든 범위"}, *load_categories()]
    cols = st.columns(2)
    for i, c in enumerate(cards):
        s = summary(c["id"])
        extra = (f" · 정답률 {s['rate']}%" if s["rate"] is not None else "") + (f" · 오답 {s['wrong']}" if s["wrong"] else "")
        with cols[i % 2]:
            if st.button(f"{c['icon']} {c['name']}\n\n{s['count']}문항{extra}", key=f"cat_{c['id']}", width="stretch"):
                start_category(c["id"])
