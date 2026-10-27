"""Private finished-mod publishing and native SteamOS installation. Standard library only.

No default destination, no automatic uploads, and no credentials in settings or ZIPs.
The same file runs in the frozen PC engine and as the standalone Deck installer.
"""
import argparse
from contextlib import contextmanager
import ctypes
import datetime as dt
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

CHANNEL = 'ffr-private-mod'
SETTINGS = 'deck-sync-settings.json'
VERIFIED = 'build/deck-sync/verified.json'
MARKER = 'FFRS/Content/Paks/FFRS-Windows.utoc'
PAKS = tuple('FFRS/Content/Paks/~mods/zzz_EstherTsukiko_P.' + ext for ext in ('utoc', 'ucas', 'pak'))
BINARY = 'FFRS/Binaries/Win64/'
LEADER = BINARY + 'ue4ss/Mods/FFRStudioFieldLeader/'
LEADER_FILES = tuple(LEADER + name for name in ('enabled.txt', 'Scripts/config.lua', 'Scripts/main.lua'))
LOADER_FILES = tuple(BINARY + name for name in ('dwmapi.dll', 'ue4ss/UE4SS.dll', 'ue4ss/UE4SS-settings.ini',
                       'ue4ss/VTableLayout.ini', 'ue4ss/MemberVariableLayout.ini', 'ue4ss/LICENSE'))
REQUIRED_LOADER = LOADER_FILES[:3]
MAX_ZIP = 2 * 1024**3
MAX_TOTAL = 8 * 1024**3
SECRET_SERVICE = 'ffr-studio-deck-sync'
_operation = threading.RLock()
_publishing = {'running': False, 'result': None, 'message': None}


class SyncError(RuntimeError):
    pass


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            digest.update(chunk)
    return digest.hexdigest()


def allowed(name):
    if name in PAKS + LEADER_FILES + LOADER_FILES:
        return True
    # Native signatures sometimes accompany the working loader. Never ship
    # another mod, logs, dumps, saves, the engine, or the whole binaries folder.
    prefix = BINARY + 'ue4ss/UE4SS_Signatures/'
    return name.startswith(prefix) and bool(re.fullmatch(r'[A-Za-z0-9_-]+\.lua', name[len(prefix):]))


def checked(root, relative):
    if (not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative
            or relative.startswith('/') or any(p in ('', '.', '..') for p in relative.split('/'))):
        raise SyncError('Invalid transfer path.')
    root = Path(root).absolute()
    target = root / relative
    for node in (target, *target.parents):
        if node.is_symlink() or (hasattr(node, 'is_junction') and node.is_junction()):
            raise SyncError('Transfer paths must not contain links.')
    if not target.resolve().is_relative_to(root.resolve()):
        raise SyncError('Transfer path escapes its folder.')
    return target


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.ffr-sync-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_write(path, value):
    atomic(path, (json.dumps(value, indent=2) + '\n').encode())


def read_json(path, default=None):
    if not Path(path).exists():
        return default
    try:
        return json.loads(Path(path).read_bytes())
    except (ValueError, OSError) as error:
        raise SyncError('A local sync record is unreadable; no files changed.') from error


def repository(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}', value):
        raise SyncError('Enter a GitHub repository as owner/name.')
    if value.lower() == 'biscoben/ffr-vison-studio' or value.split('/')[1] in ('.', '..'):
        raise SyncError('Use a separate private repository for personal mods.')
    return value


def settings(root):
    value = read_json(checked(root, SETTINGS), {'schema': 1, 'enabled': False, 'repository': ''})
    if (not isinstance(value, dict) or set(value) != {'schema', 'enabled', 'repository'}
            or value['schema'] != 1 or type(value['enabled']) is not bool):
        raise SyncError('Unsupported personal sync settings.')
    if value['repository']:
        repository(value['repository'])
    if value['enabled'] and not value['repository']:
        raise SyncError('Personal sync needs a private repository.')
    return value


