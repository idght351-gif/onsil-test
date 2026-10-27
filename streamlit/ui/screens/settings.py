from datetime import date

import streamlit as st

from core import storage
from core.nav import go


def render() -> None:
    if st.button("← 뒤로"):
        go("home")
    st.header("설정")
    settings = storage.store()["settings"]

    count = st.segmented_control("세트당 문항 수", [5, 10, 20], default=settings["count"], format_func=lambda n: f"{n}문항", key="set_count")
    if count and count != settings["count"]:
        settings["count"] = count
        st.rerun()

    st.subheader("기록 백업")
    st.caption("기록은 이 기기의 브라우저에만 저장돼요. 기기를 바꿀 때 내보낸 파일을 불러오세요.")
    st.download_button(
        "⬇️ 기록 내보내기 (JSON)",
        data=storage.export_json(),
        file_name=f"온실가스실기_기록_{date.today():%Y%m%d}.json",
        mime="application/json",
        width="stretch",
    )
    uploaded = st.file_uploader("기록 불러오기", type=["json"], key="set_import")
    if uploaded is not None and st.button("불러온 기록으로 바꾸기", width="stretch"):
        try:
            storage.import_json(uploaded.getvalue().decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            st.error(f"불러오지 못했어요: {e}")
        else:
            st.success("기록을 불러왔어요.")
            st.rerun()

    st.subheader("초기화")
    with st.popover("학습 데이터 초기화", width="stretch"):
        st.caption("오답노트·학습기록·꿀팁 즐겨찾기를 모두 지울까요?")
        if st.button("모두 지우기", type="primary"):
            storage.reset_all()
            go("home")
