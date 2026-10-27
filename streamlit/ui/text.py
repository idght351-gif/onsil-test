"""마크다운 출력 도우미."""

_MD_SPECIAL = "\\`*_~#|[]<>$"


def md_escape(s: str) -> str:
    """문제·해설 글자가 마크다운(굵게·취소선·수식 $)으로 해석되지 않게 이스케이프."""
    return "".join("\\" + ch if ch in _MD_SPECIAL else ch for ch in s)


def md_lines(s: str) -> str:
    """줄바꿈을 마크다운 줄바꿈으로."""
    return s.replace("\n", "  \n")
