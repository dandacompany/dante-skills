# Security hardening provenance

This distribution is based on upstream commit
`f10efaa7efc75591b4744cc1d885874a79f5f7ee` from
[`guillaumemeyer/watermarks-remover`](https://github.com/guillaumemeyer/watermarks-remover),
licensed under MIT. Dante Labs audited and hardened the code before publishing
this fork through `dandacompany/dante-skills`.

Hardening applied in this distribution:

- fixed 256 MiB whole-file and 64 MiB stdin caps;
- no environment-variable or credential-store reads;
- no bundled network client or document transmission;
- no external executable or external model-code launch;
- no repository bootstrap or dependency installation;
- offline-only Layer B prompt generation.

These restrictions intentionally remove optional upstream integrations with
local model servers, metadata command-line tools, and reverse-engineered media
scorers. The pure-Python Unicode and container cleaners remain available, with
PDF restricted to inspection-only operation.

Do not replace this distribution with an upstream update without re-auditing and
reapplying or retiring these controls.
