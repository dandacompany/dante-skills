#!/usr/bin/env bash
# infra-security-audit — read-only 점검 엔진
# 사용: bash audit.sh            (로컬)
#       bash audit.sh user@host  (원격, 키 기반 SSH)
# 읽기 전용. 어떤 설정도 변경하지 않는다. sudo 가 비번을 요구하면 그 점검은 "미확인"으로 표시.
set -o pipefail

TARGET="${1:-}"
IMMEDIATE=(); RECOMMEND=(); UNKNOWN=()
run() {  # 대상에서 명령 실행 (로컬 또는 ssh)
  if [ -z "$TARGET" ]; then bash -c "$1" 2>/dev/null
  else ssh -o BatchMode=yes -o ConnectTimeout=12 "$TARGET" "$1" 2>/dev/null; fi
}

PASS=0; MAX=0
add() { # add <weight> <pass:1/0/u> <label>
  MAX=$((MAX+$1))
  case "$2" in
    1) PASS=$((PASS+$1));;
    0) if [ "$1" -ge 20 ]; then IMMEDIATE+=("$3"); else RECOMMEND+=("$3"); fi;;
    u) UNKNOWN+=("$3");;
  esac
}

echo "== infra-security-audit (read-only) =="
echo "대상: ${TARGET:-로컬 호스트}"
echo

# --- P1 ---
V=$(run "sshd -T 2>/dev/null | grep -i '^permitrootlogin '")
case "$V" in
  *prohibit-password*|*without-password*|*' no'*) add 20 1 "SSH root 로그인 제한";;
  *yes*) add 20 0 "[즉시] SSH root 직접 로그인이 열려 있음 → prohibit-password/no  [승인]";;
  *) add 20 u "SSH root 로그인 (sshd -T 미확인)";;
esac

V=$(run "sshd -T 2>/dev/null | grep -i '^passwordauthentication '")
case "$V" in
  *' no'*) add 20 1 "SSH 비밀번호 인증 비활성";;
  *yes*) add 20 0 "[즉시] SSH 비밀번호 인증이 켜져 있음 → 키 전용으로  [승인]";;
  *) add 20 u "SSH 비밀번호 인증 (미확인)";;
esac

V=$(run "ss -tlnH 2>/dev/null | awk '{print \$4}' | grep -E '0\.0\.0\.0|^\*|\[::\]'")
EXPOSED=$(echo "$V" | grep -vE ':22$|:80$|:443$' | grep -c .)
if [ -z "$V" ]; then add 20 u "노출 포트 (ss 미확인)"
elif [ "$EXPOSED" -eq 0 ]; then add 20 1 "노출 포트 최소 (22/80/443 외 0.0.0.0 없음)"
else add 20 0 "[즉시] 0.0.0.0 으로 외부 노출된 추가 포트 ${EXPOSED}개 (DB/대시보드 확인) → 127.0.0.1/Tailscale 로  [승인]"; fi

V=$(run "ufw status verbose 2>/dev/null || sudo -n ufw status verbose 2>/dev/null")
if [ -z "$V" ]; then add 20 u "ufw 상태 (권한/미설치 — 미확인)"
elif echo "$V" | grep -qi "Status: active" && echo "$V" | grep -qi "deny (incoming)"; then add 20 1 "ufw 활성 + 기본 차단"
else add 20 0 "[즉시] 방화벽이 꺼져 있거나 기본 차단 아님 → ufw 설정  [승인: ufw enable 자기잠금 주의]"; fi

# --- P2 ---
V=$(run "fail2ban-client status sshd 2>/dev/null || sudo -n fail2ban-client status sshd 2>/dev/null")
if echo "$V" | grep -qi "Filter\|Jail\|banned"; then add 10 1 "fail2ban sshd jail 동작"
elif run "command -v fail2ban-client" >/dev/null; then add 10 u "fail2ban (상태 미확인 — 권한)"
else add 10 0 "[권장] fail2ban 미설치 → 반복 침입 자동 차단 없음  [자동]"; fi

V=$(run "dpkg -l unattended-upgrades 2>/dev/null | grep '^ii'")
if [ -n "$V" ]; then add 10 1 "자동 보안 업데이트 설치됨"
else add 10 0 "[권장] unattended-upgrades 미설치  [자동]"; fi

# SSH drop-in 우선순위 함정 (실효값 vs 파일)
EFF=$(run "sshd -T 2>/dev/null | grep -i '^passwordauthentication '")
FILE=$(run "grep -rhi 'passwordauthentication' /etc/ssh/sshd_config.d/ 2>/dev/null | grep -i 'no' | head -1")
if [ -n "$FILE" ] && echo "$EFF" | grep -qi "yes"; then
  add 10 0 "[즉시] drop-in 에 password no 가 있는데 실효값은 yes → 우선순위(00-) 함정  [승인]"
else add 10 1 "SSH 설정 실효값 일치"; fi

# --- P3 ---
V=$(run "command -v lynis")
if [ -n "$V" ]; then
  HI=$(run "sudo -n lynis audit system --quick --no-colors 2>/dev/null | grep -i 'Hardening index' | grep -oE '[0-9]+' | head -1")
  [ -n "$HI" ] && echo "참고: Lynis hardening index = ${HI}/100"
fi
V=$(run "tailscale status 2>/dev/null | head -1")
[ -n "$V" ] && add 5 1 "Tailscale 사설망 사용 중" || add 5 u "Tailscale (미사용 또는 미확인)"

# --- 결과 ---
SCORE=0; [ "$MAX" -gt 0 ] && SCORE=$(( PASS * 100 / MAX ))
echo
echo "== 보안 점수: ${SCORE}/100 =="
echo
if [ "${#IMMEDIATE[@]}" -gt 0 ]; then printf '%s\n' "${IMMEDIATE[@]}"; fi
if [ "${#RECOMMEND[@]}" -gt 0 ]; then printf '%s\n' "${RECOMMEND[@]}"; fi
if [ "${#UNKNOWN[@]}" -gt 0 ]; then echo; echo "미확인(권한/도구 부재 — 추정 변경 금지, 사람 확인):"; printf '  - %s\n' "${UNKNOWN[@]}"; fi
echo
echo "다음 단계: 변경은 plan(diff 미리보기) → apply 순서. [자동]=비파괴 자동, [승인]=사람 확인 필요. references/safe-boundary.md 참조."
