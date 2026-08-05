---
name: kiwoom-broker
description: 키움증권 REST API 연동 스킬. 모의투자(mockapi)를 기본으로 국내 주식·ETF의 시세와 일봉 차트, 계좌 평가잔고를 조회하고, 주문 계열은 명시적 확인 플래그가 있어야만 실행되는 안전 래퍼를 제공한다. 자격증명은 Hermes 프로필 .env 나 Bitwarden·1Password 같은 SecretSource 로 주입된 환경변수를 그대로 쓰고, 토큰은 출처별 캐시로 재사용한다. 트리거 - "키움", "키움증권", "kiwoom", "모의투자 시세", "모의투자 잔고", "국내 주식 일봉" 등 키움 REST API 관련 요청 시 사용.
---

# 키움증권 REST API (kiwoom-broker)

키움 REST API로 국내 주식·ETF 시세와 계좌를 조회하는 스킬. **모의투자가 기본값**이고 실전은 명시적으로 열어야 한다.

- 모의 서버 — `https://mockapi.kiwoom.com`
- 실전 서버 — `https://api.kiwoom.com`
- 인증 — Client Credentials. 자격증명은 **환경변수**로 받는다 (아래 「자격증명 넣는 법」)
- 공식 문서 — https://openapi.kiwoom.com · 공식 저장소 https://github.com/Kiwoom-Securities/Kiwoom-REST-API

## ⚠️ 핵심 주의사항

1. **기본 프로필은 mock 이다.** 실전은 `-p real` 을 명시해야만 열린다. 프로필과 서버 주소가 어긋나면 스크립트가 중단한다.
2. **주문 계열(`kt10000`~`kt10003`)은 그냥 실행되지 않는다.** `--confirm-order` 를 붙여야 하고, 실전이면 경고를 출력한다. 주문은 되돌릴 수 없다.
3. **HTTP 200 이어도 실패일 수 있다.** 키움은 본문 `return_code` 로 오류를 표현한다. 래퍼가 둘 다 검사하지만, 응답을 직접 다룰 때도 `return_code` 를 봐야 한다.
4. **없는 종목도 정상 응답으로 온다.** 존재하지 않는 종목코드를 조회하면 `return_code: 0` 에 필드가 빈 문자열로 채워져 돌아온다. 조회에 성공했다고 그 종목이 있는 것이 아니다.
5. 앱키·시크릿·토큰·계좌번호를 출력하거나 로그에 남기지 않는다.

## 기본 사용법

```bash
SKILL=~/.claude/skills/kiwoom-broker/scripts

# 토큰 상태 (토큰 값은 안 보인다)
$SKILL/kiwoom_token.sh --status
$SKILL/kiwoom_token.sh -p real --status

# ETF 종목 정보
$SKILL/kiwoom_api.sh ka40002 /api/dostk/etf '{"stk_cd":"069500"}'

# 주식 일봉 차트 — 1회에 600봉까지 온다
$SKILL/kiwoom_api.sh ka10081 /api/dostk/chart \
  '{"stk_cd":"069500","base_dt":"20260805","upd_stkpc_tp":"1"}'

# 계좌 평가잔고 (모의)
$SKILL/kiwoom_api.sh kt00018 /api/dostk/acnt '{"qry_tp":"1","dmst_stex_tp":"KRX"}'
```

`upd_stkpc_tp` 는 수정주가 구분이다(`1` = 적용). **한 프로젝트 안에서 이 값을 섞으면 평단 계산이 어긋난다.**

## 연속조회

응답 헤더에 `cont-yn: Y` 와 `next-key` 가 오면 이어받을 데이터가 있다. 래퍼가 stderr 로 알려준다.

```bash
$SKILL/kiwoom_api.sh -k "$NEXT_KEY" ka10081 /api/dostk/chart '{"stk_cd":"069500",...}'
```

## 주문 (실행 전에 반드시 읽을 것)

```bash
# 이렇게 하면 거부된다 — 무엇을 주문하려는지 보여주고 멈춘다
$SKILL/kiwoom_api.sh kt10000 /api/dostk/ordr '{"dmst_stex_tp":"KRX","stk_cd":"069500","ord_qty":"1","ord_uv":"","trde_tp":"3"}'

# 확인한 뒤에만
$SKILL/kiwoom_api.sh --confirm-order kt10000 /api/dostk/ordr '{...}'
```

