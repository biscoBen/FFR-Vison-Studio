"""Cheap change classification and the Windows publication check gate."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess

from build_contract import documentation_only, request_identity, required_checks_pass


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def requires_build(event_name, event):
    if event_name == "workflow_dispatch":
        return True
    base = event.get("before") if event_name == "push" else event.get("pull_request", {}).get("base", {}).get("sha")
    if not base or not re.fullmatch(r"[0-9a-f]{40}", base) or set(base) == {"0"}:
        return True
    try:
        git("cat-file", "-e", base)
    except subprocess.CalledProcessError:
        git("fetch", "--no-tags", "--depth=1", "origin", base)
    paths = git("diff", "--name-only", "--no-renames", base, "HEAD").splitlines()
    return not documentation_only(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["plan", "gate", "manifest"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "plan":
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        needed = requires_build(os.environ["GITHUB_EVENT_NAME"], event)
        build = int(os.environ.get("REQUESTED_BUILD") or "15")
        if build < 0:
            raise ValueError("Build number must be nonnegative.")
        outputs = {"build_required": str(needed).lower(), "build": str(build),
                   "workflow_sha": git("rev-parse", "HEAD:.github/workflows/windows.yml")}
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in outputs.items()))
        print("Code build required." if needed else "README/CHANGELOG-only change: Windows build and publication skipped.")
    elif args.mode == "gate":
        needs = json.loads(os.environ["JOB_RESULTS"])
        results = {key: value["result"] for key, value in needs.items()}
        needed = needs.get("plan", {}).get("outputs", {}).get("build_required") == "true"
        if not required_checks_pass(needed, results):
            raise SystemExit(f"Required jobs did not succeed: {results}")
        print("All required checks passed." if needed else "Documentation-only check passed; no application build requested.")
    else:
        identity = request_identity(
            os.environ["GITHUB_SHA"], os.environ["GITHUB_REF_NAME"],
            os.environ["REQUESTED_BUILD"], os.environ["CLOUD_DOWNLOAD"] == "true",
            git("rev-parse", "HEAD:.github/workflows/windows.yml"),
            os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"],
        )
        args.output.write_text(json.dumps(identity, indent=2) + "\n")


if __name__ == "__main__":
    main()
