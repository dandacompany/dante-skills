# 소스별 URL 패턴·필드 추출 규칙 (실측 2026-07-26·27 기준)

> Bright Data `scrape_as_markdown` 응답(마크다운)에서 필드를 뽑는 규칙.
> 사이트 개편으로 패턴이 어긋나면 이 문서를 갱신하고, 어긋난 사실을 사용자에게 보고한다.

## 무신사 (musinsa) — 필드 최다, 주력 소스

- URL: `https://www.musinsa.com/search/goods?keyword=(키워드)&gf=M`
  - `gf=M` = 남성 필터. 반드시 유지.
- 상품 블록 패턴: 상품 링크 `https://www.musinsa.com/products/(id)` 기준으로 구획.
- 필드:
  - brand: 상품 블록 안의 브랜드 링크 텍스트 (`/brand/(slug)` 링크의 라벨)
  - name: 상품 링크의 라벨 텍스트
  - discount_rate + price: `35%51,350원` 형태로 붙어 나옴 — `(\d+)%([\d,]+)원` 분리. 할인 없으면 가격만
  - rating + review_count: `4.9(46)` 형태 — `(\d\.\d)\((\d[\d,]*)\)`
  - is_ad: 무신사 목록은 광고 라벨이 드묾 — 배지(단독·아울렛 등)는 광고 아님. 광고 표기 발견 시만 true
  - 총 상품 수: 상단 `새 상품 31,693` 등 — 로그용(수집 대상 아님)

## 네이버 가격비교 (naver) — 평점·리뷰수·구매수 동시 제공

- URL: `https://search.shopping.naver.com/search/all?query=(키워드 URL인코딩)`
- 필드:
  - name: 상품 링크 라벨
  - price: `18,900원` / `정상가37,000원...할인율48%...18,900원` — 마지막 판매가 채택
  - discount_rate: `할인율48%` 패턴
  - rating: `리뷰4.8` 또는 `별점4.72` 패턴
  - review_count: `리뷰4.8_673_` / `리뷰_(2,795)_` — 괄호·언더스코어 안 숫자. `1.7만` 같은 축약은 17000으로 환산
  - purchase_count: `구매_1,657_` / `구매 360+` — `+`는 제거하고 숫자만
  - brand/판매처: 스토어명 링크(smartstore) 라벨 — brand 컬럼에 넣되 "판매처명"임을 유의
  - is_ad: 링크가 `ader.naver.com` 경유면 true
- 주의: 링크 URL이 매우 긴 리다이렉트 — product_url은 `nvMid=(\d+)` 값으로 `https://search.shopping.naver.com/catalog/(nvMid)` 재구성, 불가하면 빈 값

## 쿠팡 (coupang) — 평점 없음(rating은 항상 빈 값)

- URL: `https://www.coupang.com/np/search?q=(키워드 URL인코딩)`
- 상품 블록: `/vp/products/(id)` 링크 기준 구획
- 필드:
  - name: 상품 링크 라벨
  - price: 판매가 — `31,500원` (정가·할인율 뒤 마지막 금액)
  - discount_rate: `30%` 단독 라인
  - review_count: `(1,495)` 괄호 숫자
  - rating: **목록·상세 모두 마크다운에 안 잡힘 — 항상 빈 값** (실측 확정)
  - rank: URL 파라미터 `searchRank=(\d+)` 우선, 없으면 화면 순서
  - is_ad: URL에 `sourceType=srp_product_ads` 또는 블록에 `광고` 라벨이면 true
  - product_url: `https://www.coupang.com/vp/products/(id)` 로 정규화(쿼리 제거)

## 수집 불가 소스 (시도 금지 · 실측 2026-07-26)

- 11번가: PC·모바일 모두 전면 JS 렌더 — 본문 없이 반환
- 29cm: SPA — 404 셸 또는 타이틀 파편만 반환
