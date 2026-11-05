"""Checked stat-page layout; the native WidgetTree owns every added label."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uasset': 'a8fffe20f8401d8deb91e757d62ee95579adb38cb4f22e84063fdaafbb54034f', 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uexp': '4fa60bdc48da43d307536511dadbd648b6a9bf3f7261706882de551960a1faeb'}


def validate(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.namelist()) != len(ASSETS) or set(archive.namelist()) != set(ASSETS):
            raise ValueError('Incomplete evasion stat-page assets.')
        files = {name: archive.read(name) for name in ASSETS}
    if any(hashlib.sha256(raw).hexdigest() != ASSETS[name] for name, raw in files.items()):
        raise ValueError('Evasion stat-page asset checksum mismatch.')
    return files


def stage(out):
    from _ffr_field_leader import atomic, checked
    files = validate(Path(__file__).with_name('evasion_stats.zip').read_bytes())
    for name, raw in files.items():
        atomic(checked(out, name), raw)
