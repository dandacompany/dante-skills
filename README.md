# dante-skills

> Claude Code / Claude AI용 에이전트 스킬 모음 by [단테(Dante)](https://dante-labs.com)

[![skills.sh](https://img.shields.io/badge/skills.sh-dante--skills-blue)](https://skills.sh/dandacompany/dante-skills)

## 설치 방법

```bash
# 특정 스킬 설치 (글로벌)
skills add dandacompany/dante-skills@<skill-name> -g -y --copy -a claude-code

# 전체 스킬 설치
skills add dandacompany/dante-skills -g -y --copy -a claude-code
```

## 스킬 목록

| 스킬                                                    | 설명                                                                                                                                                                                                                                                                                  | 설치                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [dream](./dream/)                                       | 프로젝트 메모리 정리 및 최적화. 메모리 파일 중복·충돌·오래된 항목을 정리하고 인덱스를 재구성합니다.                                                                                                                                                                                   | `skills add dandacompany/dante-skills@dream`                    |
| [brand-research-glossary](./brand-research-glossary/)   | B2C 브랜드 시장조사 표기·용어 사전 (무신사·29CM 등 한국 e-커머스, Bright Data 제품명, 슬라이드 형식, 금지 표현). Brand Intelligence Lab 회사 공통.                                                                                                                                    | `skills add dandacompany/dante-skills@brand-research-glossary`  |
| [swot-from-signals](./swot-from-signals/)               | 정성·정량 신호로부터 SWOT 4사분면을 자동 도출하는 분석 패턴. 각 칸 3개씩 근거 URL/시그널값 명시. 데이터 분석가 전용.                                                                                                                                                                  | `skills add dandacompany/dante-skills@swot-from-signals`        |
| [price-positioning](./price-positioning/)               | 수집된 가격 관측치로 시장 가격 포지셔닝 맵과 빈 가격대(화이트스페이스)를 결정론적으로 도출. 수집 도구 비종속(어떤 시장·통화도) + stdlib 결정론 분석기 동봉. 데이터 분석가용.                                                                                                          | `skills add dandacompany/dante-skills@price-positioning`        |
| [marp-slide-build](./marp-slide-build/)                 | Marp 마크다운으로 임원 보고용 시장조사 슬라이드 12~15장 빌드. 단테랩스 paper+ink+rust 디자인 가드 강제. 슬라이드 제작자 전용.                                                                                                                                                         | `skills add dandacompany/dante-skills@marp-slide-build`         |
| [report-evidence-citation](./report-evidence-citation/) | 모든 산출물에서 사실/의견 분리 + 출처 URL 보존 + 평가성 어휘 차단. 회사 공통 게이트.                                                                                                                                                                                                  | `skills add dandacompany/dante-skills@report-evidence-citation` |
| [brightdata-guide](./brightdata-guide/)                 | Bright Data 웹 수집 가이드(MCP **+ CLI** 통합). MCP 도구가 있으면 MCP를, 없으면(예: delegate 서브에이전트 — MCP 미상속, 터미널·스킬은 상속) 터미널의 `bdata`/`brightdata` CLI로 검색·스크랩·구조화 추출. 헤르메스·Codex 등 범용. 보안 패치(설정 자동편집·curl-to-bash·전역설치 제거). | `skills add dandacompany/dante-skills@brightdata-guide`         |
| [oh-my-wiki](./oh-my-wiki/)                             | Karpathy 스타일 LLM 위키 스킬(omw) 설치 안내. 소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트·autoresearch·팩트체크·스웜 포함. 실제 설치는 플러그인 마켓플레이스.                                                                                                              | `/plugin install oh-my-wiki@oh-my-wiki-marketplace`             |
| [brand-logo](./brand-logo/)                             | 브랜드 로고 컨셉 디렉팅 패턴. 브리프 → 심볼 컨셉 → 이미지 프롬프트 → 생성 → 벡터화 인계의 로고 디렉터 워크플로. 모델 글자 약점 회피(추상·모노그램 우선), DESIGN.md 브랜드 토큰 고정, 강한 네거티브·평가 체크리스트. 디자이너용.                                                       | `skills add dandacompany/dante-skills@brand-logo`               |
| [magma-support](./magma-support/)                       | MAGMA 고객지원 1차 응대 지식(샘플). 고객 문의를 정책 기반으로 분류·1차 답변 초안 작성, 확실하지 않은 건 담당자 확인 필요로 표시. 웹훅 구독에서 로드해 외부 문의에 대응. 헤르메스 강의 4.1 웹훅 실습 사전 준비물.                                                                      | `hermes skills install dandacompany/dante-skills/magma-support` |
| [tally-api](./tally-api/)                               | Tally.so 폼 플랫폼 REST API·웹훅 연동. 폼·제출(submission)·분석·워크스페이스·조직 사용자 조회 및 웹훅 생성/서명검증. curl CLI 래퍼(`tally.sh`) + HMAC-SHA256 서명 검증 스크립트 동봉. Tally 폼 데이터 추출·실시간 제출 처리에 사용.                                                   | `skills add dandacompany/dante-skills@tally-api`                |

## Paperclip 회사 레벨 등록 (GitHub URL 한 줄)

Paperclip 콘솔 → **Company → Skills Library → `+ Add Skill`** 폼에 아래 GitHub URL을 그대로 붙여넣으면 자동 import 됩니다 (Paste path, GitHub URL, or skills.).

```
https://github.com/dandacompany/dante-skills/tree/main/brand-research-glossary
https://github.com/dandacompany/dante-skills/tree/main/swot-from-signals
https://github.com/dandacompany/dante-skills/tree/main/price-positioning
https://github.com/dandacompany/dante-skills/tree/main/marp-slide-build
https://github.com/dandacompany/dante-skills/tree/main/report-evidence-citation
```

자세한 회사 시나리오는 단테랩스 YouTube #23 영상 가이드 참조.

## 스킬 상세

### 🌙 dream

메모리 통합 및 최적화 스킬. 뇌가 수면 중 기억을 통합하듯, 오래된 메모리를 정리하고 신호를 강화합니다.

**사용 시점:**

- 여러 세션 이후 메모리 파일이 쌓였을 때
- 삭제된 코드나 변경된 파일을 참조하는 메모리가 있을 때
- MEMORY.md 인덱스가 실제 파일과 맞지 않을 때
- 사용자가 명시적으로 메모리 최적화를 요청할 때

```bash
skills add dandacompany/dante-skills@dream -g -y --copy -a claude-code
```

### 🏢 Brand Intelligence Lab — 4종 스킬 묶음

YouTube #23 영상 "Paperclip × Bright Data 멀티에이전트 브랜드 시장조사" 시나리오에서 사용되는 회사 공통 + 직무별 스킬 묶음. 무신사 · 29CM 예시.

- `brand-research-glossary` (회사 공통) — 표기·용어 일관성
- `swot-from-signals` (데이터 분석가) — SWOT 자동 도출
- `marp-slide-build` (슬라이드 제작자) — 임원 보고용 슬라이드 빌드 + 디자인 가드
- `report-evidence-citation` (회사 공통) — 사실/의견 분리 + 인용 보존

### 📈 price-positioning

수집된 가격 관측치(브랜드·품목·가격·출처)로부터 **가격 포지셔닝 맵**과 **빈 가격대(화이트스페이스)** 를 결정론적으로 도출하는 분석 패턴. `swot-from-signals`와 같은 "수집물 → 분석" 계열이라 **수집 도구에 종속되지 않는다** — 웹 수집 MCP·검색 API·사내 시트·수기 입력 무엇으로 모았든 동일하게 동작하고, 어떤 시장·통화에도 쓸 수 있다.

- 입력: 정규화 관측치(CSV/JSON). 여러 일꾼에게 가격대를 나눠 맡길 때 쓸 "수집 계약" 문구 포함.
- 처리: stdlib 전용 결정론 분석기(`scripts/positioning.py`) — 밴드별 통계·화이트스페이스·이상치·플래그. 같은 입력이면 항상 같은 출력. 네트워크·환경변수·외부 실행 없음.
- 출력: `positioning.json`(고정 스키마) + `pricing-landscape.md`(고정 섹션). 진입 가격대 권고는 분석가가 근거·확신도와 함께 덧붙임.

```bash
skills add dandacompany/dante-skills@price-positioning -g -y --copy -a claude-code
```

### 📚 oh-my-wiki

Karpathy "LLM Wiki" 워크플로의 Claude Code 구현. 이 repo 의 항목은 **설치 안내용 포인터**이고, 실제 스킬·훅·커맨드는 별도 플러그인 마켓플레이스로 배포된다.

```
/plugin marketplace add dandacompany/oh-my-wiki
/plugin install oh-my-wiki@oh-my-wiki-marketplace
```

소스 ingest → 구조화 위키 → 인용 달린 query. 멀티 볼트(sqlite) · autoresearch · 팩트체크/일관성/용어집 · 스웜 병렬 디스패치 포함. 전체 문서: **[github.com/dandacompany/oh-my-wiki](https://github.com/dandacompany/oh-my-wiki)**

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
