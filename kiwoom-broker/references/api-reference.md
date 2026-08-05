# 키움 REST API — 검증된 TR 레퍼런스

> 이 문서는 **직접 호출해 확인한 것**만 담는다(2026-08-05, 모의 서버).
> 전체 API 목록은 키움 공식 포털·저장소를 참조한다. 여기 없는 TR은 미검증이다.

## 공통 규칙

키움은 **경로가 아니라 `api-id` 헤더로 TR을 구분**한다. 같은 URL에 다른 TR을 보낸다.

| 요소 | 값 |
| --- | --- |
| 메서드 | 전부 `POST` |
| 인증 헤더 | `authorization: Bearer <token>` |
| TR 지정 | `api-id: <TR ID>` |
| Content-Type | `application/json;charset=UTF-8` |
| 연속조회 요청 | `cont-yn: Y` + `next-key: <값>` |
| 연속조회 응답 | 헤더 `cont-yn` · `next-key` |

**오류 표현이 특이하다.** HTTP 200으로 내려오면서 본문 `return_code`가 실패를 나타낸다. 둘 다 검사해야 한다.

```json
{"return_code": 0, "return_msg": "정상적으로 처리되었습니다"}
```

## 인증

### POST /oauth2/token

```json
{"grant_type":"client_credentials","appkey":"…","secretkey":"…"}
```

응답 — `token`(약 86자), `token_type: Bearer`, `expires_dt`(**`YYYYMMDDHHMMSS` 문자열**, 초 단위 숫자가 아님), `return_code`.

- 유효기간 실측 **24시간**
- 토큰 발급 자체에 호출 제한이 있으므로 캐시해서 재사용한다
- 모의와 실전은 **키도 서버도 다르다**

## 시세·종목 정보

### ka40002 — ETF 종목 정보 · `/api/dostk/etf`

```json
{"stk_cd":"069500"}
```

응답 — `stk_nm`(종목명) · `etfobjt_idex_nm`(추종지수명) · `wonju_pric`(원주가격) · `etftxon_type`(과세유형).

실측 예: `{"stk_nm":"KODEX 200","etfobjt_idex_nm":"KOSPI200","wonju_pric":"10","etftxon_type":"비과세"}`

> ⚠️ **없는 종목코드도 `return_code: 0`으로 온다.** 모든 필드가 빈 문자열이 될 뿐이다.
> 조회가 성공했다고 그 종목이 존재하는 것이 아니다. **`stk_nm`이 비었는지로 판별**한다.

ETF 전용 TR은 이 밖에도 NAV·수익률·일별추이 등 여러 개가 있다(미검증).

### ka10081 — 주식 일봉차트 · `/api/dostk/chart`

```json
{"stk_cd":"069500","base_dt":"20260805","upd_stkpc_tp":"1"}
```

| 파라미터 | 의미 |
| --- | --- |
| `stk_cd` | 종목코드 6자리 |
| `base_dt` | 기준일자 `YYYYMMDD` — 이 날짜부터 과거로 |
| `upd_stkpc_tp` | 수정주가 구분. `1` = 적용 |

응답 배열 키는 **`stk_dt_pole_chart_qry`**. 각 원소의 필드:

| 필드 | 의미 |
| --- | --- |
| `dt` | 일자 `YYYYMMDD` |
| `open_pric` · `high_pric` · `low_pric` | 시가 · 고가 · 저가 |
| **`cur_prc`** | **종가** (`close_pric` 아님 — 이름이 "현재가"다) |
| `trde_qty` · `trde_prica` | 거래량 · 거래대금 |
| `pred_pre` · `pred_pre_sig` | 전일대비 · 대비부호 |
| `trde_tern_rt` | 거래회전율 |

**실측 — 1회 호출에 600봉**(2024-02-16 ~ 2026-08-05, 약 2년 5개월). `cont-yn: Y`와 `next-key`로 더 당길 수 있다.

> ⚠️ 종가 필드명이 `cur_prc`다. 적재 스키마에 매핑할 때 가장 틀리기 쉬운 자리.
> ⚠️ `upd_stkpc_tp`를 프로젝트 안에서 통일해야 한다. 수정주가 적용분과 미적용분이 섞이면 평단이 어긋난다.

