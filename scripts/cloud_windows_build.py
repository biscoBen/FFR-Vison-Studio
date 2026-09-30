#!/usr/bin/env python3
"""Build a fork branch with GitHub Actions and download its verified run artifact."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote, urlencode
import zipfile

REPOSITORY = "biscoBen/FFR-Vison-Studio"
DEFAULT_BRANCH = "Sephira's-Update"
WORKFLOW = "windows.yml"
ARTIFACT = "FFR-Vision-Studio-windows"


class BuildError(RuntimeError):
    pass


def github_environment():
    result = os.environ.copy()
    if result.get("FFR_GITHUB_ACTIONS_TOKEN"):
        result["GH_TOKEN"] = result["FFR_GITHUB_ACTIONS_TOKEN"]
    return result


def gh(*arguments, body=None):
    result = subprocess.run(
        ["gh", *arguments],
        input=json.dumps(body) if body is not None else None,
        text=True,
        capture_output=True,
        env=github_environment(),
    )
    if result.returncode:
        # Download errors can contain signed URLs; never echo those credentials.
        message = re.sub(r'https?://[^\s"<>]+', '[download URL]', result.stderr.strip())
        raise BuildError(message or "GitHub command failed.")
    return result.stdout


def api(path, method="GET", body=None):
    arguments = ["api", f"repos/{REPOSITORY}/{path}", "--method", method]
    if body is not None:
        arguments.extend(["--input", "-"])
    output = gh(*arguments, body=body)
    return json.loads(output) if output.strip() else None


def matching_run(runs, *, branch, commit, previous_ids):
    candidates = [
        run
        for run in runs
        if run["id"] not in previous_ids
        and run["head_branch"] == branch
        and run["head_sha"] == commit
        and run["event"] == "workflow_dispatch"
    ]
    return min(candidates, key=lambda run: run["id"]) if candidates else None


def extract_verified_zip(archive, destination, digest):
    if not digest or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise BuildError("GitHub did not provide a valid SHA256 digest for the download.")
    with archive.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != f"sha256:{actual}":
        raise BuildError("Downloaded ZIP does not match GitHub's SHA256 digest.")
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename.replace("\\", "/")).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise BuildError("Downloaded ZIP contains a path outside its destination.")
        bundle.extractall(destination)


def download_cloud_release(run, artifact, destination):
    tag = f"cloud-test-{run['id']}"
    releases = [r for r in api("releases?per_page=100") if r["tag_name"] == tag and r["draft"]]
    if len(releases) != 1:
        raise BuildError("Expected one unpublished download copy from this workflow run.")
    release = api(f"releases/{releases[0]['id']}")
    expected = {
        "commit": run["head_sha"], "branch": run["head_branch"],
        "run_id": run["id"], "artifact_id": artifact["id"],
    }
    if release["target_commitish"] != run["head_sha"] or json.loads(release["body"]) != expected:
        raise BuildError("Unpublished download copy does not match the selected branch, commit and run.")
    assets = [a for a in release["assets"] if a["name"] == f"{ARTIFACT}.zip"]
    if len(assets) != 1:
        raise BuildError("Expected one ZIP in the unpublished download copy.")
    asset = assets[0]
    with tempfile.TemporaryDirectory(prefix="ffr-download-") as temporary:
        gh("release", "download", tag, "--repo", REPOSITORY,
           "--pattern", asset["name"], "--dir", temporary)
        extract_verified_zip(Path(temporary) / asset["name"], destination, asset.get("digest"))
    return {"temporary_release_id": release["id"], "download_sha256": asset["digest"]}


def build(args):
    if args.build < 0:
        raise BuildError("Build number must be nonnegative.")
    commit = api(f"git/ref/heads/{quote(args.ref, safe='')}")["object"]["sha"]
    checkout = Path(__file__).resolve().parent.parent
    local_branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=checkout, text=True
    ).strip()
    local_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=checkout, text=True
    ).strip()
    if local_branch == args.ref:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=checkout, text=True
        ).strip()
        if dirty or local_commit != commit:
            raise BuildError("Commit and push local changes before requesting their build.")
    print(f"Target: {REPOSITORY} / {args.ref} / {commit}", flush=True)

    if args.enable_actions:
        # Change only enabled; preserve the repository's allowed-actions policy.
        api("actions/permissions", method="PUT", body={"enabled": True})
        print("Repository Actions enabled.", flush=True)

    workflow = api(f"actions/workflows/{WORKFLOW}")
    if workflow["state"] != "active":
        api(f"actions/workflows/{WORKFLOW}/enable", method="PUT")
    query = urlencode({"head_sha": commit, "event": "workflow_dispatch", "per_page": 100})
    endpoint = f"actions/workflows/{WORKFLOW}/runs?{query}"
    previous_ids = {run["id"] for run in api(endpoint)["workflow_runs"]}
    inputs = {"build": str(args.build)}
    if args.cloud_download:
        inputs["cloud_download"] = "true"
    api(
        f"actions/workflows/{WORKFLOW}/dispatches",
        method="POST",
        body={"ref": args.ref, "inputs": inputs},
    )
    print("Build requested; waiting for a run at the selected commit.", flush=True)

    deadline = time.monotonic() + args.timeout
    run = None
    previous_status = None
    while time.monotonic() < deadline:
        if run is None:
            run = matching_run(
                api(endpoint)["workflow_runs"],
                branch=args.ref,
                commit=commit,
                previous_ids=previous_ids,
            )
        else:
            run = api(f"actions/runs/{run['id']}")
        if run:
            if run["head_sha"] != commit or run["head_branch"] != args.ref:
                raise BuildError("The run does not match the requested branch and commit.")
            if run["status"] != previous_status:
                print(f"{run['html_url']} — {run['status']}", flush=True)
                previous_status = run["status"]
            if run["status"] == "completed":
                break
        time.sleep(10)
    else:
        raise BuildError("Timed out waiting for the Windows build.")

    if run["conclusion"] != "success":
        raise BuildError(f"Build finished with {run['conclusion']}: {run['html_url']}")
    artifacts = api(f"actions/runs/{run['id']}/artifacts")["artifacts"]
    matches = [
        artifact for artifact in artifacts
        if artifact["name"] == ARTIFACT and not artifact["expired"]
    ]
    if len(matches) != 1:
        raise BuildError("Expected one nonexpired Windows artifact from this run.")
    destination = args.output.resolve() / f"{commit[:12]}-run-{run['id']}"
    if destination.exists():
        raise BuildError(f"Refusing to overwrite existing files: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    download_record = {}
    with tempfile.TemporaryDirectory(prefix="ffr-build-", dir=destination.parent) as temporary:
        staging = Path(temporary)
        if args.cloud_download:
            download_record = download_cloud_release(run, matches[0], staging)
        else:
            gh("run", "download", str(run["id"]), "--repo", REPOSITORY,
               "--name", ARTIFACT, "--dir", str(staging))
        executables = list(staging.rglob("FFR Vision Studio.exe"))
        if len(executables) != 1:
            raise BuildError("Downloaded artifact does not contain exactly one app executable.")
        if not (executables[0].parent / "flutter_windows.dll").is_file():
            raise BuildError("Downloaded app is missing its Flutter runtime.")
        staging.rename(destination)
    executables = list(destination.rglob("FFR Vision Studio.exe"))
    if len(executables) != 1:
        raise BuildError("Downloaded artifact does not contain exactly one app executable.")
    executable = executables[0]
    if not (executable.parent / "flutter_windows.dll").is_file():
        raise BuildError("Downloaded app is missing its Flutter runtime.")
    record = {
        "repository": REPOSITORY,
        "branch": args.ref,
        "commit": commit,
        "build": args.build,
        "run_id": run["id"],
        "run_url": run["html_url"],
        "artifact_id": matches[0]["id"],
        "executable": str(executable),
        "downloaded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **download_record,
    }
    (destination / "build-record.json").write_text(json.dumps(record, indent=2) + "\n")
    if args.cloud_download:
        api(f"releases/{download_record['temporary_release_id']}", method="DELETE")
        print("Temporary unpublished download copy removed.", flush=True)
    print(f"Verified build provenance; executable: {executable}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=DEFAULT_BRANCH)
    parser.add_argument("--build", type=int, default=15)
    parser.add_argument("--enable-actions", action="store_true",
                        help="Enable repository Actions (requires Administration: write).")
    parser.add_argument("--cloud-download", action="store_true",
                        help="Use a temporary unpublished release when the cloud proxy blocks artifact storage.")
    parser.add_argument("--output", type=Path, default=Path("/workspace/.runtime/ffr/builds"))
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    try:
        build(args)
    except (BuildError, OSError, subprocess.CalledProcessError) as error:
        print(f"Build blocked: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
