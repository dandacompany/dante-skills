# Security hardening provenance

This distribution is based on upstream commit
`f10efaa7efc75591b4744cc1d885874a79f5f7ee` from
[`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover),
licensed under MIT. Dante Labs audited and hardened the code before publishing
this fork through `dandacompany/dante-skills`.

Hardening applied in this distribution:

- non-loopback rewrite endpoints require HTTPS;
- rewrite responses are capped at 1 MiB and redirects remain blocked;
- direct image APIs enforce the existing 256 MiB input cap;
- reverse-SynthID imports require the audited HTTPS origin and pinned commit
  `b11083676fd3ee3ff97ce9d03c0e409e46905902`;
- an existing reverse-SynthID checkout is validated before dependency setup.

Do not replace this distribution with an upstream update without re-auditing and
reapplying or retiring these controls.