class CredentialStore:
    """Windows Credential Manager; Linux Secret Service or a prompt each run."""
    def __init__(self, root):
        self.installation = hashlib.sha256(str(Path(root).resolve()).encode()).hexdigest()[:24]

    def _windows(self):
        from ctypes import wintypes
        class Credential(ctypes.Structure):
            _fields_ = [('Flags', wintypes.DWORD), ('Type', wintypes.DWORD), ('TargetName', wintypes.LPWSTR),
                        ('Comment', wintypes.LPWSTR), ('LastWritten', wintypes.FILETIME),
                        ('CredentialBlobSize', wintypes.DWORD), ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
                        ('Persist', wintypes.DWORD), ('AttributeCount', wintypes.DWORD),
                        ('Attributes', ctypes.c_void_p), ('TargetAlias', wintypes.LPWSTR), ('UserName', wintypes.LPWSTR)]
        api = ctypes.WinDLL('advapi32', use_last_error=True)
        api.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
        api.CredWriteW.restype = wintypes.BOOL
        api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(Credential))]
        api.CredReadW.restype = wintypes.BOOL
        api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        api.CredDeleteW.restype = wintypes.BOOL
        api.CredFree.argtypes = [ctypes.c_void_p]
        api.CredFree.restype = None
        return api, Credential

    def _name(self, repo):
        return 'FFRStudio/DeckSync/' + self.installation + '/' + repository(repo).lower()

    @staticmethod
    def linux_backend():
        if shutil.which('secret-tool'):
            return 'secret', shutil.which('secret-tool')
        for name in ('kwallet-query', 'kwallet6-query'):
            if shutil.which(name):
                return 'kwallet', shutil.which(name)
        return None

    def _kwallet(self, command, mode, repo, token=None):
        return subprocess.run([command, mode, self._name(repo), '--folder', 'FFR Studio', 'kdewallet'],
                              input=token, capture_output=True, text=True, timeout=30)

    def get(self, repo):
        if sys.platform == 'win32':
            api, kind = self._windows()
            pointer = ctypes.POINTER(kind)()
            if not api.CredReadW(self._name(repo), 1, 0, ctypes.byref(pointer)):
                if ctypes.get_last_error() == 1168:
                    return None
                raise SyncError('Windows Credential Manager could not read the saved token.')
            try:
                return ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize).decode('utf-8')
            finally:
                api.CredFree(pointer)
        backend = self.linux_backend()
        if backend and backend[0] == 'secret':
            result = subprocess.run(['secret-tool', 'lookup', 'service', SECRET_SERVICE, 'installation', self.installation,
                                     'repository', repo.lower()], capture_output=True, text=True, timeout=15)
            return result.stdout.strip() if result.returncode == 0 else None
        if backend:
            result = self._kwallet(backend[1], '--read-password', repo)
            return (result.stdout.strip() or None) if result.returncode == 0 else None
        return None

    def put(self, repo, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_]{20,255}', token):
            raise SyncError('Enter a GitHub personal access token; it is stored only in the local credential manager.')
        if sys.platform == 'win32':
            api, kind = self._windows()
            blob = (ctypes.c_ubyte * len(token)).from_buffer_copy(token.encode('ascii'))
            value = kind(Type=1, TargetName=self._name(repo), CredentialBlobSize=len(token),
                         CredentialBlob=blob, Persist=2, UserName='GitHub')
            if not api.CredWriteW(ctypes.byref(value), 0):
                raise SyncError('Windows Credential Manager could not save the token.')
            return True
        backend = self.linux_backend()
        if backend and backend[0] == 'secret':
            result = subprocess.run(['secret-tool', 'store', '--label=Resonance Deck Sync', 'service', SECRET_SERVICE,
                                     'installation', self.installation, 'repository', repo.lower()],
                                    input=token, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise SyncError('The Linux keyring could not save the token. You can enter it each update instead.')
            return True
        if backend:
            result = self._kwallet(backend[1], '--write-password', repo, token)
            if result.returncode:
                raise SyncError('KWallet could not save the token. You can enter it each update instead.')
            return True
        return False

    def delete(self, repo):
        if sys.platform == 'win32':
            api, _ = self._windows()
            if not api.CredDeleteW(self._name(repo), 1, 0) and ctypes.get_last_error() != 1168:
                raise SyncError('Windows Credential Manager could not remove the token.')
        else:
            backend = self.linux_backend()
            if backend and backend[0] == 'secret':
                result = subprocess.run(['secret-tool', 'clear', 'service', SECRET_SERVICE, 'installation', self.installation,
                                         'repository', repo.lower()], capture_output=True, timeout=15, check=False)
                if result.returncode:
                    raise SyncError('The Linux keyring could not remove the token.')
            elif backend:
                # kwallet-query has read/write but no delete mode. Clearing the
                # encrypted value removes the token without using command args.
                if self._kwallet(backend[1], '--write-password', repo, '').returncode:
                    raise SyncError('KWallet could not clear the saved token.')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    def __init__(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_]{20,255}', token):
            raise SyncError('A GitHub personal access token is required.')
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, path, method='GET', body=None, stream=None, size=None, accept='application/vnd.github+json'):
        host = 'uploads.github.com' if stream is not None else 'api.github.com'
        if not path.startswith('/') or '://' in path:
            raise SyncError('Invalid GitHub endpoint.')
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': accept,
                   'User-Agent': 'FFR-Studio-Private-Deck-Sync', 'X-GitHub-Api-Version': '2022-11-28'}
        data = stream
        if stream is not None:
            headers.update({'Content-Type': 'application/zip', 'Content-Length': str(size)})
        elif body is not None:
            data = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        try:
            return self.opener.open(urllib.request.Request('https://' + host + path, data=data,
                                                         headers=headers, method=method), timeout=60)
        except urllib.error.HTTPError as error:
            if accept == 'application/octet-stream' and error.code in (301, 302, 303, 307, 308):
                location = error.headers.get('Location', '')
                url = urllib.parse.urlparse(location)
                if (url.scheme == 'https' and url.hostname == 'release-assets.githubusercontent.com'
                        and url.username is None and url.password is None and url.port in (None, 443)):
                    # The signed download URL gets no GitHub token. Do not log it.
                    try:
                        return self.opener.open(urllib.request.Request(location, headers={'User-Agent': 'FFR-Studio-Deck-Sync'}), timeout=60)
                    except (urllib.error.URLError, OSError) as download_error:
                        raise SyncError('Private package download failed; try again.') from download_error
            raise SyncError(f'GitHub returned HTTP {error.code}. Check the private repository and token permissions.') from error
        except (urllib.error.URLError, OSError) as error:
            raise SyncError('Could not reach GitHub. Check your connection and try again.') from error

    def api(self, path, method='GET', body=None):
        with self.request(path, method, body) as response:
            raw = response.read(4 * 1024**2 + 1)
        if len(raw) > 4 * 1024**2:
            raise SyncError('GitHub metadata exceeds the supported size.')
        try:
            return json.loads(raw) if raw else None
        except ValueError as error:
            raise SyncError('GitHub returned invalid metadata.') from error

    def private(self, repo, publishing=False):
        repo = repository(repo)
        info = self.api('/repos/' + repo)
        if info.get('private') is not True or str(info.get('full_name', '')).lower() != repo.lower():
            raise SyncError('Personal sync requires a private repository. Nothing was uploaded.')
        if publishing:
            account = self.api('/user').get('login', '')
            if str(info.get('owner', {}).get('login', '')).lower() != account.lower() or not account:
                raise SyncError('Publish only to your own private repository.')
            if not info.get('permissions', {}).get('push'):
                raise SyncError('The PC token needs Contents: read and write on your private repository.')
        return info


