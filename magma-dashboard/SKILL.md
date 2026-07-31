---
name: magma-dashboard
description: "MAGMA 가상 오피스 강의(섹션 7.4)용 Evidence.dev 대시보드 제작 스킬. Supabase 정제 뷰를 읽어 Markdown+SQL 페이지로 판매 대시보드를 만들고 정적 빌드로 배포한다. 소스 연결(CA 인증서 포함), 컴포넌트 8종 사용법, 만든 뒤 총계를 원본과 대조하는 검산 절차까지 포함. Use when: '대시보드 만들어', 'Evidence 페이지 작성', '판매 대시보드 제작', 'magma-dashboard 실행', or building the Section 7.4 BI dashboard."
user-invocable: true
license: MIT
metadata:
  author: dante
  version: "1.0.0"
---

# magma-dashboard — Evidence.dev 판매 대시보드 제작

## 목적

인프런 「Hermes × Codex 가상 오피스」 섹션 7.4(BI 대시보드 제작)의 작업 스킬.
Supabase에 준비된 정제 뷰를 Evidence.dev 프로젝트로 읽어 **한 장의 Markdown+SQL 페이지**로 대시보드를 만들고, 정적 빌드로 배포한다.
차트를 만드는 것으로 끝내지 않는다 — **만든 숫자가 원본과 맞는지 검산해 보고하는 것까지가 이 스킬의 절차다.**

## 전제

- Evidence 프로젝트가 이미 스캐폴드돼 있다(`npx degit evidence-dev/template <폴더>` + `npm install`). 없으면 먼저 만들 것을 사용자에게 안내한다.
- node 18 이상.
- 데이터 원천은 Supabase의 뷰(`v_sales` 등). 뷰가 없으면 대시보드를 만들지 말고 멈춰서 보고한다.

## 절차

1. **소스 연결.** `sources/magma/connection.yaml`을 만든다.

   ```yaml
   name: magma
   type: postgres
   options:
     host: aws-1-ap-northeast-2.pooler.supabase.com
     port: 5432
     database: postgres
     ssl:
       sslmode: require
   ```

   접속 정보는 프로젝트 루트 `.env`에만 둔다(값을 화면·파일·보고에 노출하지 않는다).

   ```
   EVIDENCE_SOURCE__magma__user=postgres.프로젝트ref
   EVIDENCE_SOURCE__magma__password=(DB 비밀번호)
   ```

2. **CA 인증서.** Supabase 풀러는 자체 서명 계열 인증서라 그냥 연결하면 `self-signed certificate in certificate chain` 오류가 난다. **인증서 검증을 끄지 않는다** (`rejectUnauthorized: false` 금지 — 중간자 공격 방어를 끄는 설정이다). 대신 Supabase 공식 CA를 받아 신뢰 목록에 추가한다.

   ```bash
   curl -sL "https://supabase-downloads.s3.ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt" -o prod-ca-2021.crt
   # 이후 모든 evidence 명령 앞에:
   NODE_EXTRA_CA_CERTS=./prod-ca-2021.crt npm run sources
   ```

   (같은 파일을 Supabase 대시보드의 Database Settings, SSL 항목에서도 받을 수 있다.)

3. **소스 정의와 적재.** `sources/magma/sales.sql`에 `select * from v_sales` 한 줄. `npm run sources`로 적재하고 **적재 행 수를 기록**한다.

4. **페이지 작성.** `pages/index.md`에 대시보드를 만든다. 컴포넌트 사용법은 `references/components.md`를 따른다. 기본 구성 순서:
   - KPI 4개 (총매출·주문 수·구매 고객 수·평균 주문금액)
   - 시간 추이 (월별 매출 라인)
   - 구성비 (월별 채널 스택막대 + 채널 도넛)
   - 순위 (카테고리·지역 가로막대)
   - 패턴 (요일과 시간대 히트맵)
   - 상세 (상품별 실적 표 — 매출·수량·마진율)

5. **검산 (필수 — 생략 금지).** 페이지가 렌더되면 다음을 원본에 직접 조회해 화면 값과 대조하고, **대조표를 사용자에게 보고**한다.
   - 총매출·주문 수·고객 수가 `v_sales` 직접 집계와 일치하는가
   - 구성비 차트의 합이 총계와 같은가 (필터가 행을 조용히 버리면 여기서 어긋난다)
   - 표에서 자릿수가 튀는 값·비율 100%에 붙는 값이 있으면 **정제 문제일 수 있다고 짚어서 보고**한다. 임의로 고치지 않는다 — 버릴지 살릴지는 사용자가 정한다.

6. **빌드·배포 (요청 시).** `NODE_EXTRA_CA_CERTS=./prod-ca-2021.crt npm run build` → `build/` 정적 산출물. Vercel 배포는 사용자 확인 후 진행하고, **프로젝트 이름을 명시**한다(생략하면 폴더명이 프로젝트명이 된다).

## 규칙

- DB 접속 정보는 `.env`에만. 값을 채팅·보고·커밋에 노출하지 않는다.
- 인증서 검증을 끄는 어떤 설정도 쓰지 않는다.
- 필터 기본값으로 `like '%'` 패턴을 쓰지 않는다 — **NULL 행을 조용히 버린다** (실측: 카테고리 빈 825행이 빠져 총매출이 15% 줄었다). 전체 선택은 where 절 생략이나 명시적 분기로 처리한다.
- 원화 축은 억 단위로 축약해 표기한다(`fmt` 지정) — 원 단위 그대로면 축 라벨이 겹친다.
- 검산 없이 "완성했습니다"라고 보고하지 않는다.

## 함정 (실측 2026-08-01)

| 증상 | 원인 | 처리 |
| --- | --- | --- |
| `self-signed certificate in certificate chain` | Supabase 풀러의 자체 CA | 절차 2의 CA 추가. 검증 끄기 금지 |
| 총매출이 DB보다 작다 | `like '%'` 필터가 NULL 행 제외 | 규칙의 필터 원칙 적용 |
| 표 상위 몇 개만 마진율 99% 급 | 원본 단가 이상치가 정제를 통과 | 고치지 말고 짚어서 보고 — 정제 기준은 사용자가 결정 |
| 히트맵 0시만 비정상적으로 큼 | 시각 없는 날짜가 자정으로 파싱됨 | 데이터 유래를 함께 보고 |
| 뷰 컬럼을 바꿨는데 화면이 그대로 | Evidence는 소스 캐시를 자동 갱신 안 함 | `npm run sources` 재실행 |
| 도넛 차트 컴포넌트가 없음 | Evidence 미제공 | `references/components.md`의 ECharts 도넛 스니펫 사용 |

## 산출물

- `pages/index.md` 대시보드 페이지
- 검산 대조표 (화면 값 대 원본 집계)
- (배포 시) `build/` 정적 산출물과 공개 URL
