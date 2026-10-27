"""학습 기록 저장 (브라우저 localStorage) + 오답노트 규칙. app/src/lib/storage.ts 와 같은 규칙.

동작 방식
- 첫 실행: localStorage 컴포넌트에서 전체 값을 받아올 때까지 화면을 멈추고 기다린다.
  (라이브러리 기본 LocalStorage 클래스는 응답 전에 {} 를 돌려줘서, 그 상태로 저장하면 기존 기록이 지워짐)
- 이후: 기록은 st.session_state["store"] 에서 읽고 고친다.
- 매 실행 끝(app.py)에서 persist() 가 store 전체를 JSON 한 덩어리로 localStorage 에 쓴다.
"""

import base64
import io
import json
from datetime import datetime, timezone
from typing import Any

import streamlit as st
from PIL import Image, ImageOps
from streamlit_local_storage import _st_local_storage

STORAGE_KEY = "ghg_store_v1"
_GET_KEY = "ghg_ls_get"
_SET_KEY = "ghg_ls_set"

# 오답노트 졸업 조건: 연속 정답 횟수
GRADUATE_STREAK = 2
# localStorage 한도(보통 5MB)를 넘지 않도록 사진 포함 전체 크기 제한.
# 매 실행마다 브라우저로 전체를 보내므로 넉넉하게 낮춰 둠
MAX_STORE_CHARS = 2_500_000

DEFAULT_SETTINGS = {"count": 10}


def empty_store() -> dict[str, Any]:
    return {"wrongNotes": {}, "stats": {}, "favTips": [], "settings": dict(DEFAULT_SETTINGS)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize(data: Any) -> dict[str, Any]:
    """불러온 값이 깨져 있어도 앱이 멈추지 않게 기본 구조로 맞춤."""
    store = empty_store()
    if isinstance(data, dict):
        for key in ("wrongNotes", "stats"):
            if isinstance(data.get(key), dict):
                store[key] = data[key]
        if isinstance(data.get("favTips"), list):
            store["favTips"] = [x for x in data["favTips"] if isinstance(x, str)]
        if isinstance(data.get("settings"), dict):
            store["settings"].update(data["settings"])
    return store


def init_store() -> None:
    """브라우저 기록을 한 번 불러와 session_state["store"] 에 둠. 응답 전이면 여기서 실행을 멈춤."""
    if st.session_state.get("store_loaded"):
        return
    raw = _st_local_storage(method="getAll", key=_GET_KEY, default=None)
    if raw is None:
        st.markdown("### 🌱 학습 기록을 불러오는 중…")
        if st.button("기록 없이 시작하기"):
            st.session_state["store"] = empty_store()
            st.session_state["store_loaded"] = True
            st.rerun()
        st.stop()
    value = raw.get(STORAGE_KEY) if isinstance(raw, dict) else None
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        data = None
    st.session_state["store"] = _sanitize(data)
    st.session_state["store_loaded"] = True


def store() -> dict[str, Any]:
    return st.session_state["store"]


def persist() -> None:
    """현재 기록을 localStorage 에 씀. 값이 바뀌었을 때만 브라우저 쪽에서 실제로 저장됨."""
    if not st.session_state.get("store_loaded"):
        return
    _st_local_storage(method="setItem", itemKey=STORAGE_KEY, itemValue=_dump_within_limit(store()), key=_SET_KEY)


def _dump_within_limit(data: dict[str, Any]) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= MAX_STORE_CHARS:
        return text
    # 용량 초과 시 오래된 오답의 사진부터 뺌 (기록 자체는 유지)
    notes = sorted(data["wrongNotes"].values(), key=lambda n: n.get("lastWrongAt", ""))
    for note in notes:
        if note.pop("photo", None) is not None:
            text = json.dumps(data, ensure_ascii=False)
            if len(text) <= MAX_STORE_CHARS:
                break
    return text


# ───────────── 기록 규칙 ─────────────


def record_result(question_id: str, result: dict[str, Any]) -> None:
    """풀이 결과 기록 + 오답노트 갱신.
    - 오답/부분정답: 오답노트에 추가(또는 오답 횟수 +1), 연속 정답 0, 졸업 해제
    - 정답: 오답노트에 있으면 연속 정답 +1, GRADUATE_STREAK 도달 시 졸업
    """
    data = store()
    now = _now()
    s = data["stats"].get(question_id, {"tries": 0, "correct": 0})
    data["stats"][question_id] = {
        "tries": s["tries"] + 1,
        "correct": s["correct"] + (1 if result["verdict"] == "correct" else 0),
        "last": now,
    }

    note = data["wrongNotes"].get(question_id)
    if result["verdict"] == "correct":
        if note:
            streak = note["consecutiveCorrect"] + 1
            note["consecutiveCorrect"] = streak
            note["graduated"] = note["graduated"] or streak >= GRADUATE_STREAK
    else:
        entry = {
            "questionId": question_id,
            "wrongCount": (note or {}).get("wrongCount", 0) + 1,
            "consecutiveCorrect": 0,
            "lastWrongAt": now,
            "lastUserAnswer": result["user_answer"],
            "graduated": False,
        }
        photo = result.get("photo") or (note or {}).get("photo")
        if photo:
            entry["photo"] = photo
        data["wrongNotes"][question_id] = entry


def add_to_wrong_notes(question_id: str, user_answer: str) -> None:
    """정답이어도 수동으로 오답노트에 저장."""
    notes = store()["wrongNotes"]
    note = notes.get(question_id)
    if note and not note["graduated"]:
        return
    notes[question_id] = {
        "questionId": question_id,
        "wrongCount": (note or {}).get("wrongCount", 0),
        "consecutiveCorrect": 0,
        "lastWrongAt": _now(),
        "lastUserAnswer": user_answer,
        "graduated": False,
    }


def set_graduated(question_id: str, graduated: bool) -> None:
    note = store()["wrongNotes"].get(question_id)
    if note:
        note["graduated"] = graduated
        note["consecutiveCorrect"] = 0


def remove_wrong_note(question_id: str) -> None:
    store()["wrongNotes"].pop(question_id, None)


def toggle_fav_tip(question_id: str) -> None:
    favs = store()["favTips"]
    if question_id in favs:
        favs.remove(question_id)
    else:
        favs.append(question_id)


def reset_all() -> None:
    settings = store()["settings"]
    st.session_state["store"] = {**empty_store(), "settings": settings}


def export_json() -> str:
    return json.dumps(store(), ensure_ascii=False, indent=2)


def import_json(text: str) -> None:
    """백업 JSON 불러오기. 형식이 틀리면 ValueError."""
    data = json.loads(text)
    if not isinstance(data, dict) or not any(k in data for k in ("wrongNotes", "stats", "favTips")):
        raise ValueError("온실가스 실기 준비 앱의 백업 파일이 아니에요")
    st.session_state["store"] = _sanitize(data)


# ───────────── 사진 ─────────────


def compress_image(image_bytes: bytes, max_side: int = 900, quality: int = 65) -> str:
    """사진을 작은 JPEG data URL 로 축소 (오답노트 저장용). 휴대폰 사진의 회전 정보도 반영."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def data_url_bytes(data_url: str) -> bytes:
    return base64.b64decode(data_url.split(",", 1)[1])
