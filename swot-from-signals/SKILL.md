---
name: swot-from-signals
description: 브랜드 리서처가 수집한 정성·정량 신호로부터 SWOT(강점·약점·기회·위협) 매트릭스를 자동 도출하는 분석 패턴. 각 사분면 3개씩, 모든 항목에 근거 URL 또는 시그널 값을 명시한다. Brand Intelligence Lab 의 데이터 분석가 에이전트가 사용한다.
---

# swot-from-signals

> 정성·정량 수집물 → SWOT 4사분면 자동 도출 패턴. 근거 URL/시그널 값 100% 명시.

## 입력 (브랜드 리서처 산출물 6종)

- `brand_profile.md` — 기업 개요, 미션, BM, 주요 제품
- `competitor_matrix.csv` — 경쟁사 3~5곳 (가격대·타겟·강점)
- `pricing_scrape.csv` — 자사·경쟁사 가격 50~100건
- `serp_trends.json` — 12개월 검색 트렌드
- `social_mentions.json` — Instagram·TikTok·Threads 멘션
- `dataset_imports/*.csv` — Naver / Coupang / 글로벌 SPA / Trustpilot / LinkedIn

## 절차

1. 위 6종 입력을 pandas로 로드 → 스키마·결측·중복 점검
2. 신호어 추출:
   - **가격 분포**: 평균·중앙값·표준편차, 자사 vs 경쟁사
   - **시즌성**: serp_trends 월별 평균 + 표준편차
   - **SNS 감성**: social_mentions 키워드 빈도 상위 10
   - **리뷰 분포**: Trustpilot 평점 분포 + 키워드
   - **채용 동향**: LinkedIn company headcount/jobs 트렌드
3. 신호어를 4사분면(S·W·O·T)에 매핑 — 각 칸 3개씩
4. 각 항목에 `근거: <source_url 또는 signal_value>` 명시

## 출력 형식 (JSON)

```json
{
  "strengths":     [{"text": "...", "evidence": "https://..."}, ...],
  "weaknesses":    [{"text": "...", "evidence": "signal_value: ..."}, ...],
  "opportunities": [{"text": "...", "evidence": "..."}, ...],
  "threats":       [{"text": "...", "evidence": "..."}, ...]
}
```

## 절대 제약

- 추측 어휘 사용 금지. 신호어에서 출발한 객관적 서술만.
- 평가성 어휘("좋다", "나쁘다") 금지. 사실 기반.
- 근거 칸이 비어있으면 항목 자체를 제외 (3개 미만이어도 OK).
- `brand-research-glossary` 표기 규칙 준수.

## 슬라이드 제작자 인계

`swot_matrix.json` 으로 떨군 결과를 슬라이드 제작자가 `marp-slide-build` 스킬의 슬라이드 10번(SWOT 매트릭스)에 그대로 인용.
