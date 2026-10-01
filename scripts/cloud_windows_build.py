#!/usr/bin/env python3
"""Build a fork branch with GitHub Actions and download its verified run artifact."""

import argparse
import base64
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

from build_contract import PROVENANCE, WORKFLOW_PATH, request_identity, title_inputs

REPOSITORY = "biscoBen/FFR-Vison-Studio"
DEFAULT_BRANCH = "Sephira's-Update"
WORKFLOW = "windows.yml"
ARTIFACT = "FFR-Vision-Studio-windows"


class BuildError(RuntimeError):
    pass


class InvalidArtifact(BuildError):
    """A run cannot supply the requested verified binary; a new run is needed."""


def compatible_run(run, *, branch, commit, workflow_id, build, cloud_download):
    return (
        run.get('head_branch') == branch and run.get('head_sha') == commit
        and run.get('workflow_id') == workflow_id and run.get('path') == WORKFLOW_PATH
        and run.get('event') in {'push', 'workflow_dispatch'}
        and title_inputs(run.get('display_title')) == (build, cloud_download)
    )


def select_reusable_run(runs, request, available):
    eligible = [run for run in runs if compatible_run(run, **request)]
    for run in sorted(eligible, key=lambda candidate: candidate['id'], reverse=True):
        if run.get('status') == 'completed' and run.get('conclusion') == 'success' and available(run):
            return run
    running = [run for run in eligible if run.get('status') in {'queued', 'in_progress', 'waiting', 'pending', 'requested'}]
    return min(running, key=lambda run: run['id']) if running else None


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


def matching_run(runs, *, branch, commit, previous_ids, request=None):
    candidates = [
        run
        for run in runs
        if run["id"] not in previous_ids
        and run["head_branch"] == branch
        and run["head_sha"] == commit
        and run["event"] == "workflow_dispatch"
        and (request is None or compatible_run(run, **request))
    ]
    return min(candidates, key=lambda run: run["id"]) if candidates else None


def extract_verified_zip(archive, destination, digest):
    if not digest or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise InvalidArtifact("GitHub did not provide a valid SHA256 digest for the download.")
    with archive.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != f"sha256:{actual}":
        raise InvalidArtifact("Downloaded ZIP does not match GitHub's SHA256 digest.")
    try:
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (destination / member.filename.replace("\\", "/")).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise InvalidArtifact("Downloaded ZIP contains a path outside its destination.")
            bundle.extractall(destination)
    except zipfile.BadZipFile as error:
        raise InvalidArtifact('Downloaded build ZIP is corrupt.') from error


def download_cloud_release(run, artifact, destination):
    tag = f"cloud-test-{run['id']}"
    releases = [r for r in api("releases?per_page=100") if r["tag_name"] == tag and r["draft"]]
    if len(releases) != 1:
        raise InvalidArtifact("Expected one unpublished download copy from this workflow run.")
    release = api(f"releases/{releases[0]['id']}")
    expected = {
        "commit": run["head_sha"], "branch": run["head_branch"],
        "run_id": run["id"], "artifact_id": artifact["id"],
    }
    try:
        metadata = json.loads(release["body"])
    except (TypeError, ValueError):
        metadata = None
    if release["target_commitish"] != run["head_sha"] or metadata != expected:
        raise InvalidArtifact("Unpublished download copy does not match the selected branch, commit and run.")
    assets = [a for a in release["assets"] if a["name"] == f"{ARTIFACT}.zip"]
    if len(assets) != 1:
        raise InvalidArtifact("Expected one ZIP in the unpublished download copy.")
    asset = assets[0]
    with tempfile.TemporaryDirectory(prefix="ffr-download-") as temporary:
        gh("release", "download", tag, "--repo", REPOSITORY,
           "--pattern", asset["name"], "--dir", temporary)
        extract_verified_zip(Path(temporary) / asset["name"], destination, asset.get("digest"))
    return {"temporary_release_id": release["id"], "download_sha256": asset["digest"]}


def published_release(run, build):
    try:
        release = api(f"releases/tags/sephira-test-{run['id']}")
    except BuildError as error:
        if '404' in str(error):
            return None
        raise
    expected = {'channel': 'sephira-test', 'repository': REPOSITORY,
                'branch': run['head_branch'], 'commit': run['head_sha'], 'run_id': run['id'], 'build': build}
    try:
        metadata = json.loads(release['body'])
    except (ValueError, TypeError):
        return None
    assets = [asset for asset in release.get('assets', []) if asset['name'] == 'Sephira-Studio-Test.zip'
              and re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or '')]
    if release.get('draft') or not release.get('prerelease') or release.get('target_commitish') != run['head_sha'] or metadata != expected or len(assets) != 1:
        return None
    return release, assets[0]


