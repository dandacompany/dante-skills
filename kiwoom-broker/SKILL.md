---
name: kiwoom-broker
description: 키움증권 공식 `kwcli`/`kiwoomcli`를 사용해 국내 ETF·주식 시세, 일봉, 보유종목을 조회하고 주문을 안전하게 미리보기·집행하는 운영 스킬. 키움 모의투자 조회, 계좌 확인, 주문 초안, 주문 승인 후 집행, `kiwoomcli doctor` 진단 요청에 사용한다. 직접 REST 호출이나 자체 토큰 발급 코드를 만들지 않는다.
---

# Kiwoom Broker

키움증권 공식 CLI를 증권사 어댑터로 사용한다. 인증·토큰·API 필드 매핑은 CLI에 맡기고, 이 스킬은 명령 선택과 안전 경계를 담당한다.

## 실행 전 점검

1. `command -v kiwoomcli`로 실행 파일을 찾는다.
2. 없으면 `$HOME/.local/bin/kiwoomcli`를 확인한다.
3. 둘 다 없으면 실행하지 말고 다음 설치 명령을 안내한다.

   ```bash
   uv tool install kwcli
   uv tool update-shell
   ```

4. `kiwoomcli doctor`를 실행한다. 진단이 `지금 호출 가능: 예`가 아니면 조회나 주문으로 넘어가지 않는다.
5. 강의 실습에서는 `demo`만 사용한다. `real` 전환은 사용자가 실계좌 사용을 명시적으로 요청하고 별도 운영 승인을 제공한 경우에만 검토한다.

자격증명, 접근토큰, 계좌번호 원문을 출력하거나 로그에 남기지 않는다. 토큰 발급 엔드포인트를 직접 호출하지 않는다.

## 조회

항상 구조화된 출력을 요청하고, 원문 전체를 그대로 재출력하지 말고 요청에 필요한 필드만 요약한다.

```bash
kiwoomcli domestic etfs info --code 069500 --mode demo --format json
kiwoomcli domestic candles daily --code 069500 --date YYYYMMDD --mode demo --format json
kiwoomcli domestic accounts holdings --basis total --exchange KRX --mode demo --format json
```

명령이나 옵션을 확신할 수 없으면 추정하지 말고 먼저 찾는다.

```bash
kiwoomcli spec search "검색어"
kiwoomcli domestic etfs info -h
```

`return_code`가 0인지 확인한다. 성공 코드가 아니거나 응답이 비어 있으면 값을 지어내지 말고 차단 원인과 다음 확인 명령을 보고한다.

## 주문

주문은 다음 두 단계로 분리한다.

### 1. 미전송 미리보기

사용자가 매수·매도를 요청해도 처음에는 `--confirm`을 붙이지 않는다.

```bash
kiwoomcli domestic orders buy \
  --code 069500 \
  --qty 1 \
  --price 90000 \
  --order-type limit \
  --mode demo \
  --format json
```

CLI가 `주문은 아직 전송되지 않았습니다`라고 확인한 경우에만 주문 초안으로 취급한다. 종목, 수량, 가격, 주문 유형, 모드를 사용자에게 다시 보여주고 승인을 요청한다.

### 2. 승인 후 집행

다음 조건을 모두 충족한 경우에만 같은 명령에 `--confirm`을 추가한다.

- 사용자가 방금 제시한 주문 초안을 명시적으로 승인했다.
- 승인 대상의 종목·수량·가격·주문 유형·모드가 미리보기와 동일하다.
- 상위 하네스가 요구하는 `OrderIntent`와 `ApprovalRecord`가 존재한다.
- 모드는 `demo`다. 실계좌는 이 스킬의 강의 기본 범위가 아니다.

하나라도 다르면 집행하지 않는다. 승인 뒤 입력이 달라졌다면 새 미리보기를 만들고 다시 승인받는다.

## 금지 사항

- `curl`이나 자체 Python으로 키움 REST API를 직접 호출하지 않는다.
- 자체 토큰 캐시나 토큰 발급 명령을 만들지 않는다.
- 사용자의 명시적 승인 없이 `--confirm`을 붙이지 않는다.
- 실패 응답을 성공처럼 요약하지 않는다.
- CLI의 기본 안전장치를 우회하지 않는다.

`kiwoomcli`는 브로커 호출 도구다. 전략 판단, 주문 의도 생성, 승인 기록, 중복 방지, 체결 대사는 `magma-finance-lab` 하네스가 담당한다.
