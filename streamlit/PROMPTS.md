# Streamlit 버전 단계별 개발 프롬프트

[PRD.md](PRD.md)를 바탕으로 한 4단계 작업 지시문입니다. 단계마다 그대로 복사해서 AI 코딩 도구에 붙여 넣으면 됩니다. 앞 단계가 "완료 기준"을 통과한 뒤에 다음 단계로 넘어갑니다.

공통 전제
- 작업 폴더: `streamlit/` (기존 React 앱 `app/`은 수정하지 않음)
- 문제 원본: `app/src/data/questions.ts`, 채점 원본: `app/src/lib/grading.ts`, `app/src/lib/quiz.ts`, `app/src/lib/storage.ts`
- 학습 기록 저장: 브라우저 저장소(PRD 5장 B안) + JSON 백업 내보내기/불러오기
- 모든 화면 문구는 한국어, 모바일(375px) 우선

---

## 1단계: 기본 뼈대 작성

```
streamlit/PRD.md를 읽고 Streamlit 앱의 기본 뼈대를 만들어줘.

1. PRD 6.1의 폴더 구조대로 파일을 만들어 (app.py, requirements.txt, .streamlit/config.toml,
   data/, core/, ui/screens/, tests/).
2. app/src/data/questions.ts와 categories.ts를 data/questions.json, data/categories.json으로
   변환해. 손으로 옮기지 말고 변환 스크립트(scripts/export_data.mjs)를 만들어 실행해.
   61문항이 빠짐없이 들어갔는지 개수를 확인해.
3. app.py는 st.session_state["screen"] 값으로 화면을 바꾸는 라우터로 만들어.
   화면 10개(home, difficulty, category, countdown, quiz, result, wrong_notes, settings 등)는
   ui/screens/에 함수 하나씩 두고, 지금은 제목과 "다음 화면" 버튼만 있는 임시 화면으로 둬.
4. .streamlit/config.toml에 PRD 4.1 테마를 넣어.
5. requirements.txt에 streamlit, streamlit-local-storage, Pillow, pytest를 적어.

완료 기준: `streamlit run streamlit/app.py`가 오류 없이 켜지고,
홈 → 난이도 → 카테고리 → 카운트다운 → 문제 → 결과 → 오답노트까지 버튼으로 이동된다.
```

---

## 2단계: 기능 추가

```
1단계 뼈대 위에 PRD 2장 기능을 모두 구현해줘.

1. core/grading.py: app/src/lib/grading.ts를 그대로 옮겨.
   정규화(공백·대소문자·쉼표·아래첨자·가운뎃점 무시), 동의어, 숫자 허용 오차 0.1%,
   unordered 빈칸, 키워드 통과 70%, 계산 단계 통과 75%, 화학식 숫자(CO2의 2) 제외.
2. core/quiz.py: 세트 구성(무작위 N문항), 4지선다 보기 생성(숫자 정답은 흔한 실수 배수로 오답 생성),
   계산 문제를 빈칸 형태로 바꾸기(앞 단계 정답은 ①② 표시로 가림), 템플릿 파싱.
3. core/storage.py: 브라우저 저장소에 오답노트·통계·즐겨찾기·설정을 JSON으로 저장.
   오답노트 규칙(오답 자동 저장, 연속 2회 정답 졸업, 수동 저장·졸업·삭제)과
   JSON 내보내기/불러오기. 사진은 Pillow로 긴 쪽 900px JPEG로 줄여 저장.
4. 화면 로직:
   - 3·2·1 카운트다운(st.empty + 1초 간격)
   - 난이도 하: 빈칸별 4지선다 / 중: 빈칸별 입력 / 상: 서술형 입력 + 자가 채점
   - 계산 문제 상: 풀이 입력 또는 사진(st.camera_input, st.file_uploader) + 최종값 + 단계 셀프 체크
   - 채점 결과 → 해설(모범답안·해설·꿀팁·즐겨찾기) → 다음 문제 → 결과 요약 → 오답노트
   - 오답노트 탭(복습 중/졸업/꿀팁), 카테고리 필터, 정렬, 오답만 다시 풀기
   - 설정: 문항 수 5/10/20, 데이터 초기화, 기록 내보내기/불러오기
5. tests/test_grading.py: 61문항 전부에 대해
   정답 입력→정답, 오답 보기→오답, 보기 4개·중복 없음, 계산 빈칸 정답 누출 없음,
   계산 풀이 전체 입력→정답, 최종값만→부분 정답, 3.664 사용 시 정답, 큰 값 0.24% 차이→부분 정답을 검사해.

완료 기준: `pytest streamlit/tests`가 전부 통과하고, 난이도 하·중·상으로 세트를 끝까지 풀 수 있다.
```