def verified_artifact(run):
    artifacts = api(f"actions/runs/{run['id']}/artifacts")['artifacts']
    matches = [artifact for artifact in artifacts if artifact['name'] == ARTIFACT and not artifact['expired']
               and re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest') or '')
               and artifact.get('workflow_run', {}).get('head_sha') == run['head_sha']
               and artifact.get('workflow_run', {}).get('head_branch') == run['head_branch']
               and artifact.get('workflow_run', {}).get('id') == run['id']]
    return matches[0] if len(matches) == 1 else None


def download_artifact(artifact, destination):
    with tempfile.TemporaryDirectory(prefix='ffr-artifact-') as temporary:
        archive = Path(temporary) / 'artifact.zip'
        with archive.open('wb') as stream:
            result = subprocess.run(['gh', 'api', f"repos/{REPOSITORY}/actions/artifacts/{artifact['id']}/zip"],
                                    stdout=stream, stderr=subprocess.PIPE, env=github_environment())
        if result.returncode:
            message = re.sub(r'https?://[^\s"<>]+', '[download URL]', result.stderr.decode(errors='replace'))
            raise BuildError(message.strip() or 'Authenticated artifact download failed.')
        extract_verified_zip(archive, destination, artifact['digest'])
    return {'download_sha256': artifact['digest'], 'download_source': 'artifact'}


def download_published_release(run, release_info, destination, build):
    release, asset = release_info
    with tempfile.TemporaryDirectory(prefix='ffr-release-') as temporary:
        gh('release', 'download', release['tag_name'], '--repo', REPOSITORY,
           '--pattern', asset['name'], '--dir', temporary)
        extract_verified_zip(Path(temporary) / asset['name'], destination, asset['digest'])
    expected = {'channel': 'sephira-test', 'repository': REPOSITORY, 'branch': run['head_branch'],
                'commit': run['head_sha'], 'run_id': run['id'], 'build': build}
    try:
        metadata = json.loads((destination / 'test-build.json').read_text())
    except (OSError, ValueError):
        metadata = None
    if metadata != expected:
        raise InvalidArtifact('Published ZIP metadata does not match the selected commit and build.')
    return {'download_sha256': asset['digest'], 'download_source': 'test-release', 'release_id': release['id']}


def check_bundle(staging, expected):
    manifests = list(staging.rglob(PROVENANCE))
    try:
        identity = json.loads(manifests[0].read_text()) if len(manifests) == 1 else None
    except (OSError, ValueError):
        identity = None
    if identity != expected:
        raise InvalidArtifact('Compiled artifact does not match the requested commit, workflow and build inputs.')
    executables = list(staging.rglob('FFR Vision Studio.exe'))
    if len(executables) != 1 or not (executables[0].parent / 'flutter_windows.dll').is_file():
        raise InvalidArtifact('Downloaded artifact must contain one app executable and its Flutter runtime.')
    return executables[0]


