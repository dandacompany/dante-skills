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

## 스킬 목록

### 🧠 메모리 · 지식 관리

| 스킬                        | 설명                                                                                                                                                       | 설치                                                |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [dream](./dream/)           | 프로젝트 메모리 정리·최적화. 메모리 파일의 중복·충돌·오래된 항목을 정리하고 인덱스를 재구성합니다.                                                         | `skills add dandacompany/dante-skills@dream`        |
| [oh-my-wiki](./oh-my-wiki/) | Karpathy 스타일 LLM 위키 스킬(omw). 소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트·autoresearch·팩트체크·스웜 포함. (설치는 플러그인 마켓플레이스) | `/plugin install oh-my-wiki@oh-my-wiki-marketplace` |

### 🔒 서버 · 인프라 보안 점검

| 스킬                                            | 설명                                                                                                                                                                                                                                                 | 설치                                                                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [infra-security-audit](./infra-security-audit/) | 자체 호스팅 Linux 서버/VPS 보안 점검·하드닝. ufw·SSH·fail2ban·노출 포트·자동 업데이트·Cloudflare·Tailscale 점검. 기본은 읽기 전용 감사(하드닝 점수+우선순위 리포트), 안전한 수정만 자동 적용하고 위험 변경은 백업·자가 잠금 방지와 함께 승인 게이트. | `skills add dandacompany/dante-skills@infra-security-audit`                               |
| [iris-security-audit](./iris-security-audit/)   | Hermes 에이전트 4기둥 보안 감사(키·권한·스킬·격리) 체크리스트. 내장 진단을 순회하고 위험 삼각·Rule of Two로 판정해 "잘하는 것 / 조치 필요 / 신규 위험" 3부로 보고. 전부 읽기·안전 명령.                                                              | `hermes skills install dandacompany/dante-skills/iris-security-audit --category security` |

### 📊 시장조사 · 데이터 분석

