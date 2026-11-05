"""Checked stat-page layout; the native WidgetTree owns every added label."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uasset': '109b7b8a1203d6bb34bf08c1adc678afe07899f9703234b3e6854f5a67f7c90a', 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uexp': '93b437a5e6c0f7a9cb66fc8142c75e2705c7c7e2ca244b0d794cb448a7503d3e'}


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