def configure(root, enabled, repo, token=None, github=GitHub, credentials=None):
    if type(enabled) is not bool:
        raise SyncError('Invalid sync setting.')
    repo = repository(repo.strip()) if repo.strip() else ''
    vault = credentials or CredentialStore(root)
    if enabled and not repo:
        raise SyncError('Create your own private repository first.')
    if enabled or token:
        secret = token or vault.get(repo)
        if not secret:
            raise SyncError('Add your local GitHub token first.')
        github(secret).private(repo, publishing=True)
        if token and not vault.put(repo, token):
            raise SyncError('A credential manager is required to save PC publishing credentials.')
    value = {'schema': 1, 'enabled': enabled, 'repository': repo}
    json_write(checked(root, SETTINGS), value)
    return value


def begin_build(root):
    checked(root, VERIFIED).unlink(missing_ok=True)
    checked(root, 'build/launch-game.json').unlink(missing_ok=True)


def source_files(env):
    root = Path(env['ROOT'])
    files = {name: checked(root, 'build/out/' + Path(name).name) for name in PAKS}
    if sorted(Path(name).name for name in PAKS) != sorted(env['MOD_FILES']):
        raise SyncError('The engine mod filenames changed; update Deck sync before publishing.')
    leader = read_json(checked(root, 'build/field-leader/payload.json'))
    if not isinstance(leader, dict) or leader.get('schema') != 1 or not isinstance(leader.get('files'), dict):
        raise SyncError('Rebuild with the current Studio to prepare the cycling payload.')
    names = set(leader['files'])
    if names not in (set(), {'enabled.txt', 'Scripts/config.lua', 'Scripts/main.lua'}):
        raise SyncError('Unsupported field cycling payload.')
    game = Path(env['ffrenv'].game_root())
    if names:
        for name in REQUIRED_LOADER:
            if not checked(game, name).is_file():
                raise SyncError('Prepare the working UE4SS loader on the PC before publishing character cycling.')
        for name in LOADER_FILES:
            if checked(game, name).is_file():
                files[name] = checked(game, name)
        signatures = checked(game, BINARY + 'ue4ss/UE4SS_Signatures')
        if signatures.exists():
            for path in sorted(signatures.iterdir()):
                relative = path.relative_to(game).as_posix()
                if not allowed(relative) or not path.is_file():
                    raise SyncError('Unsupported UE4SS signature file; no package published.')
                files[relative] = checked(game, relative)
    for name, path in files.items():
        if not path.is_file() or path.stat().st_size <= 0:
            raise SyncError('A finished mod file is missing. Rebuild before publishing.')
    return game, files, leader


