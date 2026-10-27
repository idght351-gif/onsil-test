"""문제 풀이 화면.

한 문제는 phase 순서로 진행: answer → (selfcheck: 상·계산·사진) → feedback → explain
기록 저장은 explain 으로 넘어갈 때 한다 (상 난이도 자가 채점 결과까지 반영하려고).
"""

import time
from typing import Any

import streamlit as st

from core import storage
from core.data import DIFFICULTY_LABEL, exam_label, load_categories
from core.grading import format_number, grade_blanks, grade_calc, grade_keywords, grade_steps_from_text, last_number
from core.nav import go
from core.quiz import CIRCLED, as_blank_question, choices_for, fill_template
from ui.review import render_review
from ui.text import md_escape, md_lines

VERDICT_LABEL = {"correct": "⭕ 정답!", "partial": "🔺 부분 정답", "wrong": "❌ 아쉬워요"}
MODE_TYPE, MODE_PHOTO = "✍️ 풀이 입력", "📷 종이 풀이 사진"


def render() -> None:
    session = st.session_state["session"]
    if not session:
        go("home")
    items, index = session["items"], session["index"]
    item = items[index]
    q = item["question"]
    difficulty = session["difficulty"]
    key = f"s{session['id']}_q{index}"  # 문제마다 입력칸 상태가 새로 시작되도록

    _header(session, q)

    phase = item.get("phase", "answer")
    if phase == "explain":
        _explain(session, item, key)
    elif phase == "selfcheck":
        _selfcheck(item, key)
    elif phase == "feedback":
        _feedback(item, difficulty, key)
    else:
        _answer(item, difficulty, key)


def _header(session: dict[str, Any], q: dict[str, Any]) -> None:
    category = next((c for c in load_categories() if c["id"] == q["category"]), None)
    top_left, top_right = st.columns([1, 4], vertical_alignment="center")
    if top_left.button("✕", help="그만두기 (지금까지 기록은 저장돼요)"):
        go("home")
    total = len(session["items"])
    top_right.markdown(
        f"**{category['icon'] if category else ''} {session['label']}** · 난이도 {DIFFICULTY_LABEL[session['difficulty']]} · {session['index'] + 1}/{total}"
    )
    st.progress(session["index"] / total)

    tags = f"`{exam_label(q)} 기출`" + (" `🧮 계산`" if q["type"] == "calc" else "")
    with st.container(border=True):
        st.markdown(tags)
        st.markdown(f"**{md_lines(md_escape(q['question']))}**")


def _blank_q(item: dict[str, Any]) -> dict[str, Any]:
    """빈칸 문제와 보기는 한 번만 만들어 저장 (다시 그릴 때 보기 순서가 바뀌지 않게)."""
    if "bq" not in item:
        item["bq"] = as_blank_question(item["question"])
        item["choices"] = [choices_for(b) for b in item["bq"]["blanks"]]
    return item["bq"]


