---
name: brand-research-glossary
description: B2C 브랜드 시장조사 산출물에서 표기·용어 일관성을 보장하는 회사 공통 용어 사전. 무신사·29CM·W컨셉·LF몰 등 한국 e-커머스/패션 브랜드 표기, Bright Data 제품 명칭(Web Unlocker · SERP API · Datasets · Scraping Browser), Marp/Reveal.js 슬라이드 형식 명칭을 통일한다. Brand Intelligence Lab 모든 에이전트가 상속한다.
---

# brand-research-glossary

> Brand Intelligence Lab 회사 공통 용어 사전. 모든 에이전트가 상속하여 산출물의 표기·용어를 일관되게 유지한다.

## 표기 규칙

### 브랜드 명

- **무신사 (MUSINSA)** — 1차 운영 도메인. 영문은 모두 대문자 `MUSINSA`.
- **29CM** — 숫자 그대로. `29cm` 소문자 표기 금지.
- **W컨셉** — 한글+영문 혼합 그대로.
- **LF몰** — 한글 그대로.

### Bright Data 제품 명칭

- **Web Unlocker** (zone=`web_unlocker1`)
- **SERP API**
- **Datasets** (마켓플레이스 사전 다운로드)
- **Scraping Browser** (참고용)
- 모든 호출은 코멘트 첫 줄에 `사용 도구: ...` 로 명시.

### 슬라이드 형식

- **Marp** 마크다운 → PDF + HTML
- **Reveal.js** / **Slidev** (대안)
- 차트: PNG (matplotlib / plotly)

### 인용·근거

- `source_url` 100% 보존
- `captured_at` (수집 시각) 메타 포함
- `provenance_note` (출처 신뢰도 한 줄)
- `public_data_only=true` 라벨

## 금지 표현

- "추천", "매수", "좋다", "나쁘다" → "관찰", "주목" 으로 대체
- 비공식 평가·소문 인용 금지
- 추측 어휘("아마", "~일 것 같다") 금지

## 적용 범위

- 브랜드 리서처: 수집 산출물의 source 표기
- 데이터 분석가: 인사이트·SWOT 본문
- 슬라이드 제작자: 슬라이드 헤더·캡션·차트 레이블

## 검증

코멘트나 보고서에 위 금지 표현이 포함되면 해당 라인을 보고 + 수정 제안.
