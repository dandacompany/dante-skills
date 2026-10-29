# 칸반 선택 모드(Hermes)

> 일부만 실측했다(2026-10-29, Hermes v0.22.5). cron 세션이 터미널의 `hermes kanban comment` 로 카드에 코멘트를 남기는 것은 확인했다. 세그먼트 카드 검토 흐름 전체는 돌려 보지 않았다. 기본 흐름(SKILL.md 9단계)만으로 충분하면 쓰지 않는다.

세그먼트마다 카드 한 장, 보류 행 카드 한 장을 두고 사람이 카드를 검토한다. 수십 통 캠페인이어도 검토는 「세그먼트 수 + 1」번으로 끝난다. 행마다 카드를 만드는 방식은 30행이면 30번 클릭해야 하고 카드마다 워커가 떠서 권하지 않는다.

## 전제

- 채팅 봇이 칸반 도구로 카드를 만들려면 `kanban` 툴셋을 이름으로 켠다: `hermes -p <프로필> tools enable kanban --platform <플랫폼>`. 툴셋 없이 터미널의 `hermes kanban …` 명령으로도 된다(cron 에서 확인함).
- 사람만 검수하게 하려면 `config.yaml` 에 `kanban.review_dispatch: false`. 워커가 카드를 집어 가지 않게 하려면 `--initial-status blocked` 로 만든다.

## 흐름

1. `check` 와 `render` 까지는 기본 흐름과 같다.
2. 카드를 만든다. 멱등 키는 `<캠페인 이름>:seg:<세그먼트>` 와 `<캠페인 이름>:holds` 를 쓴다.

   ```bash
   hermes kanban create "메일 [연동 완료] 13통 — 견본 검토" --tenant "<캠페인 이름>" --initial-status blocked \
     --idempotency-key "<캠페인 이름>:seg:연동 완료" --body "$(python3 "$MC" preview <폴더> --row <그 세그먼트 첫 행>)"
   hermes kanban create "메일 보류 3행 — 사유 확인" --tenant "<캠페인 이름>" --initial-status blocked \
     --idempotency-key "<캠페인 이름>:holds" --body "$(python3 "$MC" check <폴더> --no-write)"
   ```

3. 문구가 준비되면 세그먼트 카드를 검수 칸으로 옮긴다: `hermes kanban request-review <카드 id>`(사람만 검수하려면 `kanban.review_dispatch: false`). 사람이 검토해 승인하면 done 으로 옮기고, 고칠 점은 코멘트로 남긴다. 보류 카드는 시트를 고친 뒤 `check` 를 다시 돌리고 닫는다.
4. 승인되지 않은 세그먼트의 행은 시트 `발송 상태` 에 `제외` 를 적는다. 그다음 `plan` → 승인 토큰 → `send` 는 기본 흐름 그대로 한다. 카드 승인은 문구 검토이고, 마지막 일괄 승인 게이트를 대신하지 않는다.
5. 「N일 뒤 답장 확인」은 칸반으로 하지 않는다. v0.22.5 의 `kanban schedule` 은 사유만 남기고 타이머를 만들지 않는다. **cron 으로 한다**:

   ```bash
   hermes cron create "every 1d" "mail-campaign 스킬로 <폴더> 의 답장을 replies 로 수거해 분류하고 classify 로 기록한 뒤, 요약을 hermes kanban comment <카드 id> 로 남겨. 메일과 초안은 만들지 마." \
     --skill mail-campaign --deliver local
   ```

   후속 메일 발송은 cron 에서 하지 않는다(초안까지만). 스케줄러는 게이트웨이가 떠 있어야 저절로 돈다.

## 주의

- 칸반 워커 프로세스는 백그라운드 자기개선(refine)을 하지 않는다. 운영 규칙 학습은 사람과 나누는 대화에서 `/refine` 으로 한다.
- 워커끼리는 서로의 카드를 못 보므로 톤·서명·금지 표현은 campaign.md 에 두고, 카드 본문에는 렌더 결과만 넣는다.