# Transfer identity covers every official top-level container header and size.
# ~mods is deliberately excluded, so installed mods cannot identify the game.
def game_identity(game):
    paks = checked(game, 'FFRS/Content/Paks')
    containers = {}
    for path in sorted(paks.iterdir()):
        if path.suffix.lower() not in ('.utoc', '.ucas', '.pak') or not path.is_file():
            continue
        checked(paks, path.name)
        containers[path.name] = {'size': path.stat().st_size,
                                 **({'sha256': sha(path)} if path.suffix.lower() == '.utoc' else {})}
    if 'FFRS-Windows.utoc' not in containers:
        raise SyncError('Select the Resonance folder containing FFRS/Content/Paks/FFRS-Windows.utoc.')
    digest = hashlib.sha256(json.dumps(containers, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'schema': 1, 'sha256': digest, 'containers': containers}


STUDIO_INPUTS = ('units.json', 'icon_layout.json', 'testing.json', 'ability-modes.json', 'sephira-settings.json')


def inputs_digest(root):
    files = {name: sha(checked(root, 'mods/EstherTsukiko/' + name))
             for name in STUDIO_INPUTS if checked(root, 'mods/EstherTsukiko/' + name).is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def local_snapshot(env, output):
    """Self-contained offline installer; no repository, token or network call."""
    with tempfile.TemporaryDirectory(prefix='ffr-local-snapshot-') as folder:
        package = Path(folder) / 'mod.zip'
        manifest = make_package(env, package)
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED, allowZip64=True) as bundle:
            bundle.write(package, 'mod.zip')
            info = zipfile.ZipInfo('Install snapshot.sh')
            info.create_system = 3
            info.external_attr = 0o100755 << 16
            bundle.writestr(info, '#!/usr/bin/env bash\nset -euo pipefail\nsnapshot_dir="$(cd -- "$(dirname -- "$0")" && pwd)"\nexec python3 "$snapshot_dir/Deck Mod Sync.py" --snapshot "$snapshot_dir/mod.zip" --interactive "$@"\n')
            bundle.writestr('Deck Mod Sync.py', Path(__file__).read_bytes())
            bundle.writestr('Read me.txt',
                'Extract the whole ZIP on Steam Deck. Close Resonance. In Desktop Mode run:\n'
                'bash "Install snapshot.sh"\n'
                'Select/detect your Resonance game folder. No GitHub, token, Studio or building is needed.\n'
                'Both computers must have the same game build. A later snapshot replaces this mod and removes its stale runtime files.\n'
                'Backups and the restore shortcut stay under Downloads/FFR Mod/Deck Sync.\n'
                'If runtime scripts are included (Crystal Fina or walking-character cycling), set this game Steam launch option:\n'
                'WINEDLLOVERRIDES="dwmapi=n,b" %command%\n'
                'This is a finished mod snapshot. Use the separate Studio backup to transfer editable units/settings. Game saves are separate.\n')
    return manifest


def import_snapshot(root, game, archive, running=None):
    root, game, archive = Path(root), Path(game), Path(archive)
    running = running or game_running
    if not archive.is_file() or archive.stat().st_size > MAX_ZIP:
        raise SyncError('Choose a finished mod snapshot ZIP (mod.zip inside the exported folder).')
    with tempfile.TemporaryDirectory(prefix='snapshot-', dir=root) as folder:
        manifest = validate_package(archive, folder)
        return install(root, game, folder, manifest, '', running=running)


def capture(env):
    """Called only by the completed, verified build; later edits cannot alter it."""
    root = Path(env['ROOT'])
    game, files, leader = source_files(env)
    record = {'schema': 1, 'id': uuid.uuid4().hex, 'created': dt.datetime.now(dt.timezone.utc).isoformat(),
              'gameSha256': sha(checked(game, MARKER)),
              'gameIdentity': game_identity(game), 'inputsSha256': inputs_digest(root),
              'files': {k: {'sha256': sha(v), 'size': v.stat().st_size} for k, v in files.items()},
              'leader': leader, 'engine': env.get('ENGINE_VERSION', '')}
    # No PC paths, tokens, Studio config, or saves in the exported manifest.
    json_write(checked(root, VERIFIED), record)
    return record


def make_package(env, output):
    root = Path(env['ROOT'])
    record = read_json(checked(root, VERIFIED))
    if (not isinstance(record, dict) or record.get('schema') != 1
            or not {'gameIdentity', 'inputsSha256'} <= set(record)):
        raise SyncError('Build successfully with this Studio before exporting or publishing.')
    game, files, leader = source_files(env)
    if (record['gameSha256'] != sha(checked(game, MARKER)) or record.get('gameIdentity', game_identity(game)) != game_identity(game)
            or record.get('inputsSha256', inputs_digest(root)) != inputs_digest(root) or record['leader'] != leader
            or set(record['files']) != set(files)):
        raise SyncError('The game, Studio settings or runtime changed since the build. Rebuild before exporting or publishing.')
    manifest = {k: record[k] for k in ('schema', 'id', 'created', 'gameSha256', 'engine')}
    manifest.update(channel=CHANNEL, files=dict(record['files']))
    if 'gameIdentity' in record: manifest['gameIdentity'] = record['gameIdentity']
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as bundle:
        for name, path in files.items():
            expected = record['files'][name]
            if path.stat().st_size != expected['size'] or sha(path) != expected['sha256']:
                raise SyncError('Build output changed. Rebuild before publishing.')
            bundle.write(path, 'files/' + name)
        for name, text in leader['files'].items():
            if not isinstance(text, str):
                raise SyncError('Invalid cycling script.')
            data = text.encode('utf-8')
            relative = LEADER + name
            manifest['files'][relative] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            bundle.writestr('files/' + relative, data)
        bundle.writestr('manifest.json', json.dumps(manifest))
    if Path(output).stat().st_size > MAX_ZIP:
        raise SyncError('This finished mod exceeds the supported snapshot size limit (2 GiB).')
    # Validate the actual streamed ZIP, catching concurrent changes before upload.
    with tempfile.TemporaryDirectory(prefix='ffr-package-check-') as temporary:
        validate_package(output, Path(temporary))
    if record['inputsSha256'] != inputs_digest(root) or record['gameIdentity'] != game_identity(game):
        raise SyncError('Game or Studio inputs changed during export. Rebuild before exporting again.')
    return manifest


def publish(env, github=GitHub, credentials=None):
    root = Path(env['ROOT'])
    saved = settings(root)
    if not saved['enabled']:
        raise SyncError('Personal sync is off. No files were uploaded.')
    repo = saved['repository']
    secret = (credentials or CredentialStore(root)).get(repo)
    client = github(secret)
    info = client.private(repo, publishing=True)
    release = None
    try:
        with tempfile.TemporaryDirectory(prefix='ffr-private-publish-') as temporary:
            archive = Path(temporary) / 'Resonance-Mod.zip'
            manifest = make_package(env, archive)
            digest = sha(archive)
            tag = 'deck-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S-') + manifest['id'][:12]
            metadata = {'schema': 1, 'channel': CHANNEL, 'repository': repo,
                        'packageId': manifest['id'], 'sha256': digest, 'gameSha256': manifest['gameSha256']}
            release = client.api('/repos/' + repo + '/releases', 'POST',
                                 {'tag_name': tag, 'target_commitish': info['default_branch'], 'name': 'My Resonance mod',
                                  'draft': True, 'prerelease': False, 'body': json.dumps(metadata)})
            endpoint = '/repos/' + repo + '/releases/' + str(release['id'])
            with archive.open('rb') as stream:
                with client.request(endpoint + '/assets?name=Resonance-Mod.zip', 'POST', stream=stream, size=archive.stat().st_size) as response:
                    asset = json.loads(response.read(1024**2))
            if asset.get('digest') != 'sha256:' + digest:
                raise SyncError('GitHub did not verify the uploaded package checksum. The release stays unpublished.')
            client.private(repo, publishing=True)
            client.api(endpoint, 'PATCH', {'draft': False})
            return {'result': 'ok', 'message': 'Published your finished mod. Run Update my mod on the Deck.',
                    'packageId': manifest['id'], 'repository': repo, 'tag': tag}
    except BaseException:
        if release:
            try:
                client.api('/repos/' + repo + '/releases/' + str(release['id']), 'DELETE')
            except Exception:
                pass  # A draft is never selected by the Deck installer.
        raise


