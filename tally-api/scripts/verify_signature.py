#!/usr/bin/env python3
"""Verify a Tally webhook signature (Tally-Signature header).

Tally signs the RAW request body with HMAC-SHA256 using the webhook's
signing secret, then base64-encodes the digest. Compare that to the
`Tally-Signature` header with a constant-time comparison.

CRITICAL: hash the raw bytes of the request body exactly as received.
Do NOT re-serialize parsed JSON — key order / whitespace changes break the hash.

Usage:
    # As a library
    from verify_signature import verify
    ok = verify(raw_body_bytes, signature_header, signing_secret)

    # As a CLI (reads body from stdin)
    cat body.json | verify_signature.py <signature-header> <signing-secret>
"""
import base64
import hashlib
import hmac
import sys


def verify(raw_body: bytes, signature_header: str, signing_secret: str) -> bool:
    if isinstance(raw_body, str):
        raw_body = raw_body.encode("utf-8")
    digest = hmac.new(signing_secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature_header)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: verify_signature.py <signature-header> <signing-secret>  (body on stdin)",
              file=sys.stderr)
        sys.exit(2)
    body = sys.stdin.buffer.read()
    ok = verify(body, sys.argv[1], sys.argv[2])
    print("VALID" if ok else "INVALID")
    sys.exit(0 if ok else 1)