## 계좌

### kt00018 — 계좌평가잔고 · `/api/dostk/acnt`

```json
{"qry_tp":"1","dmst_stex_tp":"KRX"}
```

응답 — 요약 필드(`tot_pur_amt` 총매입 · `tot_evlt_amt` 총평가 · `tot_evlt_pl` 평가손익 · `tot_prft_rt` 수익률 · `prsm_dpst_aset_amt` 추정예탁자산)와 종목 배열 `acnt_evlt_remn_indv_tot`.

종목 원소 — `stk_cd` · `stk_nm` · `pur_pric`(매입가) · `evltv_prft`(평가손익) · `prft_rt`(수익률) · `pred_close_pric`(전일종가) 등.

> 보유 종목이 없으면 `return_msg`가 **"모의투자 해당조회내역이 없습니다"**로 온다. **오류가 아니다** — `return_code`는 0이고 배열이 비어 있을 뿐이다.

## 주문

### kt10000 — 주식 매수 · `/api/dostk/ordr`

```json
{"dmst_stex_tp":"KRX","stk_cd":"069500","ord_qty":"1","ord_uv":"","trde_tp":"3"}
```

| 파라미터 | 의미 |
| --- | --- |
| `dmst_stex_tp` | 거래소 구분 — `KRX` · `NXT` · `SOR` |
| `stk_cd` | 종목코드 |
| `ord_qty` | 주문수량 (**문자열**, 단위 1주) |
| `ord_uv` | 주문단가 (시장가면 빈 문자열) |
| `trde_tp` | 매매구분 (아래) |

**매매구분(`trde_tp`) 주요 코드** — `0` 보통 · **`3` 시장가** · `5` 조건부지정가 · `6` 최유리지정가 · `7` 최우선지정가 · `61` 장시작전시간외 · `62` 시간외단일가 · `81` 장마감후시간외 · `10/13/16` IOC 계열 · `20/23/26` FOK 계열.

같은 계열 — `kt10001`(매도) · `kt10002`(정정) · `kt10003`(취소).

**실측 (2026-08-05 17:10, 정규장 마감 후)**

```text
HTTP 200
{"return_msg":"[2000](RC4058:모의투자 장종료)","return_code":20}
```

경로·TR·파라미터는 맞고 **장 상태 때문에 거부**됐다. 즉 장중이었으면 접수됐을 요청이다.

> 🎯 **HTTP는 200인데 실패다.** 200만 보고 성공 처리하면 아무것도 안 샀는데 성공으로 기록된다.
> 장 개장 여부는 **주문을 보내기 전에** `market-calendar` 계열로 확인하는 게 맞다. 쏘고 나서 거부로 아는 건 늦다.

> ⏳ **체결·잔고 반영은 미검증.** 정규장(09:00~15:30) 주문으로 주문번호·체결·취소 절차를 확인해야 한다.

## Rate Limit

공식 기준은 주문·조회 각 초당 5건이지만, **실측에서 조회를 연달아 두 번 보내자 429가 떴다.** 보수적으로 **TR당 초당 1건**을 권장한다.

래퍼는 429에 지수 백오프(1s → 2s → 4s)로 최대 3회 재시도한다.

## 알려진 오류 코드

| 코드 | 의미 | 대응 |
| --- | --- | --- |
| `8001` | App Key/Secret 검증 실패 | 키 만료·해지. 포털에서 재발급 |
| `8002` | 인증 관련 (추정) | 토큰 재발급 |
| `20` (`RC4058`) | 모의투자 장종료 | 장 시간 확인. 주문 전에 캘린더로 거를 것 |
| HTTP 429 | 호출 한도 초과 | 백오프 후 재시도 |

## 미검증 영역

- WebSocket 실시간 시세 (공식적으로 제공되나 이 스킬은 REST만)
- 조건검색
- 미국 주식 TR
- 주문 **체결** 경로 (도달은 확인, 체결·취소는 미확인)
