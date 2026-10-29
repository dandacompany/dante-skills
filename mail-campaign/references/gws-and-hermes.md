# gws 실행기와 인증

## 실행기 선택(스크립트가 자동으로 고른다)

1. 환경변수 `MAIL_CAMPAIGN_GWS` 가 있으면 그 명령(예: `python3 /path/gws_bridge.py`)
2. `${HERMES_HOME:-~/.hermes}/google_token.json` 이 있고 google-workspace 스킬의 `scripts/gws_bridge.py` 가 있으면 → `python3 gws_bridge.py …`
   (브리지가 Hermes 토큰을 갱신해 `GOOGLE_WORKSPACE_CLI_TOKEN` 으로 gws 를 실행한다. 추가 키 0개)
3. PATH 의 `gws`(Claude Code 등. 사용자가 `gws auth login` 을 마친 상태)

`doctor` 가 어느 실행기를 골랐는지와 보내는 계정 주소를 보여 준다. 브리지도 내부에서 `gws` 를 실행하므로 어느 경우든 `npm i -g @googleworkspace/cli` 가 필요하다.

Hermes 프로필을 쓰면 `HERMES_HOME` 이 그 프로필 폴더를 가리키므로 프로필마다 연결된 Google 계정으로 보낸다.

## Hermes google-workspace OAuth 범위

google-workspace 스킬의 `setup.py` 는 `gmail.readonly`, `gmail.send`, `gmail.modify`, `spreadsheets` 를 포함한 8개 범위를 요청한다. 이 스킬에 필요한 것:

| 동작 | 범위 |
|---|---|
| 시트 읽기·쓰기 | spreadsheets |
| 발송(`+send`, `drafts.send`) | gmail.send / gmail.modify |
| 초안 만들기·지우기 | gmail.modify(또는 gmail.compose) |
| 답장 수거(`threads.get`, `messages.list`) | gmail.readonly / gmail.modify |

연결할 때 서비스를 일부만 고르면 초안·시트 쓰기가 403 으로 실패한다. 그때는 google-workspace 스킬로 다시 연결한다.

## 이 스킬이 쓰는 gws 명령

```bash
gws gmail users getProfile --params '{"userId":"me"}'
gws sheets spreadsheets get --params '{"spreadsheetId":"ID","fields":"sheets.properties.title"}'
gws sheets +read --spreadsheet ID --range "'탭'"
gws sheets spreadsheets values batchUpdate --params '{"spreadsheetId":"ID"}' --json '{"valueInputOption":"RAW","data":[…]}'
gws gmail +send --to 주소 --subject 제목 --body 본문 [--html] [--from 별칭] [--draft]
gws gmail users drafts send --params '{"userId":"me"}' --json '{"id":"초안ID"}'
gws gmail users drafts delete --params '{"userId":"me","id":"초안ID"}'
gws gmail users messages list --params '{"userId":"me","q":"in:sent to:주소 subject:\"…\" newer_than:1d"}'
gws gmail users threads get --params '{"userId":"me","id":"스레드ID","format":"metadata"}'
```

gws 0.22.5 기준. `+send` 에는 임의 헤더(List-Unsubscribe 등)를 넣는 옵션이 없다. 한국 법의 수신거부 안내는 본문 표시로 한다.

## Gmail 한도(공식 문서, 2026-10-29 확인)

| 계정 | 하루 발송 | 비고 |
|---|---|---|
| 개인 gmail.com | 500통 | 넘기면 1~24시간 발송 불가 https://support.google.com/mail/answer/22839 |
| Google Workspace | 사용자당 2,000통(체험 계정 500) | 24시간 롤링. 반복 초과 시 정지 가능 |
| Gmail API | 사용자당 분당 6,000 단위, `messages.send` 100단위 | 이론상 분당 60통 |

- 기본 `daily_cap: 400` 은 개인 계정 500통에 여유를 둔 값이다. 이 스킬 밖에서 보낸 메일은 세지 못하므로 그날 다른 대량 발송이 있었다면 낮춘다.
- 간격 20~30초는 공식 수치가 아니라 경험칙이다. Google 은 "비정상 발송" 기준을 공개하지 않는다. 새로 만든 계정으로 바로 대량 발송하지 않는다.
- 개인 Gmail 받은편지함으로 하루 약 5,000통 이상 보내는 대량 발신자 요건(SPF·DKIM·DMARC·원클릭 수신거부)은 개인 계정 한도로는 닿지 않는다.

## 테스트 주소

자기 자신이나 `본인주소+태그@gmail.com` 별칭으로 실험한다. `+태그` 주소는 본 주소 받은편지함으로 배달된다(https://support.google.com/mail/answer/12096). 별칭으로 보낸 메일에 본 계정이 답장하면 그 답장은 보낸 사람이 본인이라서 `replies` 는 INBOX 라벨이 붙은 메시지만 답장으로 센다.