def _answer(item: dict[str, Any], difficulty: str, key: str) -> None:
    q = item["question"]

    if difficulty != "hard":
        bq = _blank_q(item)
        st.markdown(md_lines(fill_template(md_escape(bq["template"]), lambda i: f"**( {CIRCLED[i]} )**")))
        with st.form(f"{key}_form"):
            for i, choices in enumerate(item["choices"]):
                label = f"빈칸 {CIRCLED[i]}"
                if difficulty == "easy":
                    st.pills(label, choices, key=f"{key}_b{i}")
                else:
                    st.text_input(label, key=f"{key}_b{i}")
            submitted = st.form_submit_button("제출!", type="primary", width="stretch")
        if submitted:
            values = [str(st.session_state.get(f"{key}_b{i}") or "") for i in range(len(bq["blanks"]))]
            if difficulty == "easy" and not all(values):
                st.warning("모든 빈칸의 보기를 골라주세요.")
            elif not any(v.strip() for v in values):
                st.warning("빈칸을 하나 이상 채워주세요.")
            else:
                _show_feedback(item, grade_blanks(bq["blanks"], values, bq["unordered"]))
        return

    if q["type"] == "text":
        with st.form(f"{key}_form"):
            st.text_area("답안", key=f"{key}_text", height=200, placeholder="실제 시험처럼 답안을 작성하세요")
            submitted = st.form_submit_button("제출!", type="primary", width="stretch")
        if submitted:
            text = st.session_state.get(f"{key}_text", "")
            if not text.strip():
                st.warning("답안을 작성해주세요.")
            else:
                _show_feedback(item, grade_keywords(q["keywords"], text))
        return

    # 난이도 상 · 계산 문제
    mode = st.segmented_control("풀이 방식", [MODE_TYPE, MODE_PHOTO], default=MODE_TYPE, key=f"{key}_mode") or MODE_TYPE
    unit = q["steps"][-1]["unit"]
    with st.form(f"{key}_form"):
        if mode == MODE_TYPE:
            st.text_area(
                "풀이과정",
                key=f"{key}_work",
                height=180,
                placeholder="풀이과정을 단계별로 적어주세요\n예) 열량 = 2,500 × 35.3 ÷ 10^6 = 0.08825 TJ",
            )
        else:
            st.camera_input("카메라로 찍기", key=f"{key}_camera")
            st.file_uploader("또는 갤러리에서 선택", type=["jpg", "jpeg", "png", "heic", "webp"], key=f"{key}_upload")
            st.caption("사진은 이 기기의 브라우저에만 저장돼요.")
        st.text_input(f"최종값 ({unit})", key=f"{key}_final", placeholder="숫자만 입력")
        submitted = st.form_submit_button("제출!", type="primary", width="stretch")
    if not submitted:
        return

    final = st.session_state.get(f"{key}_final", "").strip()
    if mode == MODE_TYPE:
        work = st.session_state.get(f"{key}_work", "")
        if not (work.strip() or final):
            st.warning("풀이나 최종값을 입력해주세요.")
            return
        steps = grade_steps_from_text(q["steps"], f"{work}\n{final}")
        result = grade_calc(q["steps"], final or last_number(work), steps)
        result["user_answer"] = (work.strip() + "\n" if work.strip() else "") + result["user_answer"]
        _show_feedback(item, result)
        return

    photo_file = st.session_state.get(f"{key}_camera") or st.session_state.get(f"{key}_upload")
    if not photo_file or not final:
        st.warning("풀이 사진과 최종값을 모두 넣어주세요.")
        return
    try:
        item["photo"] = storage.compress_image(photo_file.getvalue())
    except Exception:
        st.error("사진을 읽을 수 없어요. 다른 사진으로 시도해주세요.")
        return
    item["final_input"] = final
    item["phase"] = "selfcheck"
    st.rerun()


def _selfcheck(item: dict[str, Any], key: str) -> None:
    q = item["question"]
    st.markdown("#### 📝 풀이과정 셀프 체크")
    st.caption("사진 속 내 풀이에 아래 단계가 있는지 체크하세요. 최종값은 자동 채점돼요.")
    st.image(storage.data_url_bytes(item["photo"]), width="stretch")
    checks = []
    for i, s in enumerate(q["steps"]):
        label = f"{i + 1}. {s['label']} — {s['expr']} = {format_number(s['value'], s.get('digits', 0))} {s['unit']}"
        checks.append(st.checkbox(label, key=f"{key}_check{i}"))
    if st.button("채점하기", type="primary", width="stretch"):
        _show_feedback(item, grade_calc(q["steps"], item["final_input"], checks, photo=item["photo"], self_graded=True))


def _show_feedback(item: dict[str, Any], result: dict[str, Any]) -> None:
    item["result"] = result
    item["phase"] = "feedback"
    st.rerun()


