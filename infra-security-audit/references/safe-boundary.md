# 자동적용 vs 사람승인 경계 (GREEN / YELLOW / RED)

판단 기준 한 줄: **(a) 네트워크 도달성을 끊는가, (b) 현재 세션을 잠그는가, (c) 서비스를 멈추는가.** 셋 중 하나라도 yes면 자동 금지(YELLOW 이상).

## GREEN — 비파괴, 자동적용 OK

| 조치 | 왜 안전한가 |
| --- | --- |
| 점검·진단·리포트 일체 | 읽기만 함 (audit 모드 전부) |
| fail2ban 설치 + sshd jail 활성 | 악성 IP만 밴. **단 `ignoreip`에 현재 SSH 클라이언트 IP·Tailscale 대역(100.64.0.0/10)을 먼저 넣어 자기밴 방지** |
| unattended-upgrades 설치·활성 | 보안 패치 활성. 접속·서비스 안 끊음 (자동 재부팅 옵션만은 RED) |
| Caddy `rate_limit` 추가 | `caddy validate` 통과 + `reload`(restart 아님)로 한정하면 SSH·접속 안 끊김 |
| fail2ban/Cloudflare에 운영자 IP allowlist 추가 | 차단 완화 방향이라 잠금 위험 없음 |

## YELLOW — 가역, 승인 필요

| 조치 | 위험 | 안전장치 |
| --- | --- | --- |
| sshd 하드닝 (root·password·약한 알고리즘) | 오타·drop-in 충돌·키 미배치 상태에서 password 끄면 잠금 | 키 로그인 사전검증 → drop-in으로 변경 → `sshd -t` → 새 세션 재로그인 확인 후 커밋 (self-lockout.md) |
| sysctl 네트워크 파라미터 | 대개 안전하나 rp_filter·forwarding이 Tailscale/Docker 라우팅과 충돌 가능 | Tailscale/Docker 호스트면 forwarding류는 RED 취급 |

## RED — 되돌리기 어려움, 하드 게이트 + 백업 강제

| 조치 | 위험 | 안전장치 |
| --- | --- | --- |
| `ufw enable` | 규칙 누락 시 즉시 자기 SSH 차단 | enable 전 SSH·Tailscale allow 선검증, diff 제시, 승인 |
| SSH 포트 변경 | 재시작 후 옛 포트 접속 시도로 단절(멱등성 함정) | fallback: 신포트 불통 시 22 유지 |
| 포트 0.0.0.0 → loopback/Tailscale 바인딩 | 정상 접근 경로까지 끊을 수 있음 | 어떤 클라이언트가 쓰는지 확인 후 승인 |
| CrowdSec 전환 / 공격적 밴 정책 | 오탐 시 정상 사용자 차단 | 입문자는 fail2ban 유지, 전환은 옵트인 |
| unattended-upgrades 자동 재부팅 | 서비스 중단 타이밍 | 시간창 지정 + 승인 |

## 규칙

- "fix everything" 요청이어도 **RED는 자동 실행 금지** — 항상 diff + 백업 + 명시 확인.
- 모든 비-GREEN 변경은 **diff/명령 미리보기 먼저**(plan), 그 다음 승인.
- 변경 전 대상 파일 백업(`<file>.bak.<timestamp>`), 1-커맨드 롤백 경로 확보.