---

## 3단계: UI

```
기능은 그대로 두고 PRD 4장 디자인을 적용해줘. 기존 React 앱(app/src/index.css, components/)의
모양을 기준으로 맞춰.

1. ui/styles.py: 전역 CSS 한 곳에 모아 st.html로 주입.
   Black Han Sans 글꼴, 진초록(#0b4a09) 구겨진 종이 배경, 형광 연두(#b6fe00) 강조,
   종이 카드(.paper), 모눈종이(.grid-paper), 마스킹테이프(.tape), 캡슐 버튼, Streamlit 기본 메뉴·여백 정리.
2. ui/components.py: HTML 조각 함수
   - 원형 테이프 스티커(SVG, 가장자리 둥근 글자), 캡슐 카드, 테이프 롤 장식
   - 손그림 ⭕/△/✕, 밑줄, 하트 (SVG 그리기 애니메이션)
   - 테이프 떼기(정답 위 테이프가 자동으로 말려 올라가며 떼어짐)
   - 정답률 원형 그래프, 3·2·1 큰 숫자
3. 각 화면에 적용: 홈(기울어진 제목, 캡슐 현황), 난이도(테이프 롤 + 캡슐, 01·02·03),
   카테고리(스티커 10개), 문제(테이프 붙은 종이 카드), 채점(테이프 떼기 + 빨간 펜 채점),
   해설(모눈종이 + 노란 메모지 꿀팁), 결과(큰 점수 + 캡슐 목록), 오답노트·설정(종이 카드).
4. 애니메이션은 "방금 제출했을 때"만 출력해서 다시 그려질 때 반복되지 않게 해.

완료 기준: 375px 폭에서 가로 스크롤 없이 모든 화면이 기존 React 앱과 같은 콘셉트로 보인다.
```

---

## 4단계: 에러확인 및 검토 (Playwright)

```
Playwright로 실제 브라우저에서 앱 전체를 검사하고 문제를 고쳐줘.

1. streamlit run으로 앱을 켜고 Playwright로 375x812(모바일) 화면에서 접속해.
2. 시나리오:
   - 홈 → 난이도 하 → 카테고리 → 3·2·1 → 10문항 끝까지 → 결과 → 오답노트
   - 난이도 중: 빈칸 입력 채점
   - 난이도 상 서술형: 키워드 채점 + 자가 채점 바꾸기
   - 난이도 상 계산: 풀이 입력 채점, 사진 업로드 → 셀프 체크 → 채점
   - 오답노트: 다시 풀기, 졸업, 삭제 / 설정: 문항 수, 내보내기·불러오기, 초기화
   - 새로고침 후 오답노트·통계가 유지되는지
3. 화면마다 스크린샷을 남기고, 브라우저 콘솔 오류와 Streamlit 예외 메시지가 없는지 확인해.
4. 가로 스크롤, 글자 겹침, 버튼 누름 반응 등 UI 문제를 점검해.
5. 찾은 문제를 고치고 같은 시나리오를 다시 돌려 통과를 확인해. pytest도 다시 돌려.
6. 검토 결과(통과 항목, 고친 문제, 남은 문제)를 streamlit/REVIEW.md에 정리해.

완료 기준: 모든 시나리오 통과, 콘솔·Streamlit 오류 0건, REVIEW.md 작성.
```
