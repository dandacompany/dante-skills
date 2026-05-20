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

| 스킬 | 설명 | 설치 |
|------|------|------|
| [dream](./dream/) | 프로젝트 메모리 정리 및 최적화. 메모리 파일 중복·충돌·오래된 항목을 정리하고 인덱스를 재구성합니다. | `skills add dandacompany/dante-skills@dream` |
| [brand-research-glossary](./brand-research-glossary/) | B2C 브랜드 시장조사 표기·용어 사전 (무신사·29CM 등 한국 e-커머스, Bright Data 제품명, 슬라이드 형식, 금지 표현). Brand Intelligence Lab 회사 공통. | `skills add dandacompany/dante-skills@brand-research-glossary` |
| [swot-from-signals](./swot-from-signals/) | 정성·정량 신호로부터 SWOT 4사분면을 자동 도출하는 분석 패턴. 각 칸 3개씩 근거 URL/시그널값 명시. 데이터 분석가 전용. | `skills add dandacompany/dante-skills@swot-from-signals` |
| [marp-slide-build](./marp-slide-build/) | Marp 마크다운으로 임원 보고용 시장조사 슬라이드 12~15장 빌드. 단테랩스 paper+ink+rust 디자인 가드 강제. 슬라이드 제작자 전용. | `skills add dandacompany/dante-skills@marp-slide-build` |
| [report-evidence-citation](./report-evidence-citation/) | 모든 산출물에서 사실/의견 분리 + 출처 URL 보존 + 평가성 어휘 차단. 회사 공통 게이트. | `skills add dandacompany/dante-skills@report-evidence-citation` |

## Paperclip 회사 레벨 등록 (GitHub URL 한 줄)

Paperclip 콘솔 → **Company → Skills Library → `+ Add Skill`** 폼에 아래 GitHub URL을 그대로 붙여넣으면 자동 import 됩니다 (Paste path, GitHub URL, or skills.).

```
https://github.com/dandacompany/dante-skills/tree/main/brand-research-glossary
https://github.com/dandacompany/dante-skills/tree/main/swot-from-signals
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