| 스킬                                                    | 설명                                                                                                                                                                                                                 | 설치                                                            |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [deep-research](./deep-research/)                       | 병렬 웹 검색·다중 소스 검증·신뢰도 추적으로 인용 달린 심층 리서치 보고서를 생성. 시장·경쟁·기술·학술·재무·법률·트렌드 등 11개 리서치 타입 지원. 출처: [samber/cc-skills](https://github.com/samber/cc-skills) (MIT). | `skills add dandacompany/dante-skills@deep-research`            |
| [swot-from-signals](./swot-from-signals/)               | 정성·정량 신호로부터 SWOT 4사분면을 자동 도출. 각 칸 3개씩 근거 URL/시그널값 명시.                                                                                                                                   | `skills add dandacompany/dante-skills@swot-from-signals`        |
| [price-positioning](./price-positioning/)               | 수집된 가격 관측치로 가격 포지셔닝 맵과 빈 가격대(화이트스페이스)를 결정론적으로 도출. 수집 도구 비종속(어떤 시장·통화도) + stdlib 결정론 분석기 동봉.                                                               | `skills add dandacompany/dante-skills@price-positioning`        |
| [report-evidence-citation](./report-evidence-citation/) | 모든 산출물에서 사실/의견 분리 + 출처 URL 보존 + 평가성 어휘 차단. 신뢰성 게이트.                                                                                                                                    | `skills add dandacompany/dante-skills@report-evidence-citation` |
| [brand-research-glossary](./brand-research-glossary/)   | B2C 브랜드 시장조사 표기·용어 사전(무신사·29CM 등 한국 e-커머스, Bright Data 제품명, 슬라이드 형식, 금지 표현).                                                                                                      | `skills add dandacompany/dante-skills@brand-research-glossary`  |

### 📑 보고서 · 슬라이드 · 디자인

| 스킬                                            | 설명                                                                                                                                                                 | 설치                                                        |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| [marp-slide-build](./marp-slide-build/)         | Marp 마크다운으로 임원 보고용 시장조사 슬라이드 12~15장 빌드. 단테랩스 paper+ink+rust 디자인 가드 강제.                                                              | `skills add dandacompany/dante-skills@marp-slide-build`     |
| [nextjs-tremor-report](./nextjs-tremor-report/) | 시장조사 보고서를 Next.js 15 + Tailwind + ECharts 인터랙티브 웹앱으로 빌드해 Vercel에 배포. 단테랩스 디자인 토큰·5페이지 표준 구조·ECharts 4종 패턴 강제.            | `skills add dandacompany/dante-skills@nextjs-tremor-report` |
| [brand-logo](./brand-logo/)                     | 브랜드 로고 컨셉 디렉팅 패턴. 브리프 → 심볼 컨셉 → 이미지 프롬프트 → 생성 → 벡터화 인계. 모델 글자 약점 회피(추상·모노그램 우선), 브랜드 토큰 고정, 평가 체크리스트. | `skills add dandacompany/dante-skills@brand-logo`           |

### ✍️ 글쓰기 · 윤문

| 스킬                                  | 설명                                                                                                                                                                                                                                     | 설치                                                   |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [humanize-korean](./humanize-korean/) | AI가 쓴 한글 글의 "AI 티"(번역투·기계적 병렬·관용구·피동 남용 등 10대 카테고리 40+ 패턴)를 탐지해 내용은 그대로 두고 문체·리듬만 자연스럽게 윤문. [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) fast-path 에디션(MIT). | `skills add dandacompany/dante-skills@humanize-korean` |

### 🔌 데이터 수집 · API 연동

| 스킬                                    | 설명                                                                                                                                                           | 설치                                                    |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| [brightdata-guide](./brightdata-guide/) | Bright Data 웹 수집 가이드(MCP + CLI 통합). MCP 도구가 있으면 MCP를, 없으면 터미널의 `bdata`/`brightdata` CLI로 검색·스크랩·구조화 추출. Hermes·Codex 등 범용. | `skills add dandacompany/dante-skills@brightdata-guide` |
| [tally-api](./tally-api/)               | Tally.so 폼 플랫폼 REST API·웹훅 연동. 폼·제출·분석·워크스페이스 조회 및 웹훅 생성/서명검증. curl CLI 래퍼(`tally.sh`) + HMAC-SHA256 서명 검증 스크립트 동봉.  | `skills add dandacompany/dante-skills@tally-api`        |

### ⚙️ 에이전트 운영 · 모델 최적화

| 스킬                                                    | 설명                                                                                                                                                                                                        | 설치                                                                     |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| [gpt-model-effort-advisor](./gpt-model-effort-advisor/) | GPT-5.6 모델 티어(Luna/Terra/Sol)·추론 effort(Low~Ultra)를 과업에 맞게 추천하고, 실사용 성공/실패를 학습해 갱신하며, 실패를 진단(effort↑ vs 모델↑)하고 현재 세션 모델·effort를 실시간 판독. **codex 스킬**. | `skills add dandacompany/dante-skills@gpt-model-effort-advisor -a codex` |

### 🎓 Hermes 강의 실습용

| 스킬                              | 설명                                                                                                                                                            | 설치                                                            |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [magma-support](./magma-support/) | MAGMA 고객지원 1차 응대 지식(샘플). 고객 문의를 정책 기반으로 분류·1차 답변 초안 작성, 불확실한 건 담당자 확인 필요로 표시. 헤르메스 강의 4.1 웹훅 실습 준비물. | `hermes skills install dandacompany/dante-skills/magma-support` |

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

### 📈 price-positioning

수집된 가격 관측치(브랜드·품목·가격·출처)로부터 **가격 포지셔닝 맵**과 **빈 가격대(화이트스페이스)** 를 결정론적으로 도출하는 분석 패턴. "수집물 → 분석" 계열이라 **수집 도구에 종속되지 않는다** — 웹 수집 MCP·검색 API·사내 시트·수기 입력 무엇으로 모았든 동일하게 동작하고, 어떤 시장·통화에도 쓸 수 있다.

- 입력: 정규화 관측치(CSV/JSON)
- 처리: stdlib 전용 결정론 분석기(`scripts/positioning.py`) — 밴드별 통계·화이트스페이스·이상치·플래그. 같은 입력이면 항상 같은 출력. 네트워크·환경변수·외부 실행 없음.
- 출력: `positioning.json`(고정 스키마) + `pricing-landscape.md`(고정 섹션)

```bash
skills add dandacompany/dante-skills@price-positioning -g -y --copy -a claude-code
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

### 📚 oh-my-wiki

Karpathy "LLM Wiki" 워크플로의 Claude Code 구현. 이 repo의 항목은 **설치 안내용 포인터**이고, 실제 스킬·훅·커맨드는 별도 플러그인 마켓플레이스로 배포됩니다.

```
/plugin marketplace add dandacompany/oh-my-wiki
/plugin install oh-my-wiki@oh-my-wiki-marketplace
```

소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트(sqlite) · autoresearch · 팩트체크/일관성/용어집 · 스웜 병렬 디스패치 포함. 전체 문서: **[github.com/dandacompany/oh-my-wiki](https://github.com/dandacompany/oh-my-wiki)**

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
