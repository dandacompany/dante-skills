# 출력 명세 — 확정 포맷 + 결정론 규칙

산출물은 두 개다. 둘 다 분석기가 같은 입력에서 **항상 같은 결과**를 낸다.

## 1. positioning.json (기계 판독용)

```json
{
  "schema_version": "1.0",
  "generated_for": "3040 men fashion (KR)",
  "as_of": "2026-06-13",
  "currency": "KRW",
  "observation_count": 8,
  "excluded_observation_count": 0,
  "banding": {
    "mode": "user",
    "bands": [
      { "label": "저가", "min": null, "max": 80000.0 },
      { "label": "중가", "min": 80000.0, "max": 200000.0 },
      { "label": "프리미엄", "min": 200000.0, "max": null }
    ]
  },
  "bands": [
    {
      "label": "저가",
      "count": 2,
      "share": 0.25,
      "min": 49000.0,
      "p25": 51500.0,
      "median": 54000.0,
      "p75": 56500.0,
      "max": 59000.0,
      "mean": 54000.0,
      "stdev": 5000.0,
      "examples": [
        {
          "brand": "TOPTEN",
          "item": "기본 자켓",
          "price": 49000.0,
          "source_url": "https://shop.example.com/p/1"
        }
      ]
    }
  ],
  "whitespace": [
    {
      "type": "largest_gap",
      "interval": [329000.0, 790000.0],
      "width": 461000.0,
      "width_pct_of_range": 0.62,
      "confidence": "medium",
      "evidence": "7 obs at/below 329000.0, 1 obs at/above 790000.0"
    }
  ],
  "outliers": [],
  "value_metrics": { "per_unit": 8 },
  "data_gaps": [],
  "flags": {
    "red": [],
    "yellow": ["8 observations is a small sample; treat bands as indicative"]
  }
}
```

필드 뜻

- `as_of` — 보고 기준일. 지정 안 하면 관측치의 가장 최근 `observed_at`을 쓴다(시간 함수 미사용 → 결정론).
- `banding.mode` — `user`(임계값) 또는 `quantile`(분위수).
- `bands[]` — 밴드별 통계. `share`는 전체 대비 비율, `stdev`는 모표준편차.
- `whitespace[]` — `empty_band`(빈 사용자 밴드)와 `largest_gap`(가격축 최대 빈구간). 폭 내림차순 정렬.
- `outliers[]` — 밴드 IQR 울타리 밖 관측치(버리지 않고 표시만).
- `data_gaps[]` · `flags` — 누락·주의 사항. 비어 있어도 키는 유지.

## 2. pricing-landscape.md (사람 판독용)

`--format md`로 생성하는 고정 섹션 보고서.

```markdown
# Pricing Landscape: {시장}

_Skill: price-positioning | as of {날짜} | currency {통화}_

Observations analyzed: {N} (excluded: {M})

## Bands

| Band | Count | Share | Min | Median | Max | Mean | Stdev |
| ---- | ----: | ----: | --: | -----: | --: | ---: | ----: |
| ...  |   ... |   ... | ... |    ... | ... |  ... |   ... |

## Pricing Whitespace

- **{type}** interval {[lo, hi]} (confidence: {high/medium/low}) — {evidence}

## Data Gaps

- ...

## Flags

**Red**

- ...
  **Yellow**
- ...
```

밴드 표·화이트스페이스·갭·플래그는 분석기가 채운다. **진입 가격대 권고**(가격/가치/모델 경쟁)는 분석가가 `methodology.md` 7원리로 해석해 보고 끝에 근거·확신도와 함께 덧붙인다.

## 결정론 규칙

- 같은 입력 파일 → 같은 출력(바이트 동일). 정렬은 밴드=하한 오름차순, 예시=가격 오름차순, 화이트스페이스=폭 내림차순, 이상치=밴드·가격순.
- 무작위·현재시각 의존 값 없음. 날짜는 데이터에서만 가져온다.
- 통화가 섞이면 최빈 통화만 분석하고 나머지는 `data_gaps`에 남긴다(조용한 평균 금지).
- 분석기는 표준 라이브러리만 쓰고 네트워크·환경변수·외부 실행이 없다. 입력 파일을 읽고 결과 파일을 쓸 뿐이다.
