# kor-review-taker 변경 이력

새 항목은 맨 위에 쓴다. 형식: `## YYYY-MM-DD <platform>: <요약>` + 증상·원인·수정·검증.

## 2026-10-22 coupang: 페이지 간격 최소 3초 + 같은 브라우저 재방문 30분 대기

- 증상: 같은 브라우저로 하루 여러 번 열면 페이지째 "사용권한이 없습니다"(10-21). WARP IP 로는 첫 방문부터 Access denied(10-22).
  두 경우 모두 리뷰 API 를 부르기 전 페이지 단계에서 막혔다 — 페이지 간격보다 방문 횟수·IP 평판이 원인으로 보인다.
- 수정: `take.mjs` `PLATFORMS` 에 `minDelayMs`(쿠팡 3000, G마켓 2000)·`cooldownMin`(쿠팡 30) 추가. evaluate 제한 시간도 이 간격으로 계산.
  `~/.cache/kor-review-taker/visits.json` 에 `플랫폼@브라우저` 방문 시각을 남기고, 대기 중이면 페이지를 열지 않고 COOLDOWN(7). `--ignore-cooldown` 으로 무시.
- 검증: 실제 WARP 방문 기록(15:44Z)으로 19분 뒤 재실행 → `COOLDOWN 11분 남음`, 종료 코드 7, 방문 기록 덮어쓰지 않음.
  3초 간격의 실제 수집은 사용자 요청으로 쿠팡을 다시 열지 않아 **미시험**.

## 2026-10-22 최초 작성

- 수집기: 쿠팡·네이버(브랜드스토어)·11번가·하이마트·SSG·롯데ON 검증, G마켓 부분 검증. 근거는 `references/platforms.md`.
- 실행기 시험 중 고친 것
  - 11번가 0건: iframe 요청 탐색 정규식이 `…/same-kind/products/{id}/review-list`(비슷한 상품 리뷰)에 부분 일치 →
    경로 전체 `^/products/\d+/review-list$` 로 고정. 0건 + 화면 건수 미확인을 OK 로 보던 판정을 STRUCTURE 로 바꿈.
  - 네이버·롯데ON 날짜 판정 실패: ISO 시각의 밀리초 `.` 까지 `-` 로 바꾸던 정규화 → `YYYY.MM.DD` 형태만 바꾸도록.
  - 쿠팡: 차단 페이지(제목 "쿠팡!")를 본문 문구로 감지, 401/403 을 BLOCKED 로 분류(구조 수정으로 오인 방지).
  - 네이버 스마트스토어: 로그아웃 브라우저가 로그인 페이지로 넘어가는 것을 LOGIN_REQUIRED(6) 로 분류.
