# dante-skills

> 단테랩스(Dante Labs)가 강의·실무에서 직접 만들어 쓰는 **교육용 Claude Code 에이전트 스킬 모음** by [단테(Dante)](https://dante-labs.com)

[![skills.sh](https://img.shields.io/badge/skills.sh-dante--skills-blue)](https://skills.sh/dandacompany/dante-skills)

YouTube 강의·MBA 수업·커뮤니티 실습에서 바로 써먹을 수 있도록 정리한 스킬들입니다. 메모리 관리, 서버 보안 점검, 시장조사 분석, 보고서·슬라이드 제작, 데이터 수집·연동 등 실무 자동화에 필요한 도구를 모았습니다.

## 설치 방법

[Skills CLI](https://skills.sh/)가 필요합니다 (`npm i -g skills`).

```bash
# 특정 스킬 설치 (글로벌)
skills add dandacompany/dante-skills@<skill-name> -g -y --copy -a claude-code

# 전체 스킬 설치
skills add dandacompany/dante-skills -g -y --copy -a claude-code
```

[Hermes Agent](https://github.com/NousResearch/hermes-agent) 사용자는 `hermes skills install`로 개별 스킬을 바로 설치할 수 있습니다.

```bash
# 특정 스킬 설치 (Hermes)
hermes skills install dandacompany/dante-skills/<skill-name>
```

## 스킬 목록

### 🧠 메모리 · 지식 관리

| 스킬                        | 설명                                                                                                                                                       | 설치                                                                                                    |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| [dream](./dream/)           | 프로젝트 메모리 정리·최적화. 메모리 파일의 중복·충돌·오래된 항목을 정리하고 인덱스를 재구성합니다.                                                         | `skills add dandacompany/dante-skills@dream`<br>`hermes skills install dandacompany/dante-skills/dream` |
| [oh-my-wiki](./oh-my-wiki/) | Karpathy 스타일 LLM 위키 스킬(omw). 소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트·autoresearch·팩트체크·스웜 포함. (설치는 플러그인 마켓플레이스) | `/plugin install oh-my-wiki@oh-my-wiki-marketplace`                                                     |

### 🔒 서버 · 인프라 보안 점검

| 스킬                                            | 설명                                                                                                                                                                                                                                                 | 설치                                                                                                                                  |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [infra-security-audit](./infra-security-audit/) | 자체 호스팅 Linux 서버/VPS 보안 점검·하드닝. ufw·SSH·fail2ban·노출 포트·자동 업데이트·Cloudflare·Tailscale 점검. 기본은 읽기 전용 감사(하드닝 점수+우선순위 리포트), 안전한 수정만 자동 적용하고 위험 변경은 백업·자가 잠금 방지와 함께 승인 게이트. | `skills add dandacompany/dante-skills@infra-security-audit`<br>`hermes skills install dandacompany/dante-skills/infra-security-audit` |
| [iris-security-audit](./iris-security-audit/)   | Hermes 에이전트 4기둥 보안 감사(키·권한·스킬·격리) 체크리스트. 내장 진단을 순회하고 위험 삼각·Rule of Two로 판정해 "잘하는 것 / 조치 필요 / 신규 위험" 3부로 보고. 전부 읽기·안전 명령.                                                              | `hermes skills install dandacompany/dante-skills/iris-security-audit --category security`                                             |

### 📊 시장조사 · 데이터 분석

| 스킬                                                    | 설명                                                                                                                                                                                                                                                              | 설치                                                                                                                                          |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [deep-research](./deep-research/)                       | 병렬 웹 검색·다중 소스 검증·신뢰도 추적으로 인용 달린 심층 리서치 보고서를 생성. 시장·경쟁·기술·학술·재무·법률·트렌드 등 11개 리서치 타입 지원. 출처: [samber/cc-skills](https://github.com/samber/cc-skills) (MIT).                                              | `skills add dandacompany/dante-skills@deep-research`<br>`hermes skills install dandacompany/dante-skills/deep-research`                       |
| [swot-from-signals](./swot-from-signals/)               | 정성·정량 신호로부터 SWOT 4사분면을 자동 도출. 각 칸 3개씩 근거 URL/시그널값 명시.                                                                                                                                                                                | `skills add dandacompany/dante-skills@swot-from-signals`<br>`hermes skills install dandacompany/dante-skills/swot-from-signals`               |
| [price-positioning](./price-positioning/)               | 수집된 가격 관측치로 가격 포지셔닝 맵과 빈 가격대(화이트스페이스)를 결정론적으로 도출. 수집 도구 비종속(어떤 시장·통화도) + stdlib 결정론 분석기 동봉.                                                                                                            | `skills add dandacompany/dante-skills@price-positioning`<br>`hermes skills install dandacompany/dante-skills/price-positioning`               |
| [report-evidence-citation](./report-evidence-citation/) | 모든 산출물에서 사실/의견 분리 + 출처 URL 보존 + 평가성 어휘 차단. 신뢰성 게이트.                                                                                                                                                                                 | `skills add dandacompany/dante-skills@report-evidence-citation`<br>`hermes skills install dandacompany/dante-skills/report-evidence-citation` |
| [brand-research-glossary](./brand-research-glossary/)   | B2C 브랜드 시장조사 표기·용어 사전(무신사·29CM 등 한국 e-커머스, Bright Data 제품명, 슬라이드 형식, 금지 표현).                                                                                                                                                   | `skills add dandacompany/dante-skills@brand-research-glossary`<br>`hermes skills install dandacompany/dante-skills/brand-research-glossary`   |
| [kiwoom-broker](./kiwoom-broker/)                       | 키움증권 공식 `kwcli`를 증권사 어댑터로 사용하는 운영 스킬. 모의 시세·잔고 조회와 주문 미리보기·승인 후 집행을 분리하고, 자체 토큰·REST 호출 코드 생성을 금지한다.                                                                                                | `skills add dandacompany/dante-skills@kiwoom-broker`<br>`hermes skills install dandacompany/dante-skills/kiwoom-broker`                       |
| [magma-collect](./magma-collect/)                       | 커머스 웹 데이터 수집·적재 파이프라인. 무신사·네이버·쿠팡에서 남성 패션 상품 목록(가격·할인율·평점·리뷰 수)을 정규 CSV 스키마로 수집, 검증 스크립트 통과 후 컨펌 게이트를 거쳐 Supabase에 적재. 수집 윤리 가드 내장.                                              | `skills add dandacompany/dante-skills@magma-collect`<br>`hermes skills install dandacompany/dante-skills/magma-collect`                       |
| [kor-review-taker](./kor-review-taker/) | 국내 이커머스(쿠팡·네이버 브랜드스토어·11번가·롯데하이마트·SSG·롯데ON·G마켓) 상품 리뷰를 브라우저 탭 안 같은 출처 API 호출로 내려받아 플랫폼 공통 열 CSV·JSON으로 저장. 페이지 간격·재방문 대기·차단 감지 내장(캡차·차단 우회 없음), 응답 구조가 바뀌면 네트워크를 다시 분석해 수집기를 고치는 자가 복구 절차 포함. [BrowserSkill](https://github.com/Tencent/BrowserSkill)(`bsk`) 필요. | `skills add dandacompany/dante-skills@kor-review-taker`<br>`hermes skills install dandacompany/dante-skills/kor-review-taker` |
| [magma-mart-seed](./magma-mart-seed/)                   | 시드 고정 더미 판매 마트 생성기. 고객·상품·프로모션·주문·주문상세 5개 CSV(약 5.5만 행)에 현실적 오염 패턴 12종(중복·결측·포맷 혼재·고아 FK 등)을 의도 주입 — 데이터 정제 실습 재료. 누가 돌려도 완전히 동일한 데이터.                                             | `skills add dandacompany/dante-skills@magma-mart-seed`<br>`hermes skills install dandacompany/dante-skills/magma-mart-seed`                   |
| [magma-dashboard](./magma-dashboard/)                   | Evidence.dev BI 대시보드 제작 파이프라인. Supabase 정제 뷰를 읽어 Markdown+SQL 한 장으로 판매 대시보드를 만들고 정적 빌드까지. 소스 연결(CA 인증서 정식 경로), 컴포넌트 8종 사용법, **만든 뒤 총계를 원본과 대조하는 검산 절차** 포함 — 검산 없이 완성 보고 금지. | `skills add dandacompany/dante-skills@magma-dashboard`<br>`hermes skills install dandacompany/dante-skills/magma-dashboard`                   |

### 📑 보고서 · 슬라이드 · 디자인

| 스킬                                            | 설명                                                                                                                                                                 | 설치                                                                                                                                  |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [marp-slide-build](./marp-slide-build/)         | Marp 마크다운으로 임원 보고용 시장조사 슬라이드 12~15장 빌드. 단테랩스 paper+ink+rust 디자인 가드 강제.                                                              | `skills add dandacompany/dante-skills@marp-slide-build`<br>`hermes skills install dandacompany/dante-skills/marp-slide-build`         |
| [nextjs-tremor-report](./nextjs-tremor-report/) | 시장조사 보고서를 Next.js 15 + Tailwind + ECharts 인터랙티브 웹앱으로 빌드해 Vercel에 배포. 단테랩스 디자인 토큰·5페이지 표준 구조·ECharts 4종 패턴 강제.            | `skills add dandacompany/dante-skills@nextjs-tremor-report`<br>`hermes skills install dandacompany/dante-skills/nextjs-tremor-report` |
| [brand-logo](./brand-logo/)                     | 브랜드 로고 컨셉 디렉팅 패턴. 브리프 → 심볼 컨셉 → 이미지 프롬프트 → 생성 → 벡터화 인계. 모델 글자 약점 회피(추상·모노그램 우선), 브랜드 토큰 고정, 평가 체크리스트. | `skills add dandacompany/dante-skills@brand-logo`<br>`hermes skills install dandacompany/dante-skills/brand-logo`                     |

### ✍️ 글쓰기 · 윤문

| 스킬                                  | 설명                                                                                                                                                                                                                                     | 설치                                                                                                                        |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [humanize-korean](./humanize-korean/) | AI가 쓴 한글 글의 "AI 티"(번역투·기계적 병렬·관용구·피동 남용 등 10대 카테고리 40+ 패턴)를 탐지해 내용은 그대로 두고 문체·리듬만 자연스럽게 윤문. [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) fast-path 에디션(MIT). | `skills add dandacompany/dante-skills@humanize-korean`<br>`hermes skills install dandacompany/dante-skills/humanize-korean` |
| [remove-ai-marks](./remove-ai-marks/) | 소유하거나 처리 권한이 있는 텍스트·문서·이미지에서 숨은 Unicode, C2PA·EXIF·XMP, AI 생성기 메타데이터를 읽기 전용으로 탐지하고 선택적으로 정리. 원격 전송·외부 코드·대용량 입력을 제한한 보안 강화판(MIT).                                | `skills add dandacompany/dante-skills@remove-ai-marks`<br>`hermes skills install dandacompany/dante-skills/remove-ai-marks` |

### 🔌 데이터 수집 · API 연동

| 스킬                                    | 설명                                                                                                                                                           | 설치                                                                                                                          |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [brightdata-guide](./brightdata-guide/) | Bright Data 웹 수집 가이드(MCP + CLI 통합). MCP 도구가 있으면 MCP를, 없으면 터미널의 `bdata`/`brightdata` CLI로 검색·스크랩·구조화 추출. Hermes·Codex 등 범용. | `skills add dandacompany/dante-skills@brightdata-guide`<br>`hermes skills install dandacompany/dante-skills/brightdata-guide` |
| [tally-api](./tally-api/)               | Tally.so 폼 플랫폼 REST API·웹훅 연동. 폼·제출·분석·워크스페이스 조회 및 웹훅 생성/서명검증. curl CLI 래퍼(`tally.sh`) + HMAC-SHA256 서명 검증 스크립트 동봉.  | `skills add dandacompany/dante-skills@tally-api`<br>`hermes skills install dandacompany/dante-skills/tally-api`               |
| [official-reply](./official-reply/) | 받은 공문(.hwp/.hwpx/.pdf) 회신 묶음 만들기. 요구 사항·기한 정리 → 붙임 양식을 원본 서식 그대로 채우기(모르는 칸은 모아서 한 번에 묻기, `--require-unique`) → 회신 공문(일반기안문 서식 또는 회사 견본) → 표기법 검수(`lint --gate`)·구조 검증·직인·미리보기 PNG → Gmail 회신 초안까지만(보내기는 사람). [kordoc](https://github.com/chrisryugj/kordoc) 4.24.9+ 기반, 한컴·키 불필요. | `skills add dandacompany/dante-skills@official-reply`<br>`hermes skills install dandacompany/dante-skills/official-reply` |
| [rhwp-unified](./rhwp-unified/) | 한글 문서(HWP·HWPX·HML)를 [rhwp](https://github.com/edwardkim/rhwp) CLI로 다루는 통합 스킬. 문서 파악·요약·검색, PDF·PNG·SVG·Markdown·HWPX 내보내기, 누름틀 서식 채우기·메일머지, 표 CSV 왕복, 원본 보존 편집, 숨은 글·주입·개인정보 점검, 폴더 대량 처리, MCP 연결. 상류 edwardkim/rhwp(MIT)의 실사용 스킬 10개를 묶은 **비공식** 통합본(`references/` 는 상류 본문, `scripts/build_references.py <SHA>` 로 특정 커밋에 고정). rhwp 릴리스 바이너리 필요(macOS·Linux·Windows), 한컴·키 불필요. 「한글」·「한컴」·「HWP」·「HWPX」는 한글과컴퓨터의 등록 상표이며 이 스킬은 한글과컴퓨터·rhwp 프로젝트와 무관합니다. | `skills add dandacompany/dante-skills@rhwp-unified`<br>`hermes skills install dandacompany/dante-skills/rhwp-unified` |
| [mail-watch](./mail-watch/) | Gmail 받은편지함을 검색 조건(보낸 사람·제목·첨부 확장자)으로 감시해 새 메일이 있을 때만 에이전트를 깨우는 읽기 전용 스킬. Hermes cron 사전 점검(`wakeAgent`)으로 새 메일이 없으면 토큰 0, 있으면 메시지 id·첨부 정보를 넘김. 처리 완료 표시(ack)·재깨우기 상한·첨부 내려받기·연속 오류 보고. 예약에 다른 스킬을 붙여(`--skill`) 자동 처리. | `skills add dandacompany/dante-skills@mail-watch`<br>`hermes skills install dandacompany/dante-skills/mail-watch` |
| [mail-campaign](./mail-campaign/) | Google Sheets(또는 CSV) 명단 → 세그먼트별 개인화 메일을 gws CLI로 발송. 행 검증·보류, 초안, 내 주소 테스트, 승인 토큰 게이트, 간격·일일 상한 발송, 행별 상태·messageId 기록(재실행 시 중복 방지), 답장 수거·분류, **정보통신망법 제50조 광고성 판별**((광고)·수신동의·야간 차단). Hermes Google OAuth 재사용 — 추가 키 0개. 참고: Draft Machine(MIT-0)·outreach-composer(Apache-2.0)·consent-registry(Apache-2.0). | `skills add dandacompany/dante-skills@mail-campaign`<br>`hermes skills install dandacompany/dante-skills/mail-campaign` |

### 🎵 음악 · 미디어 생성

| 스킬                  | 설명                                                                                                                                                                                                                                            | 설치                                                                                                        |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| [acestep](./acestep/) | ACE-Step V1.5 API로 음악 생성·커버·리페인팅(text-to-music, 가사 생성, 오디오 continuation). 로컬/클라우드(`api.acemusic.ai`) 모두 지원. 출처: [ace-step/ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5) (MIT), 보안 스캐너 통과용 fork. | `skills add dandacompany/dante-skills@acestep`<br>`hermes skills install dandacompany/dante-skills/acestep` |

### ⚙️ 에이전트 운영 · 모델 최적화

| 스킬                                                    | 설명                                                                                                                                                                                                        | 설치                                                                                                                                                   |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [gpt-model-effort-advisor](./gpt-model-effort-advisor/) | GPT-5.6 모델 티어(Luna/Terra/Sol)·추론 effort(Low~Ultra)를 과업에 맞게 추천하고, 실사용 성공/실패를 학습해 갱신하며, 실패를 진단(effort↑ vs 모델↑)하고 현재 세션 모델·effort를 실시간 판독. **codex 스킬**. | `skills add dandacompany/dante-skills@gpt-model-effort-advisor -a codex`<br>`hermes skills install dandacompany/dante-skills/gpt-model-effort-advisor` |

### 🖥️ 터미널 · 워크스페이스 제어

| 스킬                    | 설명                                                                                                                                                                                                                                                                                  | 설치                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| [danteterm](./danteterm/) | DanteTerm(Wave Terminal 포크)을 `dsh`로 조종. 탭·블록 생성과 배치, 다른 패널에 키 입력 전송·스크롤백 회수, `claude`/`codex`/`hermes`를 별도 블록에 띄워 작업을 위임하고 결과를 수거(`danteterm_delegate.py`), 결과를 스크롤백 대신 preview/web/editor 블록으로 표시. 원격 연결·파일·변수·시크릿 관리 포함. | `skills add dandacompany/dante-skills@danteterm`<br>`hermes skills install dandacompany/dante-skills/danteterm` |

### 🎓 Hermes 강의 실습용

| 스킬                              | 설명                                                                                                                                                            | 설치                                                            |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [magma-support](./magma-support/) | MAGMA 고객지원 1차 응대 지식(샘플). 고객 문의를 정책 기반으로 분류·1차 답변 초안 작성, 불확실한 건 담당자 확인 필요로 표시. 헤르메스 강의 4.1 웹훅 실습 준비물. | `hermes skills install dandacompany/dante-skills/magma-support` |
| [persona-interview](./persona-interview/) | 소크라테스식 문답으로 5~7개만 물어보고 Hermes 공식 4섹션(Identity·Style·Avoid·Defaults) 구조의 `SOUL.md` 초안을 만들어 준다. 템플릿 없이 빈손에서 페르소나를 시작할 때. 헤르메스 강의 2.2 페르소나 만들기의 선택 도구. | `hermes skills install dandacompany/dante-skills/persona-interview` |

> `iris-security-audit`(강의 4.3), `tally-api`, `brightdata-guide`도 헤르메스 강의 실습에서 함께 활용됩니다.

## 스킬 상세

### 🌙 dream

메모리 통합·최적화 스킬. 뇌가 수면 중 기억을 통합하듯, 오래된 메모리를 정리하고 신호를 강화합니다.

**사용 시점:**

- 여러 세션 이후 메모리 파일이 쌓였을 때
- 삭제된 코드나 변경된 파일을 참조하는 메모리가 있을 때
- MEMORY.md 인덱스가 실제 파일과 맞지 않을 때
- 사용자가 명시적으로 메모리 최적화를 요청할 때

```bash
skills add dandacompany/dante-skills@dream -g -y --copy -a claude-code
```

### 📚 oh-my-wiki

Karpathy "LLM Wiki" 워크플로의 Claude Code 구현. 이 repo의 항목은 **설치 안내용 포인터**이고, 실제 스킬·훅·커맨드는 별도 플러그인 마켓플레이스로 배포됩니다.

```
/plugin marketplace add dandacompany/oh-my-wiki
/plugin install oh-my-wiki@oh-my-wiki-marketplace
```

소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트(sqlite) · autoresearch · 팩트체크/일관성/용어집 · 스웜 병렬 디스패치 포함. 전체 문서: **[github.com/dandacompany/oh-my-wiki](https://github.com/dandacompany/oh-my-wiki)**

### 🛡️ infra-security-audit

자체 호스팅 Linux 서버·VPS의 인프라 보안을 SSH 또는 로컬에서 점검하고 하드닝하는 스킬입니다.

- **audit(기본, 읽기 전용)** — ufw·SSH 설정·fail2ban·노출 포트·자동 업데이트·Cloudflare 프록시·Tailscale을 점검해 하드닝 점수와 우선순위 리포트를 냅니다
- **plan → apply** — 되돌리기 쉬운 수정만 자동 적용하고, ufw 활성화·sshd 수정·포트 바인딩 같은 위험 변경은 백업과 자가 잠금 방지 확인을 거쳐 사람 승인 후에만 적용합니다
- 비개발자에게 보고할 때의 말투 지침이 들어 있습니다

```bash
skills add dandacompany/dante-skills@infra-security-audit -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/infra-security-audit
```

### 🔐 iris-security-audit

Hermes 에이전트의 4기둥(키·권한·스킬·도커 격리) 보안 감사 체크리스트입니다. 헤르메스 강의 4.3 보안 감사 자동화 실습 준비물입니다.

- 위험 삼각(lethal trifecta)과 Rule of Two로 판정합니다
- 「잘하는 것 / 조치 필요 / 신규 위험」 3부 보고서를 냅니다. 점검 명령은 모두 읽기 전용이거나 안전한 명령입니다
- 대화형 세션에서는 발견 이슈를 하나씩 제시하고 처리 방식(자동·승인 후·안내)을 확인받습니다. cron·훅 같은 무인 실행에서는 보고서만 보내고, 이상이 없으면 `[SILENT]`로 조용히 넘어갑니다

```bash
hermes skills install dandacompany/dante-skills/iris-security-audit --category security
```

### 🔎 deep-research

병렬 웹 검색으로 인용이 달린 심층 리서치 보고서를 만드는 스킬입니다. 원본은 [samber/cc-skills](https://github.com/samber/cc-skills)(MIT)이며, 출처 표기만 더했습니다.

- 범위 정하기 → 핵심 조사 → 경쟁·지형 분석 → 심화 조사를 단계마다 병렬로 펼쳐 진행하고, 마지막에 종합합니다
- 출처를 여러 곳에서 교차 검증하고, 주장마다 신뢰도를 추적합니다
- 리서치 유형 11가지: 시장(TAM/SAM)·도메인·기술·경쟁·제품·학술·인물/기관 실사·재무·법률·트렌드 등
- Markdown 보고서(핵심 발견·전략 제언·리스크·다음 단계)를 만들고, 원하면 PDF로도 내보냅니다

```bash
skills add dandacompany/dante-skills@deep-research -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/deep-research
```

### 🧭 swot-from-signals

브랜드 리서처가 모은 정성·정량 신호로 SWOT(강점·약점·기회·위협) 매트릭스를 도출하는 분석 패턴입니다.

- 입력: 브랜드 리서처 산출물 6종
- 사분면마다 3개씩 뽑고, 모든 항목에 근거 URL이나 시그널 값을 붙입니다
- 고정된 JSON 형식으로 출력해 슬라이드 제작자에게 넘깁니다

```bash
skills add dandacompany/dante-skills@swot-from-signals -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/swot-from-signals
```

### 📈 price-positioning

수집된 가격 관측치(브랜드·품목·가격·출처)로부터 **가격 포지셔닝 맵**과 **빈 가격대(화이트스페이스)** 를 결정론적으로 도출하는 분석 패턴. "수집물 → 분석" 계열이라 **수집 도구에 종속되지 않는다** — 웹 수집 MCP·검색 API·사내 시트·수기 입력 무엇으로 모았든 동일하게 동작하고, 어떤 시장·통화에도 쓸 수 있다.

- 입력: 정규화 관측치(CSV/JSON)
- 처리: stdlib 전용 결정론 분석기(`scripts/positioning.py`) — 밴드별 통계·화이트스페이스·이상치·플래그. 같은 입력이면 항상 같은 출력. 네트워크·환경변수·외부 실행 없음.
- 출력: `positioning.json`(고정 스키마) + `pricing-landscape.md`(고정 섹션)

```bash
skills add dandacompany/dante-skills@price-positioning -g -y --copy -a claude-code
```

### 📎 report-evidence-citation

모든 산출물에 적용하는 인용·근거 공통 규칙입니다. 리서치 팀의 모든 에이전트가 상속하는 신뢰성 게이트 역할을 합니다.

- 사실과 의견을 나누고, 출처 URL을 끝까지 보존합니다
- 추측성 어휘와 근거 없는 평가 발언을 막습니다
- 보고 형식과 검증 체크리스트가 들어 있습니다

```bash
skills add dandacompany/dante-skills@report-evidence-citation -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/report-evidence-citation
```

### 📖 brand-research-glossary

B2C 브랜드 시장조사 산출물의 표기·용어를 통일하는 공통 용어 사전입니다.

- 한국 e-커머스·패션 브랜드 표기(무신사·29CM·W컨셉·LF몰 등)
- Bright Data 제품명(Web Unlocker·SERP API·Datasets·Scraping Browser)과 슬라이드 형식 명칭(Marp·Reveal.js)
- 금지 표현 목록과 검증 절차가 들어 있습니다

```bash
skills add dandacompany/dante-skills@brand-research-glossary -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/brand-research-glossary
```

### 💹 kiwoom-broker

키움증권 공식 CLI(`kwcli`/`kiwoomcli`)를 증권사 어댑터로 쓰는 운영 스킬입니다.

- 국내 ETF·주식 시세, 일봉, 보유 종목을 조회합니다. 모의투자 조회와 `kiwoomcli doctor` 진단도 다룹니다
- 주문은 두 단계로 나눕니다. 먼저 전송하지 않은 미리보기를 보여 주고, 승인을 받은 뒤에만 집행합니다
- 직접 REST를 호출하거나 자체 토큰을 발급하는 코드는 만들지 않습니다

```bash
skills add dandacompany/dante-skills@kiwoom-broker -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/kiwoom-broker
```

### 🛒 magma-collect

MAGMA 가상 오피스 강의(섹션 7.2)의 커머스 데이터 수집·적재 실습 스킬입니다.

- 무신사·네이버 가격비교·쿠팡에서 남성 패션 키워드의 상품 목록(상품명·브랜드·가격·할인율·평점·리뷰 수)을 Bright Data 도구로 수집합니다
- 열 순서가 고정된 정규 CSV 스키마로 바꿉니다. 소스마다 없는 필드는 빈 값으로 둡니다(예: 쿠팡은 평점이 없음)
- 검증 스크립트를 통과하고 사용자 확인을 받은 뒤에만 Supabase에 적재합니다
- 수집 윤리 규칙이 들어 있습니다

```bash
skills add dandacompany/dante-skills@magma-collect -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/magma-collect
```

### 💬 kor-review-taker

국내 이커머스 7곳(쿠팡·네이버 브랜드스토어·11번가·롯데하이마트·SSG·롯데ON·G마켓)의 상품 리뷰를 내려받는 스킬입니다.

- [BrowserSkill](https://github.com/Tencent/BrowserSkill)(`bsk`)로 연 브라우저 탭 안에서, 그 사이트가 쓰는 API를 직접 부르는 스크립트로 빠르게 받습니다
- 모든 플랫폼에 같은 열을 쓰는 CSV·JSON으로 저장합니다
- 페이지 사이 간격, 재방문 대기, 차단 감지를 넣었습니다. 캡차나 차단은 우회하지 않습니다
- 응답 구조가 바뀌면 네트워크를 다시 분석해 수집기를 고치는 자가 복구 절차가 들어 있습니다. 종료 코드마다 다음에 할 일도 정해 두었습니다

```bash
skills add dandacompany/dante-skills@kor-review-taker -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/kor-review-taker
```

### 🧪 magma-mart-seed

MAGMA 강의(섹션 7.3) 데이터 정제 실습용 판매·프로모션 더미 데이터 마트 생성기입니다.

- 고객·상품·프로모션·주문·주문상세 CSV 5개, 약 5.5만 행을 만듭니다
- 중복 고객·결측·날짜 포맷 4종 혼재·금액 표기 혼재·음수 수량·고아 FK·이상치 가격·비정규 코드값 등 현실적인 오염 패턴 12종을 일부러 넣었습니다
- 시드가 고정돼 있어 누가 언제 실행해도 같은 데이터가 나옵니다

```bash
skills add dandacompany/dante-skills@magma-mart-seed -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/magma-mart-seed
```

### 📊 magma-dashboard

MAGMA 강의(섹션 7.4)의 Evidence.dev BI 대시보드 제작 스킬입니다.

- Supabase 정제 뷰를 읽어 Markdown+SQL 페이지로 판매 대시보드를 만들고, 정적 빌드까지 합니다
- CA 인증서를 포함한 소스 연결 방법과 컴포넌트 8종 사용법을 담았습니다
- **검산 절차** — 만든 뒤 총계를 원본과 대조합니다. 검산 없이는 완성으로 보고하지 않습니다
- 실측으로 확인한 함정을 정리해 두었습니다

```bash
skills add dandacompany/dante-skills@magma-dashboard -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/magma-dashboard
```

### 🖼️ marp-slide-build

Marp 마크다운으로 임원 보고용 시장조사 슬라이드 12~15장을 빌드해 PDF·HTML로 내보내는 표준 패턴입니다.

- 12장 표준 구성 골격을 씁니다
- 단테랩스 paper+ink+rust 디자인 가드를 지키지 않으면 빌드를 거부합니다
- 차트 규칙과 검증 절차가 들어 있습니다

```bash
skills add dandacompany/dante-skills@marp-slide-build -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/marp-slide-build
```

### 🌐 nextjs-tremor-report

시장조사 보고서를 정적 PDF 대신 인터랙티브 웹앱으로 만들어 Vercel에 배포하는 스킬입니다. Next.js 15, Tailwind, ECharts를 씁니다.

- 단테랩스 디자인 토큰(paper·ink·rust·slate)을 Tailwind 설정으로 고정합니다
- 페이지 5개(홈·SWOT·차트·팩트체크·경쟁사)의 표준 구조와 ECharts 차트 4종 패턴을 지킵니다
- 더미 데이터 규칙을 따르고, 메타 면책 문구는 넣지 않습니다
- 배포 전에 자가 검증 체크리스트를 돌리고, 트러블슈팅 안내도 담았습니다

```bash
skills add dandacompany/dante-skills@nextjs-tremor-report -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/nextjs-tremor-report
```

### ✒️ brand-logo

브랜드 로고 컨셉을 디렉팅하는 디자이너 직무용 스킬입니다. 5단계로 진행합니다: 브리프 → 컨셉 압축 → 프롬프트 → 생성 → 선별·벡터화 인계.

- 이미지 생성 모델은 글자를 잘 못 그립니다. 그래서 심볼·추상·모노그램을 먼저 시도합니다
- DESIGN.md가 있으면 그 브랜드 토큰(정확한 hex·폰트·비율)을 그대로 씁니다
- 강한 네거티브 프롬프트와 평가 체크리스트로 결과가 흔들리지 않게 합니다
- 로고, 워드마크, 앱 아이콘, 파비콘, 채널 아이콘 제작에 씁니다

```bash
skills add dandacompany/dante-skills@brand-logo -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/brand-logo
```

### ✍️ humanize-korean

AI(ChatGPT·Claude·Gemini)가 쓴 한글 텍스트를 사람이 쓴 글처럼 되돌리는 윤문 스킬. 단일 호출 안에서 탐지 → 윤문 → 자체검증까지 끝내는 **독립형 fast-path 에디션**입니다.

- 4대 철칙: 의미 불변 · 근거 기반 · 장르 유지 · 과윤문 금지(변경률 50% 초과 시 롤백)
- 룰북: 10대 카테고리 × 40+ AI 티 패턴 분류 체계(`references/ai-tell-taxonomy.md`) + 카테고리별 치환 레시피
- 산출물: `_workspace/{run_id}/final.md` + 변경률·등급(A~D)·자체검증 리포트
- 원본: [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) (MIT) — 정밀 3콜 파이프라인이 필요하면 원본 플러그인 설치 권장. fork: [dandacompany/im-not-ai](https://github.com/dandacompany/im-not-ai)

```bash
skills add dandacompany/dante-skills@humanize-korean -g -y --copy -a claude-code
```

### 🧽 remove-ai-marks

자신이 소유하거나 처리 권한이 있는 텍스트·문서·이미지의 출처 표식과 메타데이터를 검사하고 정리하는 스킬입니다.

- **Layer A 텍스트 검사** — zero-width·bidi·variation selector·이상 공백·선택적 homoglyph 탐지/정규화
- **파일 메타데이터 검사** — PNG/JPEG/SVG/PDF/DOCX/ODT/HTML/Markdown의 C2PA·EXIF·XMP·AI 생성기 흔적
- **보존적 정리** — PDF는 검사 전용, DOCX `customXml`은 AI 표식이 확인된 part만 제거, ZWJ·ZWNJ·variation selector는 기본 보존
- **통계적 텍스트 워터마크** — 공식 탐지 키 없이 확정 판정하지 않으며, 사용자가 원할 때만 의미 보존 rewrite를 제안
- **안전 기본값** — 입력 256 MiB·stdin 64 MiB 고정 제한, 환경변수·자격증명 파일을 읽지 않음
- **실행 경계** — 네트워크 호출, 외부 실행 파일, 외부 모델 코드, 저장소 자동 다운로드를 모두 제외
- **오프라인 rewrite** — 의미 보존 rewrite 프롬프트만 생성하며 문서 내용을 외부로 전송하지 않음

원본은 [`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover)의 MIT 코드이며, 단테랩스 배포본은 감사 커밋 `f10efaa7`을 기준으로 보안 강화했습니다. 탐지 결과가 음성이라고 해서 사람이 작성한 콘텐츠라는 뜻은 아닙니다.

```bash
skills add dandacompany/dante-skills@remove-ai-marks -g -y --copy -a claude-code
```

### 🕸️ brightdata-guide

Bright Data로 웹 데이터를 수집하는 가이드입니다. MCP와 CLI 두 방식을 함께 다룹니다.

- 불러온 도구를 확인해 MCP가 있으면 MCP를, 없으면 터미널의 `bdata`/`brightdata` CLI를 씁니다
- 검색·스크랩·구조화 추출 중 무엇을 쓸지 고르는 결정 트리가 있습니다. 구조화 데이터셋을 쓸지 스크래핑할지도 판단해 줍니다
- 필요한 도구 그룹이 꺼져 있으면 운영자에게 켜 달라고 요청하는 절차가 들어 있습니다
- Hermes·Codex 등 여러 하네스에서 씁니다

```bash
skills add dandacompany/dante-skills@brightdata-guide -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/brightdata-guide
```

### 📝 tally-api

Tally.so 폼 플랫폼의 REST API와 웹훅을 다루는 스킬입니다.

- 폼 목록·상세 조회, 제출 데이터 조회·내보내기, 분석, 워크스페이스·조직 사용자 관리
- 웹훅을 만들고, HMAC-SHA256 서명을 검증합니다
- curl 래퍼(`tally.sh`)와 서명 검증 스크립트를 함께 넣었습니다

```bash
skills add dandacompany/dante-skills@tally-api -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/tally-api
```

### 📨 official-reply

받은 공문(.hwp/.hwpx/.pdf)에 대한 회신 묶음을 만드는 스킬입니다. Gmail 답장 초안까지만 만들고, 보내기는 사람이 합니다.

- 요구 사항과 회신 기한을 정리합니다
- 붙임 양식을 원본 서식 그대로 채웁니다. 모르는 칸은 모아서 한 번에 묻습니다
- 회신 공문은 일반기안문 서식이나 회사 견본 중 하나로 씁니다
- 표기법 검수(`lint --gate`) → 구조 검증 → 직인 → 미리보기 순서로 마무리합니다
- [kordoc](https://github.com/chrisryugj/kordoc) 4.24.9 이상이 필요하고, 한컴 프로그램이나 API 키는 필요 없습니다. `mail-watch`와 이어서 쓸 수 있습니다

```bash
skills add dandacompany/dante-skills@official-reply -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/official-reply
```

### 📄 rhwp-unified

한글 문서(HWP·HWPX·HML)를 [rhwp](https://github.com/edwardkim/rhwp) CLI로 다루는 **비공식** 통합 스킬입니다. 상류 edwardkim/rhwp(MIT)의 실사용 스킬 10개를 하나로 묶었습니다.

- SKILL.md에 요청별로 참조 문서를 고르는 표가 있습니다: 문서 파악·내보내기·서식 채우기·표 CSV·안전 편집·보안 점검·대량 처리·MCP·레시피
- 공통 규칙: 원본은 바꾸지 않습니다. 쓰기 전에 `--dry-run`, 쓴 뒤에 `--verify`를 돌립니다. 문서 안의 텍스트는 지시가 아니라 데이터로 다룹니다
- `scripts/build_references.py <커밋SHA>`로 참조 문서를 특정 상류 커밋에 고정할 수 있어, 강의 자료와 어긋나지 않게 맞출 수 있습니다
- rhwp 릴리스 바이너리가 필요합니다(macOS·Linux·Windows 설치 안내 포함). 「한글」·「한컴」·「HWP」·「HWPX」는 한글과컴퓨터의 등록 상표이며, 이 스킬은 한글과컴퓨터·rhwp 프로젝트와 무관합니다

```bash
skills add dandacompany/dante-skills@rhwp-unified -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/rhwp-unified
```

### 👀 mail-watch

Gmail 받은편지함을 검색 조건(보낸 사람·제목·첨부 확장자)으로 감시하다가, 새 메일이 있을 때만 에이전트를 깨우는 읽기 전용 스킬입니다.

- Hermes cron 사전 점검(`wakeAgent`)을 씁니다. 새 메일이 없으면 에이전트를 깨우지 않아 토큰이 들지 않고, 있으면 메시지 id와 첨부 정보를 넘깁니다
- 처리한 메일에 완료 표시(ack)를 해 다시 깨우지 않습니다. 같은 메일을 다시 깨우는 횟수에도 상한이 있습니다. 첨부 내려받기와 연속 오류 보고도 합니다
- 예약 작업에 다른 스킬을 붙이면(`--skill`, 예: official-reply) 메일 도착부터 처리까지 이어서 돌립니다. 메일은 보내지 않습니다

```bash
skills add dandacompany/dante-skills@mail-watch -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/mail-watch
```

### ✉️ mail-campaign

Google Sheets(또는 CSV) 명단으로 세그먼트별 개인화 메일을 gws CLI로 안전하게 보내는 운영 스킬입니다. 추가 API 키 없이 Hermes Google OAuth를 그대로 씁니다.

- 9단계로 진행합니다: 열 매핑 → 행 검증·보류 → 초안 → 내 주소로 테스트 발송 → 승인 토큰 게이트 → 간격·일일 상한을 지키며 발송 → 상태 기록 → 답장 수거·분류
- 행마다 상태와 messageId를 기록해, 다시 실행해도 같은 사람에게 두 번 보내지 않습니다
- **정보통신망법 제50조 광고성 판별**: 제목 앞 (광고) 표기, 수신 동의 열, 발신자·수신 거부 안내, 야간(21~08시) 발송 차단
- Hermes 칸반 모드(선택)를 지원하고, 운영하며 배운 규칙을 쌓는 절이 있습니다. 참고한 프로젝트: Draft Machine(MIT-0)·outreach-composer(Apache-2.0)·consent-registry(Apache-2.0)

```bash
skills add dandacompany/dante-skills@mail-campaign -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/mail-campaign
```

### 🎵 acestep

ACE-Step V1.5 API로 음악을 생성·편집하는 스킬입니다. 원본은 [ace-step/ACE-Step-1.5](https://github.com/ace-step/ACE-Step-1.5)(MIT)입니다.

- text-to-music, 가사 생성, 오디오 이어 붙이기(continuation), 커버·리페인팅
- 공식 클라우드(`api.acemusic.ai`)와 로컬·사용자 지정 API를 모두 지원합니다
- Hermes 보안 스캐너 오탐을 피하려고 변수명 등만 고친 포크입니다. 동작은 원본과 같습니다

```bash
skills add dandacompany/dante-skills@acestep -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/acestep
```

### 🎚️ gpt-model-effort-advisor

GPT-5.6의 두 다이얼 — **모델 티어**(Luna/Terra/Sol, 지능 상한)와 **추론 effort**(Low~Ultra, 사고 시간) — 를 과업에 맞게 골라 주는 **codex 스킬**. 자동 라우터가 아니라 **추천기**로, 근거 있는 출발점과 승급 규칙을 제안하고 전환은 사람이 한다.

- **추천** — 과업 4축(검증가능성·실패비용·처리량·추론깊이)으로 티어·effort와 "싸게 먼저 → 실패 지점에서만 승급" 규칙 제시.
- **학습** — 실사용 성공/실패를 `registry.py`에 기록. 개인 이력이 콜드스타트 휴리스틱보다 우선한다(모델이 바뀌어도 낡지 않음).
- **실패 진단** — 얕은 추론이면 effort↑, **High에서도 실패면 effort 말고 모델 티어↑**, 무한 다듬기면 effort↓+완료 기준 명시.
- **세션 상태** — 현재 세션의 모델·effort를 실시간 판독.

```bash
# codex 스킬로 설치 (전역)
skills add dandacompany/dante-skills@gpt-model-effort-advisor -g -y --copy -a codex
```

설치 후 codex 세션에서 "이 작업 어떤 모델로 할까?"처럼 물어보거나 작업을 시키면 자동으로 추천한다. 레지스트리는 빈 상태로 시작해 사용자의 실제 결과로 채워진다.

### 🖥️ danteterm

DanteTerm(Wave Terminal 포크)을 `dsh` 명령으로 조종하는 스킬입니다.

- 탭과 블록을 만들고 배치합니다. 다른 패널에 키 입력을 보내고 스크롤백을 회수합니다
- `claude`/`codex`/`hermes`를 별도 블록에 띄워 작업을 맡기고 결과를 거둡니다(`danteterm_delegate.py`)
- 결과를 스크롤백 대신 preview/web/editor 블록으로 보여 줍니다
- 블록 지정 실수를 막는 규칙(번호가 아니라 uuid로 지정)이 있고, 원격 연결·파일·변수·시크릿 관리도 다룹니다

```bash
skills add dandacompany/dante-skills@danteterm -g -y --copy -a claude-code
hermes skills install dandacompany/dante-skills/danteterm
```

### 🎧 magma-support

MAGMA 고객지원 1차 응대 지식(샘플)입니다. 헤르메스 강의 4.1 웹훅 실습 준비물입니다.

- 제품·사이즈·재입고·교환/환불·배송 정책을 참고해 정중한 1차 답변 초안을 씁니다
- 확실하지 않은 정보는 추측하지 않고 「담당자 확인 필요」로 표시합니다
- gws로 Gmail 초안을 저장하는 방법이 들어 있습니다

```bash
hermes skills install dandacompany/dante-skills/magma-support
```

### 🗣️ persona-interview

소크라테스식 문답으로 짧게 인터뷰해 Hermes `SOUL.md` 초안을 만드는 스킬입니다. 헤르메스 강의 2.2 페르소나 만들기에서 선택해 쓰는 도구입니다.

- 5~7개만 묻고 Hermes 공식 4섹션(Identity·Style·Avoid·Defaults) 구조로 정리합니다
- 빈손에서 페르소나를 시작할 때나, 기존 SOUL.md를 내 말투로 바꿀 때 씁니다

```bash
hermes skills install dandacompany/dante-skills/persona-interview
```

---

## 별도 배포 도구

스킬 형태가 아닌 1줄 curl 한 방으로 적용하는 운영 패치는 별도 repo로 분리되어 있습니다:

- **[paperclip-hotpatch](https://github.com/dandacompany/paperclip-hotpatch)** — paperclipai/paperclip의 codex_local 어댑터에 GPT-5.5를 추가하는 1줄 hotpatch.
  ```bash
  curl -fsSL https://raw.githubusercontent.com/dandacompany/paperclip-hotpatch/main/patch.sh | bash
  ```

---

## 기여 / 문의

- **YouTube**: [@dante-labs](https://youtube.com/@dante-labs)
- **Discord**: [Dante Labs Community](https://discord.com/invite/rXyy5e9ujs)
- **Email**: dante@dante-labs.com

☕️ 도움이 되셨다면 [커피 한 잔 후원](https://buymeacoffee.com/dante.labs)도 감사히 받습니다.