def validate_package(archive, destination):
    """Reject anything outside the manifest/allowlist before any game-file write."""
    destination = Path(destination)
    try:
        with zipfile.ZipFile(archive) as bundle:
            members = bundle.infolist()
            names = [member.filename for member in members]
            if len(names) != len(set(names)) or len(names) > 200 or 'manifest.json' not in names:
                raise SyncError('Invalid or duplicate package members.')
            info = bundle.getinfo('manifest.json')
            if info.file_size > 256 * 1024 or sum(x.file_size for x in members) > MAX_TOTAL:
                raise SyncError('The package exceeds transfer size limits.')
            manifest = json.loads(bundle.read(info))
            if (manifest.get('schema') != 1 or manifest.get('channel') != CHANNEL
                    or not re.fullmatch(r'[0-9a-f]{32}', manifest.get('id', ''))
                    or not re.fullmatch(r'[0-9a-f]{64}', manifest.get('gameSha256', ''))
                    or not isinstance(manifest.get('files'), dict)):
                raise SyncError('Unsupported finished-mod manifest.')
            files = manifest['files']
            if not set(PAKS).issubset(files) or set(names) != {'manifest.json', *('files/' + k for k in files)}:
                raise SyncError('The mod package is incomplete or contains extra files.')
            runtime = set(files) & set(LEADER_FILES)
            if runtime and (runtime != set(LEADER_FILES) or not set(REQUIRED_LOADER).issubset(files)):
                raise SyncError('The cycling runtime is incomplete.')
            if not runtime and any(k not in PAKS for k in files):
                raise SyncError('A loader without the cycling mod is unsupported.')
            for name, expected in files.items():
                if not allowed(name) or not isinstance(expected, dict) or set(expected) != {'size', 'sha256'}:
                    raise SyncError('The package contains an unsupported game file.')
                target = checked(destination, name)
                member = bundle.getinfo('files/' + name)
                mode = member.external_attr >> 16
                if (member.is_dir() or stat.S_ISLNK(mode) or mode & 0o170000 not in (0, stat.S_IFREG)
                        or type(expected['size']) is not int or not 0 <= expected['size'] <= MAX_TOTAL
                        or member.file_size != expected['size'] or not re.fullmatch(r'[0-9a-f]{64}', expected['sha256'])):
                    raise SyncError('Invalid package file size, type or checksum.')
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as source, target.open('wb') as out:
                    shutil.copyfileobj(source, out, length=1024**2)
                if sha(target) != expected['sha256']:
                    raise SyncError('A transferred mod file failed its checksum.')
            return manifest
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError) as error:
        raise SyncError('The downloaded mod package is invalid.') from error


def latest(client, repo):
    client.private(repo)
    releases = client.api('/repos/' + repo + '/releases?per_page=100')
    candidates = []
    for release in releases:
        if release.get('draft') or release.get('prerelease') or not release.get('published_at'):
            continue
        try:
            metadata = json.loads(release.get('body') or '')
            if (metadata.get('channel') != CHANNEL or metadata.get('schema') != 1
                    or metadata.get('repository', '').lower() != repo.lower()
                    or not re.fullmatch(r'[0-9a-f]{32}', metadata.get('packageId', ''))
                    or not re.fullmatch(r'[0-9a-f]{64}', metadata.get('gameSha256', ''))
                    or not re.fullmatch(r'[0-9a-f]{64}', metadata.get('sha256', ''))):
                continue
            assets = [a for a in release.get('assets', []) if a.get('name') == 'Resonance-Mod.zip']
            if (len(assets) != 1 or assets[0].get('digest') != 'sha256:' + metadata['sha256']
                    or type(assets[0].get('id')) is not int or not 0 < assets[0].get('size', 0) <= MAX_ZIP):
                continue
            candidates.append((release, metadata, assets[0]))
        except (ValueError, TypeError):
            continue
    if not candidates:
        raise SyncError('No finished mod has been published to this private repository yet.')
    return max(candidates, key=lambda item: (item[0]['published_at'], item[0]['id']))


def download(client, repo, asset, digest, destination):
    with client.request('/repos/' + repo + '/releases/assets/' + str(asset['id']), accept='application/octet-stream') as response:
        total = 0
        with Path(destination).open('wb') as stream:
            while True:
                chunk = response.read(1024**2)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP or total > asset['size']:
                    raise SyncError('Downloaded package exceeds the declared size.')
                stream.write(chunk)
    if total != asset['size'] or sha(destination) != digest:
        raise SyncError('The download is incomplete or failed its checksum. Your installed mod was kept.')


def game_running():
    if sys.platform == 'win32':
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq FFRS-Win64-Shipping.exe'],
                                    capture_output=True, text=True, timeout=15)
            if result.returncode: raise SyncError('Could not check the game process. Close Resonance and retry.')
            return 'ffrs-win64-shipping.exe' in result.stdout.lower()
        except (OSError, subprocess.SubprocessError) as error:
            raise SyncError('Could not check the game process. Close Resonance and retry.') from error
    proc = Path('/proc')
    if not proc.is_dir():
        return False
    for path in proc.glob('[0-9]*/cmdline'):
        try:
            args = path.read_bytes().split(b'\0')
            if any(a.replace(b'\\', b'/').split(b'/')[-1].lower() == b'ffrs-win64-shipping.exe' for a in args):
                return True
        except OSError:
            continue
    return False


@contextmanager
def locked(root):
    path = checked(root, 'installer.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        if sys.platform == 'win32':
            import msvcrt
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b'\0'); stream.flush()
            stream.seek(0)
            try: msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error: raise SyncError('Another Deck update is already running.') from error
            try: yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error: raise SyncError('Another Deck update is already running.') from error
            try: yield
            finally: fcntl.flock(stream, fcntl.LOCK_UN)


