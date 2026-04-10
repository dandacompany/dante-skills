# dante-skills

> Claude Code / Claude AI용 에이전트 스킬 모음 by [단테(Dante)](https://dante-labs.com)

[![skills.sh](https://img.shields.io/badge/skills.sh-dante--skills-blue)](https://skills.sh/dante/dante-skills)

## 설치 방법

```bash
# 특정 스킬 설치 (글로벌)
skills add dante/dante-skills@<skill-name> -g -y --copy -a claude-code

# 전체 스킬 설치
skills add dante/dante-skills -g -y --copy -a claude-code
```

## 스킬 목록

| 스킬 | 설명 | 설치 |
|------|------|------|
| [dream](./dream/) | 프로젝트 메모리 정리 및 최적화. 메모리 파일 중복·충돌·오래된 항목을 정리하고 인덱스를 재구성합니다. | `skills add dante/dante-skills@dream` |

## 스킬 상세

### 🌙 dream

메모리 통합 및 최적화 스킬. 뇌가 수면 중 기억을 통합하듯, 오래된 메모리를 정리하고 신호를 강화합니다.

**사용 시점:**
- 여러 세션 이후 메모리 파일이 쌓였을 때
- 삭제된 코드나 변경된 파일을 참조하는 메모리가 있을 때
- MEMORY.md 인덱스가 실제 파일과 맞지 않을 때
- 사용자가 명시적으로 메모리 최적화를 요청할 때

```bash
skills add dante/dante-skills@dream -g -y --copy -a claude-code
```

---

## 기여 / 문의

- **YouTube**: [@dante-labs](https://youtube.com/@dante-labs)
- **Discord**: [Dante Labs Community](https://discord.com/invite/rXyy5e9ujs)
- **Email**: dante@dante-labs.com
