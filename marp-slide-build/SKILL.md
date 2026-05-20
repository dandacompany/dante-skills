---
name: marp-slide-build
description: Marp 마크다운으로 임원 보고용 시장조사 보고서 슬라이드 12~15장을 빌드해 PDF·HTML로 출력하는 표준 패턴. 단테랩스 paper+ink+rust 디자인 가드와 12장 구성 골격을 강제한다. Brand Intelligence Lab 의 슬라이드 제작자 에이전트가 사용한다.
---

# marp-slide-build

> 마크다운 → Marp → PDF/HTML 임원 보고용 슬라이드 빌드 패턴. 단테랩스 디자인 가드 위반 시 빌드 거부.

## 빌드 명령

```bash
cd /workspace
marp report.md --pdf  --allow-local-files -o report.pdf
marp report.md --html --allow-local-files -o report.html
```

## 슬라이드 12장 표준 구성

| # | 섹션 | 입력 |
|---|---|---|
| 1 | 표지 + 한 줄 결론 | 분석가 종합 |
| 2 | 브랜드 개요 | brand_profile.md |
| 3 | 제품·서비스 라인업 | brand_profile + Web Unlocker scrap |
| 4 | 경쟁사 매트릭스 | competitor_matrix.csv |
| 5 | 검색 트렌드 (12개월) | serp_trends.json |
| 6 | 언론·SNS 멘션 | social_mentions.json |
| 7 | 리뷰 분석 | Trustpilot dataset |
| 8 | 가격 정책 비교 | pricing_scrape.csv |
| 9 | 시장 점유 / 카테고리 동향 | Naver/Coupang products dataset |
| 10 | SWOT 매트릭스 | swot_matrix.json (swot-from-signals) |
| 11 | 기회·리스크 TOP 3 | insights.md |
| 12 | 시사점 + 다음 액션 | 분석가 종합 |

## 디자인 가드 (위반 시 빌드 거부)

- **팔레트**: paper + ink + rust accent
- **시그니처**: 좌측 4px rust accent stripe
- **본문**: 명조 세리프 (Noto Serif KR)
- **헤더**: 슬랩 세리프
- **금지**:
  - 글래스모피즘 (`backdrop-filter`)
  - 그라데이션 블롭 / mesh gradient
  - 네온
  - blur shadow / 컬러 드롭섀도
  - 이모지
  - 8px 초과 corner radius

## 차트

- 입력: `chart_spec.json` (데이터 분석가가 떨군 차트 사양)
- 출력: `assets/charts/*.png`
- 라이브러리: matplotlib 또는 plotly
- 색: 디자인 가드 토큰만 사용

## 검증

```bash
# 빌드 후 PDF 페이지 수 + 디자인 가드 위반 키워드 검색
pdfinfo report.pdf | grep "Pages:"   # 12 이상
grep -E "backdrop-filter|blur\(|emoji" report.md && echo "WARN: 디자인 가드 위반"
```

## 절대 제약

- 데이터·문구 임의 가공 금지. 분석가 산출물 그대로 인용.
- 디자인 가드 위반 0건 강제.
- 평문 API 키 노출 금지.
- `brand-research-glossary` 표기 규칙 준수.
