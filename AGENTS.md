# Fork development

- Work on `Sephira's-Update`. Keep `master` clean as the inherited baseline.
- Update the fork section of `CHANGELOG.md` alongside each user-facing feature or fix. Describe what users get and any
  material testing limits. Preserve the original project's release notes.
- Keep new work under **Unreleased** until the Windows package passes the required checks. Once published, record its
  date in America/Los_Angeles, commit and test-release link. Do not treat build 15 as a unique fork release number;
  tested packages are identified by their commit and workflow run.
- During development, run focused checks for the change. Run the full relevant checks once against the final code;
  Windows CI supplies the full Flutter suite, real frozen-engine setup, Python checks, launcher/updater checks and build.
- After pushing code, use `scripts/cloud_windows_build.py` to join or reuse the exact commit's matching build. Do not
  dispatch another build while a matching push run is active. Use `--force-rebuild` only when a new run is intentional.
  The helper verifies workflow/input provenance and checksums, including its authenticated test-release fallback.
- README/CHANGELOG-only pushes run the cheap `plan` and `windows` checks and produce no binary or release. After the
  package is verified, commit publication notes only in those files; do not request another build for that documentation
  commit or relabel the earlier binary. Other paths, including these instructions, keep the full checks.
- Validation and Windows compilation run concurrently. Publication requires both to succeed for the same commit.
  Job-level cancellation applies only to superseded automatic builds on this branch; manual builds and publication
  are protected. Keep the checksum-pinned engine cache and fresh extraction; never cache generated build directories.
- Record when the first complete code candidate is finished and when the verified release is delivered. Include local
  checks, corrections, extra builds, waiting and verification in that elapsed time; do not restart the timer after a fix.
  Report measured CI time and runner usage separately from estimates or user-reported prior task duration.
