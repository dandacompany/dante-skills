# 교정 명령 (dogfood 검증본)

Ubuntu 24.04 LTS 백지 VPS에서 실측 확정한 명령. 라이브 변경은 데모/대상 서버에서만, 위험 항목은 safe-boundary.md의 승인 절차를 거친다.

## ufw 방화벽 (RED — `ufw enable` 자기잠금)

```bash
ufw allow OpenSSH          # 켜기 전에 SSH부터 허용 (안 하면 자기 잠금)
ufw allow 80,443/tcp
ufw default deny incoming
ufw default allow outgoing
ufw --force enable         # 대화형 프롬프트 건너뜀 (SSH 이미 허용했으니 안전)
ufw status verbose         # 확인: Status: active, deny (incoming)
```

Tailscale 사용 시 사설 대역도 허용: `ufw allow in on tailscale0`.

## SSH 하드닝 (YELLOW) — drop-in 우선순위 함정 주의

```bash
# ⚠️ Ubuntu는 50-cloud-init.conf 에 PasswordAuthentication yes 를 박아두고
#    sshd 는 "먼저 읽은 값이 우선(first-match)"이라, 하드닝 파일은 더 낮은 번호(00-)로 만들어야 이긴다.
printf 'PasswordAuthentication no\nPermitRootLogin prohibit-password\n' > /etc/ssh/sshd_config.d/00-hardening.conf
sshd -t && systemctl reload ssh
sshd -T | grep -E 'permitrootlogin|passwordauthentication'   # no · prohibit-password 확인
```

`prohibit-password` = 키 허용·비번 금지라 키 접속이면 reload 후에도 안 잠긴다. 적용 전 키 로그인이 되는지 반드시 사전 확인.

## fail2ban (GREEN)

```bash
apt install -y fail2ban        # 설치만 하면 sshd jail 이 기본으로 켜진다 (backend auto = systemd/journald)
fail2ban-client status sshd    # 차단된 주소 목록
# 자기밴 방지: 운영자 IP·Tailscale 대역을 ignoreip 에
#   /etc/fail2ban/jail.local 에  ignoreip = 127.0.0.1/8 100.64.0.0/10 <운영자IP>
```

차단 동작 시연(문서용 예약 IP, 안전): `fail2ban-client set sshd banip 203.0.113.10` → `status sshd` → `unbanip 203.0.113.10`.

> 키 전용 SSH면 비번 실패가 안 쌓여 fail2ban이 잡을 게 줄어든다. fail2ban의 진가는 비번이 열린 서비스(웹 로그인 등). SSH는 키 잠금이 더 근본적 — 둘은 같이 쓴다.

## Caddy rate limit (GREEN — reload 한정)

기본 Caddy엔 rate limit이 없다. `xcaddy` 로 모듈을 넣어 빌드해야 한다(자료실 가이드).

```bash
xcaddy build --with github.com/mholt/caddy-ratelimit
caddy list-modules | grep rate_limit    # http.handlers.rate_limit 포함 확인
```

Caddyfile:

```caddyfile
rate_limit {
  zone per_ip { key {remote_host}  events 100  window 1m }
}
```

⚠️ Cloudflare proxied 뒤에서는 `{remote_host}`가 전부 Cloudflare IP로 뭉개져 rate limit이 무력화된다. `trusted_proxies` + `client_ip` 로 실제 방문자 IP를 식별해야 한다.

## Cloudflare proxied (RED 아님 — DNS 토글)

도메인을 proxied(주황 구름)로 두면 트래픽이 Cloudflare를 먼저 통과(대규모 DDoS 흡수)하고 원본 IP가 가려진다. 검증: `dig +short <도메인>` 이 원본이 아닌 Cloudflare IP(104.x·172.67.x)를 반환하면 가려진 것.

## unattended-upgrades (GREEN — 자동 재부팅만 RED)

```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades   # 보안 origin 활성
```

자동 재부팅(`Unattended-Upgrade::Automatic-Reboot`)은 서비스 중단 타이밍이라 승인 + 시간창 지정.

## 가장 강한 한 수 — 공개 안 하기 (Tailscale)

대부분의 셀프호스팅은 나·우리 팀만 쓴다. 공개가 꼭 필요하지 않으면 Tailscale 사설망 뒤에 두어 인터넷에 포트를 아예 열지 않는 것이 1순위 방어다. 그러면 자동 봇의 스캐닝 대상에서 빠진다.