def download_run(run, args, workflow_sha, reused):
    jobs = api(f"actions/runs/{run['id']}/jobs?per_page=100")['jobs']
    results = {job['name']: job['conclusion'] for job in jobs}
    if any(results.get(name) != 'success' for name in ('plan', 'validate', 'compile', 'windows')):
        raise InvalidArtifact('This run did not pass every required validation and compilation job.')
    artifact = verified_artifact(run)
    destination = args.output.resolve() / f"{run['head_sha'][:12]}-run-{run['id']}"
    if destination.exists():
        raise BuildError(f"Refusing to overwrite existing files: {destination}. Choose a different --output directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = request_identity(run['head_sha'], args.ref, args.build, args.cloud_download,
                                workflow_sha, run['id'], run.get('run_attempt', 1))
    with tempfile.TemporaryDirectory(prefix='ffr-build-', dir=destination.parent) as temporary:
        staging = Path(temporary) / 'primary'
        staging.mkdir()
        if args.cloud_download and artifact:
            try:
                download_record = download_cloud_release(run, artifact, staging)
            except BuildError:
                release = published_release(run, args.build)
                if not release:
                    raise
                staging = Path(temporary) / 'fallback'
                staging.mkdir()
                download_record = download_published_release(run, release, staging, args.build)
        elif artifact:
            try:
                download_record = download_artifact(artifact, staging)
            except BuildError:
                release = published_release(run, args.build)
                if not release:
                    raise
                print('Using the verified published test ZIP through the authenticated release endpoint.', flush=True)
                staging = Path(temporary) / 'fallback'
                staging.mkdir()
                download_record = download_published_release(run, release, staging, args.build)
        else:
            release = published_release(run, args.build)
            if not release:
                raise InvalidArtifact('The run has no compatible artifact or verified test release.')
            download_record = download_published_release(run, release, staging, args.build)
        executable = check_bundle(staging, expected)
        relative_executable = executable.relative_to(staging)
        staging.rename(destination)
    record = {
        'repository': REPOSITORY, **expected, 'run_url': run['html_url'],
        'artifact_id': artifact['id'] if artifact else None,
        'executable': str(destination / relative_executable), 'reused_run': reused,
        'downloaded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), **download_record,
    }
    (destination / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    if 'temporary_release_id' in download_record:
        api(f"releases/{download_record['temporary_release_id']}", method='DELETE')
        print('Temporary unpublished download copy removed.', flush=True)
    print(f"Verified build provenance; executable: {record['executable']}", flush=True)
    return record


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
    configuration = api(f"contents/{WORKFLOW_PATH}?{urlencode({'ref': commit})}")
    if 'ffr-windows-v1' not in base64.b64decode(configuration['content']).decode():
        raise BuildError('The requested commit has no verified build-input contract. Use its original Actions workflow directly.')
    request = {'branch': args.ref, 'commit': commit, 'workflow_id': workflow['id'],
               'build': args.build, 'cloud_download': args.cloud_download}
    query = urlencode({"head_sha": commit, "per_page": 100})
    endpoint = f"actions/workflows/{WORKFLOW}/runs?{query}"
    deadline = time.monotonic() + args.timeout
    run = None
    rejected = set()
    dispatched = False
    previous_ids = set()
    previous_status = None
    while time.monotonic() < deadline:
        if run is None:
            runs = api(endpoint)['workflow_runs']
            if dispatched:
                run = matching_run(runs, branch=args.ref, commit=commit, previous_ids=previous_ids, request=request)
            else:
                if not args.force_rebuild:
                    run = select_reusable_run([candidate for candidate in runs if candidate['id'] not in rejected],
                                              request, lambda candidate: bool(verified_artifact(candidate) or published_release(candidate, args.build)))
                if run:
                    print(f"Reusing matching run {run['id']}; no workflow dispatched.", flush=True)
                else:
                    if api(f"git/ref/heads/{quote(args.ref, safe='')}")['object']['sha'] != commit:
                        raise BuildError('The branch advanced before dispatch; request the new commit explicitly.')
                    previous_ids = {candidate['id'] for candidate in runs}
                    inputs = {'build': str(args.build), 'cloud_download': str(args.cloud_download).lower()}
                    api(f"actions/workflows/{WORKFLOW}/dispatches", method='POST', body={'ref': args.ref, 'inputs': inputs})
                    dispatched = True
                    print('No reusable run selected; requested one build for the exact commit and inputs.', flush=True)
        else:
            run = api(f"actions/runs/{run['id']}")
        if run:
            if not compatible_run(run, **request):
                raise BuildError('The run does not match the requested commit, workflow and build inputs.')
            if run["status"] != previous_status:
                print(f"{run['html_url']} — {run['status']}", flush=True)
                previous_status = run["status"]
            if run["status"] == "completed":
                if run['conclusion'] == 'success':
                    try:
                        return download_run(run, args, configuration['sha'], reused=not dispatched)
                    except InvalidArtifact as error:
                        if dispatched:
                            raise
                        print(f"Rejecting incompatible run {run['id']}: {error}", flush=True)
                elif dispatched:
                    raise BuildError(f"Build finished with {run['conclusion']}: {run['html_url']}")
                rejected.add(run['id'])
                run = None
                continue
        time.sleep(5)
    raise BuildError('Timed out waiting for the verified Windows build and publication.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default=DEFAULT_BRANCH)
    parser.add_argument("--build", type=int, default=15)
    parser.add_argument("--force-rebuild", action="store_true", help="Dispatch a new run even when an identical build exists.")
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
