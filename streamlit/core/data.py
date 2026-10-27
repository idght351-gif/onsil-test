"""문제·카테고리 데이터 로드. 원본은 data/*.json (scripts/export_data.ts 로 React 앱에서 생성)."""

import json
import random
from pathlib import Path
from typing import Any

import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

DIFFICULTY_LABEL = {"easy": "하", "normal": "중", "hard": "상"}


@st.cache_data
def load_questions() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "questions.json").read_text(encoding="utf-8"))


@st.cache_data
def load_categories() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "categories.json").read_text(encoding="utf-8"))


def questions_by_category(category: str) -> list[dict[str, Any]]:
    questions = load_questions()
    return questions if category == "ALL" else [q for q in questions if q["category"] == category]


def find_question(question_id: str) -> dict[str, Any] | None:
    return next((q for q in load_questions() if q["id"] == question_id), None)


def build_set(pool: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    return random.sample(pool, min(count, len(pool)))


def exam_label(q: dict[str, Any]) -> str:
    exam = q["exam"]
    return f"{exam['year']}년 {exam['round']}회" if exam.get("round") else f"{exam['year']}년"
