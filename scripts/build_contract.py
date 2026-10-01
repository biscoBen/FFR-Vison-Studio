"""Identity shared by CI, package verification and the authenticated build helper."""

import re

CONTRACT = "ffr-windows-v1"
WORKFLOW_PATH = ".github/workflows/windows.yml"
PROVENANCE = "build-provenance.json"
FLUTTER_VERSION = "3.47.6"
DOCUMENTATION = {"README.md", "CHANGELOG.md"}


def documentation_only(paths):
    return bool(paths) and set(paths) <= DOCUMENTATION


def run_title(build, cloud_download):
    return f"{CONTRACT} build={build} cloud={str(cloud_download).lower()}"


def title_inputs(title):
    match = re.fullmatch(r"ffr-windows-v1 build=(\d+) cloud=(true|false)", title or "")
    return (int(match[1]), match[2] == "true") if match else None


def request_identity(commit, branch, build, cloud_download, workflow_sha, run_id, run_attempt=1):
    return {
        "contract": CONTRACT, "commit": commit, "branch": branch,
        "build": int(build), "cloud_download": bool(cloud_download),
        "workflow_sha": workflow_sha, "flutter_version": FLUTTER_VERSION,
        "run_id": int(run_id), "run_attempt": int(run_attempt),
    }


def required_checks_pass(build_required, results):
    expected = "success" if build_required else "skipped"
    return results.get("plan") == "success" and all(
        results.get(name) == expected for name in ("validate", "compile")
    )
