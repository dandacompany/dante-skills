# 참고한 공개 스킬

코드를 복사하지 않았다. 아래 스킬에서 흐름과 기준을 참고했다(2026-10-29 확인).

| 스킬 | 라이선스 | 참고한 것 |
|---|---|---|
| [Draft Machine](https://clawhub.ai/audiojak/skills/draft-machine) (audiojak) | MIT-0 | 템플릿 → 첫 행 미리보기 → 전체 렌더 → 초안 일괄 생성 흐름. 재실행 때 초안이 중복되는 한계를 저널·해시로 보완 |
| [outreach-composer](https://github.com/anthropics/knowledge-work-plugins) (anthropics/knowledge-work-plugins, small-business) | Apache-2.0 | 모든 발송을 승인 대기열에 두는 원칙, 받는 사람에 대해 근거 없는 개인화를 하지 않는 기준 |
| [consent-registry](https://github.com/aaron-he-zhu/aaron-marketing-skills) (aaron-he-zhu) | Apache-2.0 | 수신거부를 기록해 이후 발송에서 빼는 구조(이 스킬은 수신동의 열 `거부(날짜)` 로 단순화) |
| gmail-skill (idanbeck/claude-skills) | 미지정 | 라이선스가 없어 코드·문구는 쓰지 않았다. 건별 확인이라는 아이디어만 |
| [googleworkspace/cli](https://github.com/googleworkspace/cli) | Apache-2.0 | 발송·시트 도구(gws). 2026-03 삭제된 `recipe-send-personalized-emails` 의 `sheets +read` → `gmail +send` 조합 |