def copy_atomic(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.ffr-sync-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream, Path(source).open('rb') as src:
            shutil.copyfileobj(src, stream, length=1024**2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def recover(root, running=game_running):
    """Finish rolling back an interrupted installation before another update."""
    journal_path = checked(root, 'install-journal.json')
    record = read_json(journal_path)
    if record is None:
        return False
    if running():
        raise SyncError('Close Resonance before recovering the interrupted update.')
    if (not isinstance(record, dict) or record.get('schema') != 1
            or not re.fullmatch(r'backups/[0-9a-f]{32}', record.get('backup', ''))
            or not isinstance(record.get('before'), dict) or not isinstance(record.get('after'), dict)
            or set(record['before']) != set(record['after']) or not isinstance(record.get('game'), str)):
        raise SyncError('An interrupted install record is invalid. No game files changed.')
    game = Path(record['game'])
    if not checked(game, MARKER).is_file():
        raise SyncError('The game folder is unavailable. Reconnect its drive before recovering the update.')
    for name, before in record['before'].items():
        after = record['after'][name]
        if not allowed(name) or any(d is not None and not re.fullmatch(r'[0-9a-f]{64}', d) for d in (before, after)):
            raise SyncError('Invalid interrupted-install file record.')
        target = checked(game, name)
        current = sha(target) if target.is_file() else None
        permitted = {before, after}
        if name == LEADER + 'enabled.txt':
            permitted.add(None)
        if current not in permitted:
            raise SyncError('A file changed after the interrupted install; recovery will preserve it.')
        if before is not None:
            backup = checked(root, record['backup'] + '/' + name)
            if not backup.is_file() or sha(backup) != before:
                raise SyncError('Interrupted-install backup checksum mismatch.')
    state = checked(root, 'installed-state.json')
    prior = record.get('previousState')
    if prior is not None:
        try:
            value = json.loads(prior)
        except (ValueError, TypeError) as error:
            raise SyncError('Invalid interrupted-install state backup.') from error
        if value.get('schema') != 1 or value.get('game') != str(game):
            raise SyncError('Interrupted-install state belongs to another game.')
    for name, before in record['before'].items():
        target = checked(game, name)
        if before is None:
            target.unlink(missing_ok=True)
        else:
            copy_atomic(checked(root, record['backup'] + '/' + name), target)
    if prior is None:
        state.unlink(missing_ok=True)
    else:
        atomic(state, prior.encode())
    journal_path.unlink()
    return True


def install(root, game, staging, manifest, repo, running=game_running):
    """Own only listed files; preserve originals, remove stale mods, rollback errors."""
    root, game, staging = Path(root), Path(game).resolve(), Path(staging)
    if running():
        raise SyncError('Close Resonance before updating the mod.')
    recover(root, running)
    marker = checked(game, MARKER)
    if (not marker.is_file() or sha(marker) != manifest['gameSha256']
            or ('gameIdentity' in manifest and game_identity(game) != manifest['gameIdentity'])):
        raise SyncError('The Deck game version differs from the PC build. Update both games and rebuild on the PC.')
    state_path = checked(root, 'installed-state.json')
    previous_raw = state_path.read_bytes() if state_path.exists() else None
    previous = read_json(state_path, {'schema': 1, 'game': str(game), 'files': {}, 'originals': {}})
    if (previous.get('schema') != 1 or not isinstance(previous.get('files'), dict)
            or not isinstance(previous.get('originals'), dict)):
        raise SyncError('Unsupported saved installation record.')
    if previous.get('game') != str(game) and (previous['files'] or previous['originals']):
        raise SyncError('The saved install belongs to another game folder. Restore it before switching folders.')
    old, new = previous['files'], manifest['files']
    originals = dict(previous['originals'])
    affected = set(old) | set(new)
    for name in affected | set(originals):
        if not allowed(name):
            raise SyncError('Unsupported file in the install record.')
    for name, digest in old.items():
        target = checked(game, name)
        if target.exists() and (not target.is_file() or sha(target) != digest):
            raise SyncError('A previously installed mod file was changed outside sync. Restore that file before updating.')
    for name, expected in new.items():
        source = checked(staging, name)
        if not source.is_file() or source.stat().st_size != expected['size'] or sha(source) != expected['sha256']:
            raise SyncError('The staged package changed before installation.')
        target = checked(game, name)
        if name not in old and target.exists() and name not in PAKS and sha(target) != expected['sha256']:
            raise SyncError('An existing runtime loader or mod differs. Keep it separate or remove it before syncing cycling.')
    stamp = uuid.uuid4().hex
    backup = checked(root, 'backups/' + stamp)
    before = {}
    for name in sorted(affected):
        target = checked(game, name)
        if target.exists() and not target.is_file():
            raise SyncError('A mod destination is not a file.')
        before[name] = sha(target) if target.is_file() else None
        if target.is_file():
            copy_atomic(target, checked(backup, name))
        if name not in originals:
            originals[name] = {'backup': 'backups/' + stamp + '/' + name, 'sha256': before[name]} if before[name] else None
    for name, saved in originals.items():
        if saved:
            if (not isinstance(saved, dict) or not isinstance(saved.get('backup'), str)
                    or not saved['backup'].startswith('backups/') or not re.fullmatch(r'[0-9a-f]{64}', saved.get('sha256', ''))):
                raise SyncError('Invalid original-file backup record.')
            if not checked(root, saved['backup']).is_file() or sha(checked(root, saved['backup'])) != saved['sha256']:
                raise SyncError('An original-file backup is damaged. No game files changed.')
    written = []
    journal = checked(root, 'install-journal.json')
    json_write(journal, {'schema': 1, 'game': str(game), 'backup': 'backups/' + stamp, 'before': before,
                        'after': {k: new[k]['sha256'] if k in new else originals[k]['sha256'] if originals[k] else None for k in affected},
                        'previousState': previous_raw.decode() if previous_raw is not None else None})
    try:
        if running():
            raise SyncError('Resonance started during the update. Close it and try again.')
        # Disable the cycling mod first, enable it after every other file is ready.
        enable = LEADER + 'enabled.txt'
        order = [enable] if enable in affected else []
        order += sorted(affected - {enable})
        if enable in affected:
            order += [enable]
        for index, name in enumerate(order):
            target = checked(game, name)
            if name not in written:
                now = sha(target) if target.is_file() else None
                if now != before[name]:
                    raise SyncError('A game file changed during installation.')
                written.append(name)
            if name == enable and index == 0:
                # First visit disables; the second visit deploys the final file.
                if target.exists():
                    target.unlink()
                continue
            if name in new:
                copy_atomic(checked(staging, name), target)
                if sha(target) != new[name]['sha256']:
                    raise SyncError('An installed mod file failed its checksum.')
            elif originals[name]:
                copy_atomic(checked(root, originals[name]['backup']), target)
            else:
                target.unlink(missing_ok=True)
        json_write(state_path, {'schema': 1, 'game': str(game), 'repository': repo, 'packageId': manifest['id'],
                               'files': {k: v['sha256'] for k, v in new.items()},
                               'originals': {k: originals[k] for k in new}})
        journal.unlink()
    except BaseException:
        for name in reversed(written):
            target = checked(game, name)
            if before[name] is None:
                target.unlink(missing_ok=True)
            else:
                copy_atomic(checked(backup, name), target)
        if previous_raw is None:
            state_path.unlink(missing_ok=True)
        else:
            atomic(state_path, previous_raw)
        journal.unlink(missing_ok=True)
        raise
    return {'files': len(new), 'cycling': LEADER + 'enabled.txt' in new}


def restore(root, running=game_running):
    recover(root, running)
    value = read_json(checked(root, 'installed-state.json'))
    if not value or not value.get('files'):
        return False
    game = Path(value['game'])
    marker = checked(game, MARKER)
    manifest = {'id': uuid.uuid4().hex, 'gameSha256': sha(marker), 'files': {}}
    install(root, game, root, manifest, value.get('repository', ''), running)
    return True


def steam_games():
    libraries = []
    for base in (Path.home() / '.local/share/Steam', Path.home() / '.steam/steam'):
        if base.is_dir():
            libraries.append(base.resolve())
            vdf = base / 'steamapps/libraryfolders.vdf'
            if vdf.is_file():
                libraries += [Path(p.replace('\\\\', '\\')) for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text())]
    games = []
    for lib in dict.fromkeys(libraries):
        common = lib / 'steamapps/common'
        for path in sorted(common.glob('*')):
            if (path / MARKER).is_file() and path.resolve() not in games:
                games.append(path.resolve())
    return games


def deck_update(root, game, repo, token, github=GitHub):
    if game_running():
        raise SyncError('Close Resonance before updating the mod.')
    client = github(token)
    release, metadata, asset = latest(client, repo)
    with tempfile.TemporaryDirectory(prefix='download-', dir=root) as temporary:
        archive = Path(temporary) / 'mod.zip'
        print('Downloading your published mod...', flush=True)
        download(client, repo, asset, metadata['sha256'], archive)
        staging = Path(temporary) / 'files'
        manifest = validate_package(archive, staging)
        if manifest['id'] != metadata['packageId'] or manifest['gameSha256'] != metadata['gameSha256']:
            raise SyncError('The release does not match its package manifest.')
        result = install(root, game, staging, manifest, repo)
    print(f"Installed {result['files']} files from {release['tag_name']}. Backups are kept in {root / 'backups'}.")
    if result['cycling']:
        print('For character cycling, set this game’s Steam Launch Options to:')
        print('WINEDLLOVERRIDES="dwmapi=n,b" %command%')
    return result


def desktop_shortcut(script, root):
    # Desktop files use their own quoting/percent rules; never invoke a shell.
    def quoted(value):
        return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
    content = '[Desktop Entry]\nType=Application\nName=Update my Resonance mod\nTerminal=true\nIcon=system-software-update\nExec=' + \
              ' '.join(quoted(v) for v in (sys.executable, script, '--root', root, '--interactive')) + '\n'
    for directory in (Path.home() / 'Desktop', Path.home() / '.local/share/applications'):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / 'Resonance Mod Sync.desktop'
        atomic(path, content.encode())
        path.chmod(0o755)


def deck_main():
    parser = argparse.ArgumentParser(description='Install your privately published PC mod on Steam Deck. No Studio or building.')
    parser.add_argument('--root', type=Path, default=Path.home() / 'Downloads/FFR Mod/Deck Sync')
    parser.add_argument('--game', type=Path)
    parser.add_argument('--repository')
    parser.add_argument('--snapshot', type=Path, help='Install a local finished mod ZIP without GitHub.')
    parser.add_argument('--restore', action='store_true')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument('--forget-token', action='store_true')
    args = parser.parse_args()
    root = args.root.absolute()
    root.mkdir(parents=True, exist_ok=True)
    try:
        with locked(root):
            cfg = read_json(checked(root, 'deck-settings.json'), {})
            if args.restore:
                print('Restored.' if restore(root) else 'No synced mod to restore.')
                return 0
            # Local import branches before any credentials/repository work.
            local = args.snapshot
            if args.interactive and not local:
                print('1 — Import local mod snapshot\n2 — Restore files from before importing\n3 — GitHub sync (optional)\nEnter — Exit')
                action = input('Choose: ').strip()
                if not action: return 0
                if action == '2':
                    print('Restored.' if restore(root) else 'No installed snapshot to restore.')
                    return 0
                if action == '1':
                    local = Path(input('Path to mod.zip from the exported snapshot: ').strip().strip('"'))
                elif action != '3': raise SyncError('Choose one of the listed actions.')
            if local:
                game = args.game or (Path(cfg['game']) if cfg.get('game') else None)
                if game is None:
                    found = steam_games()
                    game = found[0] if len(found) == 1 else Path(input('Resonance game folder: ').strip().strip('"'))
                result = import_snapshot(root, game.resolve(), local)
                json_write(checked(root, 'deck-settings.json'), {**cfg, 'game': str(game.resolve())})
                helper = checked(root, 'Deck Mod Sync.py')
                atomic(helper, Path(__file__).read_bytes())
                desktop_shortcut(helper, root)
                print('Snapshot installed. No download or build was needed.')
                if result['cycling']:
                    print('Steam launch option for the included runtime: WINEDLLOVERRIDES="dwmapi=n,b" %command%')
                return 0
            repo = args.repository or cfg.get('repository')
            vault = CredentialStore(root)
            if args.forget_token:
                repo = repository(repo or input('Your private GitHub repository (owner/name): ').strip())
                vault.delete(repo)
                print('Local token removed.')
                return 0
            if args.interactive:
                print('1 — Download/install my published mod\n2 — Restore files from before syncing\n3 — Change repository/game folder\n4 — Forget saved token\nEnter — Exit')
                action = input('Choose: ').strip()
                if not action:
                    return 0
                if action == '2':
                    print('Restored.' if restore(root) else 'No synced mod to restore.')
                    return 0
                if action == '4':
                    repo = repository(repo or input('Your private GitHub repository (owner/name): ').strip())
                    vault.delete(repo)
                    print('Local token removed.')
                    return 0
                if action == '3':
                    repo = repository(input('Private repository (owner/name): ').strip())
                    choice = input('Resonance game folder (Enter to detect Steam libraries): ').strip().strip('"')
                    cfg = {'game': choice} if choice else {}
                elif action != '1':
                    raise SyncError('Choose one of the listed actions.')
            repo = repository(repo or input('Your private GitHub repository (owner/name): ').strip())
            game = args.game or (Path(cfg['game']) if cfg.get('game') else None)
            if game is None:
                found = steam_games()
                if len(found) == 1:
                    game = found[0]
                    print('Found Resonance: ' + str(game))
                else:
                    for path in found:
                        print(path)
                    game = Path(input('Resonance game folder: ').strip().strip('"'))
            if not (game / MARKER).is_file():
                raise SyncError('That folder does not contain FFRS/Content/Paks/FFRS-Windows.utoc.')
            token = vault.get(repo)
            if not token:
                print('Use a fine-grained GitHub token with Contents: read on your private repository.')
                token = getpass.getpass('Token (hidden): ').strip()
                GitHub(token).private(repo)
                if vault.linux_backend() and input('Remember in the local Linux keyring / KWallet? [y/N]: ').strip().lower() == 'y':
                    vault.put(repo, token)
                elif not vault.linux_backend():
                    print('No Linux keyring is available; the token will be requested each update and will not be saved.')
            deck_update(root, game.resolve(), repo, token)
            json_write(checked(root, 'deck-settings.json'), {'repository': repo, 'game': str(game.resolve())})
            helper = checked(root, 'Deck Mod Sync.py')
            atomic(helper, Path(__file__).read_bytes())
            helper.chmod(0o755)
            desktop_shortcut(helper, root)
            return 0
    except (SyncError, OSError, ValueError, KeyboardInterrupt, EOFError, subprocess.SubprocessError):
        # Print only safe exceptions. Network errors may contain signed URLs.
        error = sys.exc_info()[1]
        print('ERROR: ' + (str(error) if isinstance(error, SyncError) else 'Update interrupted or a local file could not be read/written.'), file=sys.stderr)
        return 1
    finally:
        if args.interactive and sys.stdin.isatty():
            input('Press Enter to close...')


def register(app, env):
    from fastapi import HTTPException, Request
    # FastAPI resolves annotated Request against the module globals.
    globals()['Request'] = Request
    root = Path(env['ROOT'])
    def status():
        saved = settings(root)
        vault = CredentialStore(root)
        return {**saved, 'hasToken': bool(saved['repository'] and vault.get(saved['repository'])),
                'ready': checked(root, VERIFIED).is_file(), **_publishing}

    @app.get('/api/deck/status')
    def deck_status():
        try:
            return status()
        except (SyncError, OSError) as error:
            raise HTTPException(409, str(error)) from error

    @app.put('/api/deck/settings')
    async def deck_settings(req: Request):
        body = await req.json()
        with _operation:
            if _publishing['running'] or env.get('state', {}).get('running'):
                raise HTTPException(409, 'Wait for the current build/publish to finish.')
            try:
                configure(root, body.get('enabled'), body.get('repository', ''), body.get('token') or None)
                return status()
            except (SyncError, OSError) as error:
                raise HTTPException(422, str(error)) from error

    @app.delete('/api/deck/token')
    def forget_token():
        with _operation:
            if _publishing['running']:
                raise HTTPException(409, 'Wait for publishing to finish.')
            saved = settings(root)
            if saved['repository']:
                CredentialStore(root).delete(saved['repository'])
            json_write(checked(root, SETTINGS), {**saved, 'enabled': False})
            return status()

    def worker():
        try:
            result = publish(env)
            _publishing.update(result)
        except Exception as error:
            _publishing.update(result='failed', message=str(error) if isinstance(error, SyncError) else 'Publishing failed. Your existing release was kept.')
        finally:
            _publishing['running'] = False

    @app.post('/api/deck/publish')
    def deck_publish():
        with _operation:
            if env.get('state', {}).get('running') or _publishing['running']:
                raise HTTPException(409, 'A build or publish is running.')
            if not settings(root)['enabled'] or not checked(root, VERIFIED).is_file():
                raise HTTPException(409, 'Enable personal sync and build successfully before publishing.')
            _publishing.update(running=True, result=None, message='Packaging and publishing your mod...')
            threading.Thread(target=worker, daemon=True).start()
            return {'ok': True}


if __name__ == '__main__':
    sys.exit(deck_main())
