# 점검 출력 해석

각 명령의 출력을 입문자에게 평어로 옮길 때의 기준.

## `sshd -T | grep ...`

실효 설정(파일이 아니라 실제 적용값)을 본다.

- `permitrootlogin yes` → [즉시] root 직접 로그인 열림. `prohibit-password`(키만) 또는 `no`로.
- `permitrootlogin prohibit-password` / `no` → 통과.
- `passwordauthentication yes` → [즉시] 비번 무차별 대입 노출. 키 배치 후 `no`로(self-lockout 절차).
- `passwordauthentication no` → 통과.

> 파일에 썼는데 실효값이 다르면 drop-in 우선순위 함정(self-lockout.md 함정 3).

## `ss -tlnH`

리스닝 소켓의 로컬 주소를 본다.

- `0.0.0.0:PORT` 또는 `*:PORT` → 모든 인터페이스 노출. SSH(22)·웹(80/443) 외에 DB(5432·3306·6379)·대시보드가 0.0.0.0이면 [즉시]. 127.0.0.1 또는 Tailscale(100.x)에만 묶여야.
- `127.0.0.1:PORT` → 로컬 전용, 안전.

## `ufw status verbose`

- `Status: inactive` → [즉시] 방화벽 꺼짐.
- `Default: deny (incoming)` 없음 → [즉시] 기본 차단 아님.
- active + deny incoming + 22/80/443만 ALLOW → 통과.

## `fail2ban-client status sshd`

- 명령 자체 실패(미설치) → [권장] 침입 자동 차단 없음.
- `Currently banned: N` → 동작 중. N은 시점에 따라 0일 수 있음(키 전용이면 비번 실패가 안 쌓임 — 정상).
- backend가 systemd면 `/var/log/auth.log`가 비어도 정상(journald를 읽음).

## `dpkg -l unattended-upgrades`

- `ii` 없음 → [권장] 자동 보안 업데이트 없음.
- 설치됨 → 통과(보안 origin 활성 여부까지 보면 더 정확).

## Lynis (있으면)

- `Hardening index: NN` → 0~100 점수. 신선한 Ubuntu가 50~60대. "올려가는 게임"으로 제시.
- `WARNINGS` → [즉시] 후보, `SUGGESTIONS` → [권장] 후보. 우리 스코프(SSH·방화벽·네트워크)만 필터.
- 근거는 `lynis show details <TEST-ID>`.

## ssh-audit (있으면)

- 알고리즘별 `fail`(빨강)=제거 권장, `warn`=주의, `ok`. Terrapin(CVE-2023-48795) 표시.
- 출력이 "이 줄을 빼라" 식으로 구체적 — 그대로 sshd 하드닝 제안에 옮긴다.

## Cloudflare / Tailscale (특화)

- `dig +short <도메인>`이 원본 IP를 반환 → proxied 아님(원본 노출, 우회 가능). Cloudflare IP(104.x·172.67.x) 반환 → 가려짐.
- `tailscale status`로 사설망 연결 확인. 관리·내부 서비스가 공인 IP로도 닿으면 [권장] Tailscale 전용으로.

## 점수 산정(간이)

P1 항목 각 20점, P2 각 10점, P3 각 5점 만점 기준으로 통과 비율을 0~100으로 환산. 절대값보다 **재실행 시 전/후 비교**(점수가 올랐다)가 입문자 동기부여에 효과적.
