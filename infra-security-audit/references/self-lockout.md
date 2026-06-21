# 자기 잠금(self-lockout) 방지 — 3대 함정

방화벽·SSH 변경은 잘못하면 운영자 자신이 서버에서 영구히 잠긴다. 표준 감사 도구가 약한 지점이자 이 스킬의 핵심 안전 요건. RED/YELLOW 변경 전 반드시 적용한다.

## 함정 1 — `ufw enable` 자기 차단

ufw를 켜는 순간 허용 규칙에 없는 포트는 즉시 차단된다. SSH가 빠지면 그대로 잠긴다.

방어:
1. enable **전에** `ufw allow OpenSSH`(또는 실제 SSH 포트)와 Tailscale 대역을 먼저 넣는다.
2. 현재 규칙에 SSH 허용이 있는지 선검증 후 diff 제시.
3. 승인받고 `ufw --force enable`.

## 함정 2 — sshd 변경 후 잠금

`PasswordAuthentication no`를 키가 배치 안 된 상태에서 켜거나, 오타·잘못된 지시문이 있으면 다음 접속부터 잠긴다.

방어 절차(순서 엄수):
1. **키 로그인이 실제로 되는지 먼저 확인**(현재 세션이 키 기반인지).
2. 변경은 메인 파일이 아니라 **drop-in**(`/etc/ssh/sshd_config.d/00-hardening.conf`)으로.
3. `sshd -t` 문법 검사.
4. `systemctl reload ssh`(restart 아님 — reload는 기존 세션 유지).
5. **현재 세션을 끊지 말고 새 터미널로 재로그인이 되는지 확인**한 뒤에만 확정.
6. 실패하면 즉시 drop-in 삭제 후 reload로 롤백.
7. `PermitRootLogin`은 `no`가 아니라 `prohibit-password`(키 허용)로 — root 키 접속만 쓰는 환경에서 `no`로 하면 잠긴다.

## 함정 3 — SSH drop-in 우선순위(first-match)

`/etc/ssh/sshd_config.d/*.conf`는 이름 번호 순으로 로드되고 sshd는 **먼저 읽은 값이 우선**이다. Ubuntu는 `50-cloud-init.conf`에 `PasswordAuthentication yes`를 박아둔다. 그래서 `99-hardening.conf`로 만들면 `50-`이 이겨 안 꺼진다.

방어:
- 하드닝 drop-in은 **더 낮은 번호**(`00-hardening.conf`)로 만들어 먼저 읽히게 한다.
- 변경 후 반드시 **실효값**을 `sshd -T`로 확인(파일에 썼다고 적용된 게 아니다).
- `Include` 지시문 위치도 본다(메인 파일의 Include가 drop-in보다 뒤면 메인 값이 이긴다).

## SSH 포트 변경(추가)

포트를 바꾸고 재시작하면 옛 포트로 접속하던 세션·자동화가 끊긴다. 변경 시 신포트가 실제로 열렸는지 새 세션으로 확인하기 전에는 옛 포트(22) 허용을 유지하고, 확인 후 제거한다.

## 공통 원칙

- 변경 전 대상 파일 백업: `cp <file> <file>.bak.<timestamp>`.
- 되돌리기 어려운 변경은 롤백 타이머(예: 5분 뒤 자동 원복 예약)를 걸고, 사람이 "유지" 확인하면 타이머 해제.
- 점검 결과가 비거나 모호하면 변경하지 말고 사람에게 보고.
