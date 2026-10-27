"""세트 구성용 문제 변환. app/src/lib/quiz.ts 를 옮긴 것."""

import random
import re
from typing import Any

from core.grading import format_number

CIRCLED = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
_BLANK_RE = re.compile(r"\{\{(\d+)\}\}")


def calc_as_blanks(q: dict[str, Any]) -> dict[str, Any]:
    """계산 문제의 단계 값들을 빈칸으로 바꾼 형태 (난이도 하·중)."""
    steps = q["steps"]
    formatted = [format_number(s["value"], s.get("digits", 0)) for s in steps]

    def hide(expr: str, upto: int) -> str:
        # 뒤 단계 식에 앞 단계 정답이 그대로 보이면 빈칸 번호로 가림
        for j, v in enumerate(formatted[:upto]):
            expr = re.sub(rf"(?<![\d.,]){re.escape(v)}(?![\d.,]*\d)", f"({CIRCLED[j]})", expr)
        return expr

    template = "\n".join(f"{s['label']}: {hide(s['expr'], i)} = {{{{{i + 1}}}}} {s['unit']}" for i, s in enumerate(steps))
    blanks = [{"answer": formatted[i], "distractors": number_distractors(s["value"], s.get("digits", 0))} for i, s in enumerate(steps)]
    return {"template": template, "blanks": blanks, "unordered": False}


def as_blank_question(q: dict[str, Any]) -> dict[str, Any]:
    if q["type"] == "calc":
        return calc_as_blanks(q)
    return {"template": q["template"], "blanks": q["blanks"], "unordered": q.get("unordered", False)}


def number_distractors(v: float, digits: int) -> list[str]:
    """숫자 정답의 그럴듯한 오답 보기 (단위 실수·GWP 누락 등 흔한 실수 배수)."""
    factors = [10, 0.1, 1000, 0.001, 1.1, 0.9, 21, 1 / 21, 3.664, 1.21]
    random.shuffle(factors)
    answer = format_number(v, digits)
    out: list[str] = []
    for f in factors:
        s = format_number(v * f, digits)
        if s != answer and s not in out and float(s.replace(",", "")) != 0:
            out.append(s)
        if len(out) == 3:
            break
    return out


def choices_for(blank: dict[str, Any]) -> list[str]:
    """4지선다 보기 (정답 + 오답 3개, 섞어서)."""
    distractors = list(blank.get("distractors", []))
    random.shuffle(distractors)
    choices = [blank["answer"], *distractors[:3]]
    random.shuffle(choices)
    return choices


def parse_template(template: str) -> list[tuple[str, Any]]:
    """템플릿을 ("text", 글자) / ("blank", 빈칸 번호 0부터) 조각으로 분리."""
    parts: list[tuple[str, Any]] = []
    last = 0
    for m in _BLANK_RE.finditer(template):
        if m.start() > last:
            parts.append(("text", template[last : m.start()]))
        parts.append(("blank", int(m.group(1)) - 1))
        last = m.end()
    if last < len(template):
        parts.append(("text", template[last:]))
    return parts


def fill_template(template: str, fill) -> str:
    """빈칸 자리를 fill(빈칸 번호) 결과로 채운 문자열."""
    return _BLANK_RE.sub(lambda m: fill(int(m.group(1)) - 1), template)


def full_answer(q: dict[str, Any]) -> str:
    """모범답안 전체 문장 (빈칸을 정답으로 채움)."""
    return fill_template(q["template"], lambda i: q["blanks"][i]["answer"])
