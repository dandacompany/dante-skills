---
name: oh-my-wiki
description: Karpathy 스타일 LLM 위키 스킬 oh-my-wiki(omw) 의 설치 안내. 소스를 수집(ingest)해 구조화된 위키를 만들고, 인용(citation)이 달린 답변으로 질의(query)한다. 멀티 볼트 sqlite 레지스트리, 메모 볼트, autoresearch, 팩트체크·일관성 검사, 용어집(glossary), 스웜(swarm) 병렬 디스패치를 포함한다. Claude Code 플러그인 마켓플레이스로 배포되며, 이 스킬은 정식 설치 경로를 안내하는 포인터다.
---

# oh-my-wiki

> Karpathy "LLM Wiki" 워크플로의 Claude Code 구현. 메모는 썩지만 위키는 복리로 쌓인다. 이 스킬은 **설치 안내용 포인터**이며, 실제 기능은 플러그인 마켓플레이스로 설치한다.

## 설치 (Claude Code 플러그인 마켓플레이스)

Claude Code 세션에서:

```
/plugin marketplace add dandacompany/oh-my-wiki
/plugin install oh-my-wiki@oh-my-wiki-marketplace
```

이 한 번으로 스킬 · 훅 · 커맨드가 모두 연결된다. 마켓플레이스 install 은 항상 최신 릴리스를 받는다(별도 버전 고정 없음). 업데이트는:

```
/plugin marketplace update oh-my-wiki-marketplace
```

## 무엇을 하나

소스를 넣으면 `raw/` 스냅샷, `wiki/summaries/` 페이지, 엔티티·개념 페이지로 분해해 구조화된 위키를 만든다. 질의하면 평평한 파일 더미가 아니라 이 구조에서 끌어와 **특정 페이지를 인용**해 답한다. 질의 과정에서 생긴 새 종합이 다시 위키로 파일링되어 루프가 닫힌다.

멀티 볼트(sqlite 레지스트리) · 메모 볼트 CRUD · autoresearch · 팩트체크/일관성/용어집 페르소나 · 스웜 병렬 디스패치까지 v2.5 기준으로 제공한다.

## 전체 문서 · 트리거 · 튜토리얼

정식 트리거 문구, 운영 가이드, 한국어/영어 튜토리얼은 upstream 저장소에서:

**https://github.com/dandacompany/oh-my-wiki**