- 수량·단가는 **문자열**로 보낸다 (`"1"`, 숫자 1 아님)
- `dmst_stex_tp` 는 거래소 구분 — `KRX` · `NXT` · `SOR`
- **주문 응답을 못 받았다고 재주문하지 않는다.** 주문 조회로 이미 나갔는지부터 확인한다

## 키를 한 프로필에만 두기

여러 에이전트가 같은 저장소에서 일할 때, **키를 가진 쪽을 하나로 좁히는 것**이 가장 단순한 사고 예방이다.
`KIWOOM_AUTH_ENV` 로 자격증명 파일 경로를 프로필마다 다르게 준다.

```bash
# 집행 담당만 키를 갖는다
KIWOOM_AUTH_ENV=~/.hermes/profiles/sam/kiwoom-mock.env   $SKILL/kiwoom_api.sh kt00018 /api/dostk/acnt '{"qry_tp":"1","dmst_stex_tp":"KRX"}'

# 판단 담당에게는 그 파일이 없다 → 여기서 멈춘다
KIWOOM_AUTH_ENV=~/.hermes/profiles/ada/kiwoom-mock.env $SKILL/kiwoom_api.sh ...
# ERROR: 자격증명 파일 없음: /Users/…/ada/kiwoom-mock.env
```

파일이 없으면 **호출 자체가 시작되지 않는다.** 권한을 안 준 일은 실수로도 못 하게 된다.
토큰 캐시도 자격증명 파일 경로별로 갈라지므로 프로필끼리 토큰을 공유하지 않는다.

## 안전 경계 — 에이전트에게 맡길 때

이 스킬은 조회를 편하게 해주지만 **주문 안전은 스킬 바깥에서 설계해야 한다.**

- 판단하는 프로필과 주문을 집행하는 프로필을 나눈다. **키는 집행 프로필의 `.env` 에만** 넣는다(위 절)
- 주문 직전에 사람이 승인한다. 승인은 그 주문 내용에 한정된 1회용이다
- 1회·1일 한도, 종목 허용 목록, 허용 시간을 코드로 강제한다
- 결과는 응답 한 번으로 확정하지 말고 주문 조회로 대사한다

자세한 내용은 `references/safety.md`.

## 상세 레퍼런스

- `references/api-reference.md` — 검증된 TR 목록, 파라미터, 응답 필드, 실측 함정
- `references/safety.md` — 주문 안전 게이트, 상태 머신, 승인 화면 항목

## 트러블슈팅

- `8001 App Key와 Secret Key 검증에 실패했습니다` — 키가 만료·해지됐다. 키움은 일정 기간 미사용 시 자동 해지하므로 포털에서 재발급한다. 모의는 상시모의투자 참가신청도 함께 확인한다.
- `프로필과 서버가 어긋난다` — `KIWOOM_API_BASE_URL` 이 프로필과 맞지 않다. mock 은 `mockapi.kiwoom.com`, real 은 `api.kiwoom.com`.
- `키움 자격증명을 찾지 못했습니다` — 위 네 곳 어디에도 키가 없다. 프로필 `.env` 에 넣는 것이 가장 확실하다. **다른 프로필에서는 일부러 안 보이게 한 것일 수도 있다**(키를 가진 프로필을 좁히는 설계).
- 429 — 래퍼가 지수 백오프로 재시도한다. 반복되면 호출 간격을 늘린다. 조회는 TR당 초당 1건 수준이 안전하다.
- 조회는 되는데 필드가 전부 빈 문자열 — 종목코드를 확인한다. 없는 종목도 정상 응답으로 온다(주의사항 4).
- `모의투자 해당조회내역이 없습니다` — 오류가 아니다. 보유 종목이 0이라는 뜻이고 `return_code` 는 0이다.

## 이 스킬과 공식 저장소의 관계

키움 공식 저장소(`Kiwoom-Securities/Kiwoom-REST-API`)는 Python 런타임과 예제를 제공하지만 **라이선스가 `All rights reserved`** 라 복제·재배포·2차 저작물에 제약이 있다.

이 스킬은 공식 코드를 포함하지 않는다. 공개된 API 사양(엔드포인트·TR 식별자·파라미터명)만 참조해 **HTTP 호출을 직접 구성한 자체 구현**이다. 공식 Python 런타임이나 CLI(`kwcli`)가 필요하면 키움 배포처에서 별도로 설치한다.