def _feedback(item: dict[str, Any], difficulty: str, key: str) -> None:
    q, result = item["question"], item["result"]
    {"correct": st.success, "partial": st.warning, "wrong": st.error}[result["verdict"]](f"### {VERDICT_LABEL[result['verdict']]}")

    if result.get("blank_results") is not None:
        answers = [b["answer"] for b in item["bq"]["blanks"]]
        given = result["user_answer"].split(" / ")
        for i, ok in enumerate(result["blank_results"]):
            mine = "" if ok else f" · 내 답: {md_escape(given[i] if i < len(given) else '')}"
            st.markdown(f"{'✅' if ok else '❌'} {CIRCLED[i]} 정답: **{md_escape(answers[i])}**{mine}")
    elif result.get("keyword_hits") is not None:
        hits = result["keyword_hits"]
        st.markdown(f"필수 키워드 {sum(h['hit'] for h in hits)}/{len(hits)}개 포함")
        st.markdown(" ".join(f":green-background[{md_escape(h['keyword'])}]" if h["hit"] else f":red-background[~~{md_escape(h['keyword'])}~~]" for h in hits))
    elif result.get("step_results") is not None:
        final = q["steps"][-1]
        st.markdown(f"{'✅' if result['final_ok'] else '❌'} 최종값 정답: **{format_number(final['value'], final.get('digits', 0))} {md_escape(final['unit'])}**")
        steps_ok = result["step_results"]
        st.caption(f"풀이과정 {sum(steps_ok)}/{len(steps_ok)}단계 확인" + (" (셀프 체크)" if result.get("self_graded") else ""))
        for i, s in enumerate(q["steps"]):
            st.markdown(f"{'✅' if steps_ok[i] else '❌'} {md_escape(s['label'])}: {format_number(s['value'], s.get('digits', 0))} {md_escape(s['unit'])}")
        if result["verdict"] == "partial":
            st.caption(
                "최종값은 맞았지만 풀이과정이 부족해요. 실기는 과정 점수가 있어요!"
                if result["final_ok"]
                else "풀이과정은 좋은데 최종값이 달라요. 단위·반올림을 확인하세요."
            )

    if difficulty == "hard":
        st.caption("모범답안과 비교해 직접 채점할 수도 있어요")
        left, right = st.columns(2)
        if left.button("맞았어요 ⭕", key=f"{key}_self_ok", width="stretch"):
            result.update(verdict="correct", self_graded=True)
            st.rerun()
        if right.button("틀렸어요 ❌", key=f"{key}_self_ng", width="stretch"):
            result.update(verdict="wrong", self_graded=True)
            st.rerun()

    if st.button("해설 보기 📖", type="primary", width="stretch", key=f"{key}_to_explain"):
        storage.record_result(q["id"], result)
        item["phase"] = "explain"
        st.rerun()


def _explain(session: dict[str, Any], item: dict[str, Any], key: str) -> None:
    q, result = item["question"], item["result"]
    {"correct": st.success, "partial": st.warning, "wrong": st.error}[result["verdict"]](VERDICT_LABEL[result["verdict"]])
    if result.get("photo"):
        with st.expander("📷 내 풀이 사진 보기"):
            st.image(storage.data_url_bytes(result["photo"]), width="stretch")

    render_review(q, key)

    if result["verdict"] == "correct":
        saved = item.get("saved", False)
        if st.button("오답노트에 저장됨 ✓" if saved else "📒 헷갈렸어요 · 오답노트에 저장", disabled=saved, width="stretch", key=f"{key}_save"):
            storage.add_to_wrong_notes(q["id"], result["user_answer"])
            item["saved"] = True
            st.rerun()

    is_last = session["index"] + 1 >= len(session["items"])
    if st.button("결과 보기 🏁" if is_last else "다음 문제 →", type="primary", width="stretch", key=f"{key}_next"):
        if is_last:
            session["finished_at"] = time.time()
            go("result")
        session["index"] += 1
        st.rerun()
