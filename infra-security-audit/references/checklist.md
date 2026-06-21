# 점검 항목 마스터 리스트 (scoped)

이 스킬이 점검하는 항목. 우선순위 P1(치명·필수) → P2(중요) → P3(권장). 표준 도구(Lynis·CIS·dev-sec·ssh-audit) 교집합 + 셀프호스팅 특화 항목.

| # | 우선 | 점검 | 무엇을 보는가 | 점검 방법 |
| --- | --- | --- | --- | --- |
| 1 | P1 | SSH root 로그인 | `PermitRootLogin` 가 `no` 또는 `prohibit-password` | `sshd -T \| grep permitrootlogin` |
| 2 | P1 | SSH 비밀번호 인증 | `PasswordAuthentication no`, `PubkeyAuthentication yes` | `sshd -T \| grep -E 'passwordauthentication\|pubkey'` |
| 3 | P1 | 노출 포트 / 0.0.0.0 바인딩 | 외부에 열린 리스닝 소켓. 앱 포트(DB·대시보드)가 0.0.0.0인지 127.0.0.1/Tailscale인지 | `ss -tlnH` |
| 4 | P1 | ufw 기본 정책 | `default deny incoming` | `ufw status verbose` |
| 5 | P1 | ufw 활성 | 방화벽이 실제 active | `ufw status` |
| 6 | P2 | SSH 약한 알고리즘·Terrapin | 취약 cipher/MAC/kex 제거 (CVE-2023-48795) | `ssh-audit localhost` (있으면) |
| 7 | P2 | SSH drop-in 우선순위 함정 | `/etc/ssh/sshd_config.d/*.conf` 와 메인 충돌. 앞 번호가 first-match로 이김 | 파일 번호·`Include` 위치 + `sshd -T` 실효값 대조 |
| 8 | P2 | fail2ban(또는 CrowdSec) | 설치 + sshd jail 활성 | `fail2ban-client status sshd` |
| 9 | P2 | unattended-upgrades | 설치 + 보안 origin 활성 | `dpkg -l unattended-upgrades` |
| 10 | P2 | Cloudflare origin 보호 | 도메인 proxied 여부, origin IP 직접 노출로 우회 가능한지 | DNS 조회 + 노출포트 대조 (특화) |
| 11 | P3 | Caddy rate limit | `rate_limit` 핸들러 존재 + proxied 환경에서 실제 client IP 기준인지(CF IP로 뭉개지면 무력) | Caddyfile 검사 (특화) |
| 12 | P3 | Tailscale 사설망 경계 | 관리·내부 서비스가 공인 IP 아닌 100.x로만 접근되는지 | `tailscale status` + 노출포트 대조 (특화) |
| 13 | P3 | sysctl 네트워크 하드닝 | IP spoof 방지·redirect 거부·source route 차단 | `sysctl` 키 확인 (Tailscale/Docker 충돌 주의) |
| 14 | P3 | SSH 추가 하드닝 | `PermitEmptyPasswords no`·`MaxAuthTries`·`LoginGraceTime` | `sshd -T` |

## 점검 엔진 — 바퀴 재발명 금지

- **Lynis** 가 설치돼 있으면 `lynis audit system` 결과(hardening index·warnings)를 파싱해 위 스코프 항목만 필터·재라벨. read-only.
- **ssh-audit** 가 있으면 #6을 위임. 둘 다 read-only·입문자 친화 표준.
- 없으면 표의 "점검 방법" 직접 실행으로 폴백.

## 특화 항목(표준 도구가 못 보는 것)

#10·#11·#12는 일반 감사 도구가 점검하지 않는 셀프호스팅 운영 특화 점검이다. 이 스킬의 차별점이므로 반드시 포함한다.
