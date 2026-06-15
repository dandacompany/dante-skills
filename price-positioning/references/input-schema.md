# 입력 — 정규화 가격 관측 스키마 (도구 무관 수집 계약)

이 스킬은 **이미 수집된** 가격 관측치만 받는다. 어떻게 모았는지는 묻지 않는다. 한 행(또는 JSON 객체 하나)이 **한 시점에 관측한 한 품목의 한 가격**이다.

## 컬럼 정의

| 필드 | 필수 | 타입 | 설명 |
|---|:--:|---|---|
| `brand` | O | 문자열 | 브랜드/사업자/공급자 이름 |
| `item` | O | 문자열 | 품목·SKU·요금제·플랜 이름 |
| `price` | O | 숫자 | 관측된 실판매가(정가 아님). 천 단위 콤마는 허용, 통화기호는 넣지 않는다 |
| `currency` | O | 문자열 | ISO 통화 코드. 예: `KRW`, `USD`, `JPY` |
| `source_url` | O | 문자열 | 그 가격을 본 출처 주소 |
| `observed_at` | O | 날짜 | 관측일 `YYYY-MM-DD` |
| `category` | | 문자열 | 하위 분류(예: 자켓·니트, 또는 SaaS의 플랜군) |
| `tier_hint` | | 문자열 | 수집자가 이미 아는 밴드 라벨(있으면 검증에만 쓰고 강제하지 않음) |
| `value_metric` | | 문자열 | 가치 척도. 예: `per_unit`·`per_seat`·`per_month`·`flat`·`per_usage` |

규칙
- 가격은 통화당 한 숫자다. 통화기호·단위는 빼고 `currency`로 분리한다.
- 통화가 섞여 들어오면 분석기는 **최빈 통화만** 분석하고 나머지는 데이터 갭으로 남긴다. 가능하면 수집 단계에서 한 통화로 모은다.
- 같은 품목을 날짜만 달리해 여러 번 관측해도 된다. 각각 한 행이다.

## CSV 예시

```text
brand,item,price,currency,source_url,observed_at,value_metric,category
TOPTEN,기본 자켓,49000,KRW,https://shop.example.com/p/1,2026-06-10,per_unit,자켓
HAZZYS,코튼 자켓,128000,KRW,https://shop.example.com/p/2,2026-06-11,per_unit,자켓
COS,울 자켓,295000,KRW,https://shop.example.com/p/3,2026-06-12,per_unit,자켓
```

## JSON 예시

```json
[
  {"brand": "TOPTEN", "item": "기본 자켓", "price": 49000, "currency": "KRW",
   "source_url": "https://shop.example.com/p/1", "observed_at": "2026-06-10",
   "value_metric": "per_unit", "category": "자켓"}
]
```

JSON은 위처럼 객체 배열이거나, `{"observations": [ ... ]}` 형태여도 된다.

## 도구 무관 수집 계약 (여러 일꾼에게 나눠 맡길 때 그대로 복사)

> 아래 가격대 구간을 맡아, 대표 브랜드와 대표 품목의 **실판매가**를 모아주세요. 결과는 한 품목당 한 줄로, 다음 항목을 반드시 포함하세요. 브랜드명, 품목명, 가격(숫자만), 통화 코드, 출처 주소, 관측일(YYYY-MM-DD). 가격을 본 출처가 없으면 그 줄은 빼주세요. 정리는 한국어로 해주세요.

이 계약은 수집 수단(웹 수집 MCP·검색 API·사내 데이터·수기)을 가리지 않는다. 각 일꾼이 같은 컬럼으로 돌려주면, 그 결과를 이어 붙여 하나의 관측 파일로 만든 뒤 분석기에 넣는다.
