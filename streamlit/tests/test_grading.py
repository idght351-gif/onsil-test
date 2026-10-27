"""61문항 데이터·채점 규칙 검사. 실행: streamlit 폴더에서 `python -m pytest tests`"""

import json
import re
from pathlib import Path

import pytest

from core.grading import (
    extract_numbers,
    grade_blanks,
    grade_calc,
    grade_keywords,
    grade_steps_from_text,
    last_number,
    normalize,
)
from core.quiz import as_blank_question, calc_as_blanks, choices_for, full_answer

QUESTIONS = json.loads((Path(__file__).resolve().parent.parent / "data" / "questions.json").read_text(encoding="utf-8"))
BY_ID = {q["id"]: q for q in QUESTIONS}
CALC = [q for q in QUESTIONS if q["type"] == "calc"]
TEXT = [q for q in QUESTIONS if q["type"] == "text"]


def test_question_count_and_unique_ids():
    assert len(QUESTIONS) == 61
    assert len(BY_ID) == len(QUESTIONS)


@pytest.mark.parametrize("q", QUESTIONS, ids=lambda q: q["id"])
def test_blank_template_matches_blanks(q):
    bq = as_blank_question(q)
    nums = [int(n) for n in re.findall(r"\{\{(\d+)\}\}", bq["template"])]
    assert max(nums) == len(bq["blanks"])
    assert len(set(nums)) == len(bq["blanks"])


@pytest.mark.parametrize("q", QUESTIONS, ids=lambda q: q["id"])
def test_choices_are_four_and_unique(q):
    for blank in as_blank_question(q)["blanks"]:
        choices = choices_for(blank)
        assert len(choices) == 4, choices
        assert len({normalize(c) for c in choices}) == 4, choices
        assert blank["answer"] in choices


@pytest.mark.parametrize("q", QUESTIONS, ids=lambda q: q["id"])
def test_correct_answers_pass_and_distractors_fail(q):
    bq = as_blank_question(q)
    assert grade_blanks(bq["blanks"], [b["answer"] for b in bq["blanks"]], bq["unordered"])["verdict"] == "correct"
    wrong = [b["distractors"][0] for b in bq["blanks"]]
    assert grade_blanks(bq["blanks"], wrong, bq["unordered"])["verdict"] != "correct"


@pytest.mark.parametrize("q", TEXT, ids=lambda q: q["id"])
def test_model_answer_passes_keywords(q):
    result = grade_keywords(q["keywords"], full_answer(q))
    assert result["verdict"] == "correct", [h for h in result["keyword_hits"] if not h["hit"]]


@pytest.mark.parametrize("q", CALC, ids=lambda q: q["id"])
def test_calc_blank_template_does_not_leak_answers(q):
    bq = calc_as_blanks(q)
    numbers_in_template = re.findall(r"\d[\d,]*(?:\.\d+)?", bq["template"])
    for blank in bq["blanks"]:
        assert blank["answer"] not in numbers_in_template, blank["answer"]


@pytest.mark.parametrize("q", CALC, ids=lambda q: q["id"])
def test_calc_full_work_is_correct_and_final_only_is_partial(q):
    steps = q["steps"]
    work = "\n".join(f"{s['expr']} = {s['value']}" for s in steps)
    final = str(steps[-1]["value"])
    assert grade_calc(steps, final, grade_steps_from_text(steps, work))["verdict"] == "correct"
    if len(steps) > 1:
        assert grade_calc(steps, final, [False] * len(steps))["verdict"] == "partial"


def test_unordered_blanks_accept_any_order():
    q = BY_ID["Q2021-2-07"]
    assert grade_blanks(q["blanks"], ["항공", "선박", "철도", "도로"], True)["verdict"] == "correct"


def test_synonyms_subscripts_and_commas():
    q = BY_ID["Q2020-4-02"]
    assert grade_blanks(q["blanks"], ["caso3", "CaSO4·2H₂O"])["verdict"] == "correct"
    q = BY_ID["Q2020-4-13"]
    assert grade_blanks(q["blanks"], ["50000", "200", "15000", "80"])["verdict"] == "correct"


def test_chemical_formula_digits_are_not_numbers():
    assert extract_numbers("CO2 = 2370 x 95,100 / 1000 tCO2-eq") == [2370, 95100, 1000]


def test_typed_work_without_final_uses_last_number():
    q = BY_ID["Q2021-2-15"]
    work = (
        "열량 = 100,000t x 1000 x 23.7 / 10^6 = 2,370 TJ\nCO2 = 2370 x 95100 /1000 = 225,387 t\n"
        "CH4 = 2370 x 1 / 1000 x 21 = 49.77\nN2O = 2370 x 1.5/1000 x 310 = 1102.05\n합계 = 226,538.82 tCO2-eq"
    )
    assert last_number(work) == "226538.82"
    assert grade_calc(q["steps"], last_number(work), grade_steps_from_text(q["steps"], work))["verdict"] == "correct"


def test_tolerance_is_tight_for_large_values():
    q = BY_ID["Q2021-2-15"]
    # 226,000 은 226,538.82 와 0.24% 차이 → 최종값 오답
    assert grade_calc(q["steps"], "226,000", [True] * 4 + [False])["final_ok"] is False


def test_3664_variant_is_accepted():
    q = BY_ID["Q2021-4-09"]
    assert grade_calc(q["steps"], "366.4", grade_steps_from_text(q["steps"], "100 x 3.664 = 366.4"))["verdict"] == "correct"
