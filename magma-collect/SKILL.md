---
name: magma-collect
description: "MAGMA 가상 오피스 강의(섹션 7)용 커머스 웹 데이터 수집·적재 스킬. 무신사·네이버 가격비교·쿠팡에서 남성 패션 키워드의 상품 목록(상품명·브랜드·가격·할인율·평점·리뷰 수 등)을 Bright Data 도구로 수집해 정규 CSV 스키마로 변환하고, 검증 스크립트 통과 후 사용자의 컨펌을 받아 Supabase에 적재한다. 소스별로 얻을 수 있는 필드가 다르다는 점(쿠팡은 평점 없음)을 nullable로 다룬다. Use when: '무신사에서 셔츠 데이터 수집해', '커머스 데이터 긁어서 DB에 넣어', 'magma-collect 실행', '시장 데이터 수집·적재', or the Section 7.2 collection exercise."
user-invocable: true
license: MIT
compatibility: "Bright Data 도구(MCP 또는 플러그인)와 Supabase 접근(MCP execute_sql 또는 CLI)이 연결된 에이전트 환경."
metadata:
  author: dante
  version: "1.0.0"
---

# magma-collect — 커머스 수집·적재 파이프라인

## 목적

남성 패션 시장 데이터(리얼 축)를 세 소스에서 수집해 하나의 정규 스키마로 적재한다.
소스마다 주는 필드가 다르다 — 그 차이를 감추지 않고 nullable로 기록하는 것이 이 스킬의 설계 철학이다.

## 수집 윤리 (필수 준수)

- 공개 화면의 **집계 수치**(가격·할인율·리뷰 수·평점·랭킹)만 수집한다.
- **리뷰 본문, 작성자명 등 저작물·개인정보성 데이터는 수집하지 않는다.**
- 키워드당 1~2페이지, 소스당 상위 50개 이내로 제한한다. 반복 대량 요청을 하지 않는다.
- 교육 목적 수집임을 전제로 하며, 수집 결과를 상업적으로 재배포하지 않는다.

## 절차

1. **수집 대상 확인**: 사용자에게 키워드(예: 남성셔츠)와 소스(기본: 무신사+네이버+쿠팡)를 확인받는다.
2. **수집**: `references/site-field-map.md`의 소스별 URL 패턴과 필드 추출 규칙을 따라
   Bright Data 도구(`scrape_as_markdown` 계열)로 목록 페이지를 가져와 필드를 추출한다.
   - 11번가·29cm은 전면 JS 렌더라 이 방식으로 수집되지 않는다(실측 2026-07-26). 시도하지 않는다.
   - 광고 상품은 `is_ad=true`로 표시해 포함한다(제외하지 않는다 — 정제 단계의 재료).
3. **CSV 생성**: 정규 스키마(아래) 순서 그대로 `collected_products.csv`를 만든다.
   소스에 없는 필드는 빈 값으로 둔다(예: 쿠팡의 rating).
4. **검증**: `python3 scripts/validate_csv.py collected_products.csv` 를 실행해
   컬럼·타입·범위 검사를 통과시킨다. 실패 행은 고치거나 사유와 함께 제외 보고한다.
5. **컨펌 게이트**: 소스별 수집 건수·샘플 5행·검증 결과를 사용자에게 보여주고
   **적재 승인을 받는다. 승인 전에 데이터베이스에 쓰지 않는다.**
6. **적재**: `references/schema.sql`의 `collected_products` 테이블에 insert 하고,
   적재 후 소스별 count를 조회해 CSV와 대조 보고한다.

## 정규 CSV 스키마 (컬럼 순서 고정)

| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| source | text | musinsa · naver · coupang |
| keyword | text | 수집 키워드 |
| rank | int | 목록 내 순번 (광고 포함 화면 순서) |
| brand | text | 브랜드명 (네이버·쿠팡은 빈 값 가능) |
| name | text | 상품명 |
| price | int | 판매가 (원) |
| discount_rate | int | 할인율 % (없으면 빈 값) |
| rating | numeric | 평점 (쿠팡은 빈 값 — 목록에 없음) |
| review_count | int | 리뷰 수 |
| purchase_count | int | 구매 수 (네이버만) |
| is_ad | bool | 광고 상품 여부 |
| product_url | text | 상품 URL (쿼리 파라미터 제거) |
| collected_at | timestamptz | 수집 시각 (ISO 8601) |

## 규칙

- 스키마 컬럼을 임의로 추가·개명하지 않는다(강의 화면과 어긋난다). 확장이 필요하면 사용자에게 먼저 묻는다.
- 수집 실패(차단·구조 변경) 시 실패 소스를 정직하게 보고하고, 성공한 소스만으로 진행할지 확인받는다.
- 원본 마크다운 응답은 임시 파일로만 두고 저장소·DB에 넣지 않는다.
