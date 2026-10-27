"""채점 규칙. app/src/lib/grading.ts 를 그대로 옮긴 것 (두 쪽 기준이 같아야 함).

결과(result)는 dict:
  verdict: "correct" | "partial" | "wrong"
  user_answer: 오답노트에 보여줄 사용자 답 요약
  blank_results / keyword_hits / step_results / final_ok / self_graded / photo (해당될 때만)
"""

import re
from typing import Any

# 난이도 상 서술형: 키워드 포함 비율 기준
KEYWORD_PASS_RATE = 0.7
# 계산 문제: 풀이 단계 통과 비율 기준
STEP_PASS_RATE = 0.75
# 숫자 허용 오차 (상대 0.1%: 중간값 반올림·3.664 vs 44/12 차이 정도만 허용)
NUM_TOLERANCE = 0.001

_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
# CO2·CH4 같은 화학식 숫자(앞에 글자가 붙은 숫자)는 제외
_NUMBER_IN_TEXT_RE = re.compile(r"(?<![A-Za-z\d.,])-?\d[\d,]*(?:\.\d+)?")


def normalize(s: str) -> str:
    """공백·대소문자·쉼표·괄호·아래첨자·가운뎃점 차이를 무시하기 위한 정규화."""
    s = s.translate(_SUBSCRIPTS)
    s = re.sub(r"[·∙•.]", "", s)
    s = re.sub(r"[\s,()（）\-_]", "", s)
    return s.lower()


def parse_number(s: str) -> float | None:
    cleaned = re.sub(r"[,\s]", "", s)
    return float(cleaned) if _NUMBER_RE.match(cleaned) else None


def numbers_close(a: float, b: float) -> bool:
    return abs(a - b) <= max(abs(b) * NUM_TOLERANCE, 0.0011)


def format_number(v: float, digits: int = 0) -> str:
    return f"{v:,.{digits}f}"


def _blank_accepts(blank: dict[str, Any], given: str) -> bool:
    n = normalize(given)
    if not n:
        return False
    ans_num = parse_number(blank["answer"])
    in_num = parse_number(given)
    if ans_num is not None and in_num is not None:
        return numbers_close(in_num, ans_num)
    return any(normalize(a) == n for a in [blank["answer"], *blank.get("synonyms", [])])


def _verdict_from_ratio(hit: int, total: int, pass_rate: float) -> str:
    if total == 0:
        return "wrong"
    if hit / total >= pass_rate:
        return "correct"
    return "partial" if hit > 0 else "wrong"


def grade_blanks(blanks: list[dict[str, Any]], inputs: list[str], unordered: bool = False) -> dict[str, Any]:
    """빈칸 채점 (난이도 하·중 공통). unordered 문제는 다른 빈칸의 정답도 한 번씩 인정."""
    used: set[int] = set()
    results: list[bool] = []
    for i, blank in enumerate(blanks):
        given = inputs[i] if i < len(inputs) and inputs[i] else ""
        if not unordered:
            results.append(_blank_accepts(blank, given))
            continue
        idx = next((j for j, b in enumerate(blanks) if j not in used and _blank_accepts(b, given)), -1)
        if idx >= 0:
            used.add(idx)
        results.append(idx >= 0)
    return {
        "verdict": _verdict_from_ratio(sum(results), len(results), 1),
        "blank_results": results,
        "user_answer": " / ".join(v or "(빈칸)" for v in inputs),
    }


def grade_keywords(keywords: list[str], text: str) -> dict[str, Any]:
    """난이도 상 서술형: 필수 키워드 매칭. "a|b" 는 둘 중 하나만 있으면 인정."""
    n = normalize(text)
    hits = [{"keyword": kw.split("|")[0], "hit": any(normalize(alt) in n for alt in kw.split("|"))} for kw in keywords]
    return {
        "verdict": _verdict_from_ratio(sum(h["hit"] for h in hits), len(hits), KEYWORD_PASS_RATE),
        "keyword_hits": hits,
        "user_answer": text.strip() or "(미작성)",
    }


def extract_numbers(text: str) -> list[float]:
    """풀이 텍스트에서 숫자 추출 (쉼표 포함 숫자 처리, 화학식 숫자 제외)."""
    out = []
    for m in _NUMBER_IN_TEXT_RE.finditer(text):
        try:
            out.append(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return out


def last_number(text: str) -> str:
    """최종값 칸을 비웠을 때 풀이의 마지막 숫자를 최종값으로 사용."""
    nums = extract_numbers(text)
    return repr(nums[-1]) if nums else ""


def grade_steps_from_text(steps: list[dict[str, Any]], work: str) -> list[bool]:
    """풀이 속에 각 단계의 중간값이 등장하는지 확인."""
    nums = extract_numbers(work)
    return [any(numbers_close(n, s["value"]) for n in nums) for s in steps]


def grade_calc(steps: list[dict[str, Any]], final_input: str, step_results: list[bool], **extra: Any) -> dict[str, Any]:
    """계산 문제 최종 판정: 최종값 정답 + 풀이 단계 통과율."""
    final = steps[-1]
    num = parse_number(final_input or "")
    final_ok = num is not None and numbers_close(num, final["value"])
    # 최종값 단계는 최종값 정답 여부로도 인정
    results = [r or (final_ok and i == len(steps) - 1) for i, r in enumerate(step_results)]
    step_ok = sum(results) / len(results) >= STEP_PASS_RATE
    verdict = "correct" if final_ok and step_ok else "partial" if final_ok or step_ok else "wrong"
    return {
        "verdict": verdict,
        "final_ok": final_ok,
        "step_results": results,
        "user_answer": f"최종값: {final_input or '(미입력)'} {final['unit']}",
        **extra,
    }
