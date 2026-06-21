---
name: infra-security-audit
description: Audit and harden a self-hosted Linux server's infrastructure security over SSH or locally. Covers ufw firewall, SSH hardening, fail2ban, exposed ports, unattended-upgrades, Cloudflare proxy, and Tailscale. Runs a read-only audit by default that returns a hardening score and a prioritized report, then auto-applies only non-destructive fixes and gates risky changes (ufw enable, sshd edits, port binding) behind human approval with backup and self-lockout prevention. Use when the user wants to check, audit, score, or harden a server or VPS infrastructure, asks about firewall/SSH/fail2ban/exposed ports, or says things like "내 서버 보안 점검", "서버 하드닝", "VPS 잠그기", "infra security audit".
---

# Infra Security Audit

## Overview

This skill audits and hardens the **host and network layer** of a self-hosted Linux server (firewall, SSH, intrusion blocking, exposed ports, public-exposure posture). It is distinct from agent/application-layer security (skills, permissions, sandboxing). It is built for non-developer operators running a single VPS or home server, and it never makes a risky change on its own.

The single most important rule: **audit reads, applying changes is gated.** Diagnosis is automatic; anything that can sever a connection, lock the current session, or stop a service requires explicit human approval, a backup, and a self-lockout safeguard.

## Workflow Decision Tree

Operate in three modes, always in this order. Never skip from audit straight to applying risky changes.

1. **audit** (default, read-only) — Diagnose and report. Safe to run anytime.
2. **plan** — For each finding, classify the fix as GREEN / YELLOW / RED and produce a concrete diff/command preview. No changes yet.
3. **apply** — Execute GREEN fixes automatically; for YELLOW/RED, show the diff, take a backup, get explicit approval, apply, then verify (and roll back on failure).

When the user only says "점검" or "audit", stop after mode 1 and report. Only proceed to plan/apply when the user asks to fix or harden.

## Mode 1 — audit (read-only)

Run the bundled audit script. It is read-only and safe.

```bash
bash scripts/audit.sh            # local host
bash scripts/audit.sh user@host  # remote over SSH (key-based)
```

The script checks the items in `references/checklist.md`, prints a **hardening score (0–100)** and a two-tier report (`[즉시]` must-fix / `[권장]` recommended), and labels each finding `[자동]` (safe to auto-fix) or `[승인]` (needs approval). If a check cannot run (tool missing, permission denied), it prints `미확인` rather than guessing.

To interpret raw command output (ufw status, `sshd -T`, fail2ban, `ss`, Lynis/ssh-audit if present), load `references/interpret.md`.

> Reuse existing tools, do not reinvent. If `lynis` or `ssh-audit` is installed, the script uses them and filters to this skill's scope; otherwise it falls back to direct checks. See `references/checklist.md`.

## Mode 2 — plan

For each finding from the audit, classify the remediation by risk and produce a preview. Load `references/safe-boundary.md` for the full GREEN/YELLOW/RED table. Summary:

- **GREEN — non-destructive, auto-apply OK**: does not cut connectivity, lock the session, or stop a service. Examples: install fail2ban + enable sshd jail (with operator IP/Tailscale range added to `ignoreip`), enable unattended-upgrades, add operator IP to an allowlist, add a validated Caddy `rate_limit` and `reload`.
- **YELLOW — reversible, needs approval**: sshd hardening (PermitRootLogin, PasswordAuthentication, weak algorithms), sysctl network params.
- **RED — hard to reverse, hard gate + mandatory backup**: `ufw enable`, SSH port change, binding a port from `0.0.0.0` to loopback/Tailscale, switching to CrowdSec, enabling auto-reboot.

Produce, for every non-GREEN fix, a **diff or exact command preview** ("this file changes like this") before doing anything.

## Mode 3 — apply

- Execute GREEN fixes, then re-audit to confirm the score moved.
- For YELLOW/RED: show diff → take a timestamped backup (e.g. `sshd_config.bak.<ts>`) → get explicit approval → apply → verify in a **new** session → roll back on failure.
- **Self-lockout prevention is mandatory.** Before any firewall or SSH change, load `references/self-lockout.md` and follow it exactly. Core safeguards: allow SSH (and the Tailscale range) in ufw *before* `ufw enable`; put sshd changes in a low-numbered drop-in and verify a fresh login keeps working before committing; check `/etc/ssh/sshd_config.d/*.conf` ordering for the first-match trap.

## Safety Rules (always)

1. **Stop on empty/ambiguous results.** If an audit check returns nothing or errors, never make a guessed change — report and escalate to the human.
2. **Back up before any file change.** Keep a one-command rollback path.
3. **Log every command and its result** so the run is auditable.
4. **Idempotent.** Re-running must not double-apply.
5. **Never auto-run a RED change**, even if the user says "fix everything" — RED always shows diff + backup + explicit confirm.
6. This skill is itself third-party code running with the agent's privileges; the human approval gate is the only real boundary for risky changes. Treat it as load-bearing.

## Resources

- `references/checklist.md` — the 14 scoped audit items (P1–P3) and which tool covers each.
- `references/safe-boundary.md` — GREEN/YELLOW/RED classification and the rationale (cut/lock/stop test).
- `references/commands.md` — copy-paste remediation commands, dogfood-verified (ufw, SSH 00-hardening drop-in, fail2ban, Caddy rate_limit, Cloudflare, Tailscale).
- `references/self-lockout.md` — the three self-lockout traps and how to avoid each.
- `references/interpret.md` — how to read ufw/`sshd -T`/fail2ban/`ss`/Lynis/ssh-audit output.
- `scripts/audit.sh` — read-only audit engine (local or `user@host`), prints score + report.

## Tone (when reporting to a non-developer)

Plain Korean, calm, non-fear-mongering. Frame attacks as "the internet's default weather", not a targeted threat. Do not assert attacker nationality (bots spoof and relay; origin is meaningless). Do not name specific vendors as "bad" or cite CVE numbers as fact. No emoji in output — use text labels `[즉시]` / `[권장]` / `[자동]` / `[승인]`.
