# 플랫폼별 리뷰 API (실측 정본)

수집기를 고치거나 새 플랫폼을 붙일 때 이 표부터 갱신한다. "검증"은 실제 상품에서 화면 건수와 수집 건수가 맞은 날짜다.
모든 호출은 **상품 페이지를 연 bsk 탭 안에서 같은 출처 fetch** 로 한다(쿠키·봇 쿠키가 자연히 붙는다). 탭 밖 curl 은 막힌다.

| 플랫폼 | 수집기 | 리뷰 목록 요청 | 형식 | 필요한 값과 얻는 곳 | 검증 |
|---|---|---|---|---|---|
| 쿠팡 | `coupang.js` | `GET /next-api/review?productId=&page=&size=10&sortBy=DATE_DESC&ratingSummary=true` | JSON `rData.paging.{totalCount,contents[]}` | productId = URL `/vp/products/{id}` | 2026-10-21 83/83 (로그인·비로그인 동일) |
| 네이버 브랜드스토어 | `naver.js` | `POST /n/v1/contents/reviews/query-pages` `{checkoutMerchantNo,originProductNo,page,pageSize,reviewSearchSortType}` | JSON `{contents[],totalElements}` | 둘 다 페이지가 부르는 `…/reviews/product-summary/{originProductNo}?…checkoutMerchantNo=` URL | 2026-10-21 19/19 |
| 네이버 스마트스토어 | `naver.js` | 위와 같은 형태로 추정(경로 접두 `/i/` 가능) | — | — | **미검증** — 로그아웃 브라우저는 로그인으로 넘어감(LOGIN_REQUIRED) |
| 11번가 | `11st.js` | `GET /products/{id}/review-list?pageSize=&pageNo=&sortType=01&marketType=RETAIL…` | HTML `li.review_list_element` | iframe(review-frame) 이 실제로 부른 URL 의 쿼리. 경로는 정확히 `^/products/\d+/review-list$` | 2026-10-22 4/4 |
| 롯데하이마트 | `himart.js` | `POST /app/goods/reviewAllListAjax` `goodsNo=&goodsCmpsCd=01&orderType=02&page=&goodsStatSctCd=01` | HTML `li.hm-list__item` | goodsNo = URL 쿼리. 건수 = `#gdasCnt` | 2026-10-22 6/6 |
| SSG.COM | `ssg.js` | `GET /item/ajaxItemCommentList.ssg?itemId=&siteNo=&filterCol=10&page=&pageSize=10…` | HTML `div.rvw_expansion_panel[data-postngid]` | itemId·siteNo = URL 쿼리. 건수 = 화면 "고객리뷰 (N 건)" | 2026-10-22 199/199 (에어팟) |
| 롯데ON | `lotteon.js` | `POST https://pbf.lotteon.com/review/v1/productDetail/getProductReviewSearchList` `{sitmNoList,pageNo,rowsPerPage,…}` | JSON `data.reviewList.{totalCount,dataList[]}` | sitmNo = 페이지 HTML 의 `LO{상품}_{단품}` | 2026-10-22 71/71 (에어팟) |
| G마켓 | `gmarket.js` | `POST /Review`(첫 화면) · `/Review/Text`(일반) · `/Review/Premium`(포토) `goodsCode=&pageNo=&sellerCustNo=` | HTML `table tbody tr` | goodsCode = URL, sellerCustNo = 페이지 HTML | **부분** — 일반 1/1, 페이지 파라미터는 클릭으로 확인. 대량 수집 중 `Failed to fetch` 차단 |
| 옥션 | 없음 | — (G마켓 계열이라 비슷할 것으로 추정) | — | — | 미검증 — 대상 상품 리뷰 0건이었음 |
| GS SHOP · CJ온스타일 | 없음 | — | — | — | 맥미니 M6 미판매로 조사 못 함 |

## 플랫폼별 함정 (실측)

- **쿠팡** — 같은 브라우저로 하루 여러 번 열면 페이지 전체가 "요청하신 페이지의 사용권한이 없습니다"로 막힌다(제목은 "쿠팡!").
  API 도 403. 구조 문제가 아니다. 시간을 두거나 다른 브라우저 프로필을 쓴다. 리뷰 83개 중 75개가 본문 없는 별점이다.
  같은 상품 ID 에 다른 모델(M5 Pro) 리뷰가 섞인다 — `option` 열로 거른다.
  2026-10-22 Cloudflare WARP(한국 출구) 로 열자 첫 페이지부터 "Sorry! Access denied" — VPN·공용 IP 는 오히려 막힌다.
  그래서 실행기는 쿠팡 페이지 간격을 최소 3초로, 같은 브라우저 재방문을 30분 뒤로 묶는다(COOLDOWN).
- **네이버** — 리뷰 목록은 리뷰 영역이 화면에 들어와야 부른다(스크롤 필요). 요청에 `x-client-rtk`/`x-client-rts` 헤더가 붙지만
  없어도 같은 탭 fetch 는 응답한다. **토큰을 꺼내 쓰지 않는다.** `originProductNo` 는 화면 상품번호와 다르다.
  검색 결과의 `smartstore.naver.com/main/products/…` 링크는 상점 ID 가 없는 내부 링크다.
- **11번가** — 리뷰가 iframe 안에서 오므로 `bsk debug` 메인 프레임 캡처에 안 잡힌다. iframe `performance` 로 찾는다.
  `/products/v1/pc/reviews/same-kind/products/{id}/review-list` 는 "비슷한 상품" 리뷰라 다른 엔드포인트다 — 부분 일치로 잡지 않는다.
  본문 없이 설문(사용성·성능·내구성)만 있는 리뷰가 있다.
- **하이마트** — `reviewListInitAjax?page=N` 은 첫 화면용(3개)이라 페이지가 넘지 않는다. "상품평 전체보기"가 부르는 `reviewAllListAjax` 를 쓴다.
- **SSG** — 연속 요청 중 빈 응답이 섞인다(7페이지 무렵부터). 4초 뒤 다시 부르면 정상 — `paginate` 재시도가 처리한다.
  조각 안 JSON-LD 는 본문 제어문자 때문에 `JSON.parse` 가 깨진다.
- **롯데ON** — 다른 출처(`pbf.lotteon.com`) 지만 페이지와 같이 `credentials: 'include'` 로 부르면 된다. `trNo` 는 비워도 된다.
  응답의 `mbNo`(회원번호)는 옮기지 않는다. 작성자 표시명 필드는 비어 있다.
- **G마켓** — 리뷰 수백 건을 1초 간격 안팎으로 넘기다 리뷰 엔드포인트만 `Failed to fetch` 로 막혔다(페이지는 열림). 기본 간격 2초.
