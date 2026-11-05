"""Checked stat-page layout; the native WidgetTree owns every added label."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uasset': '733d3a846e040c487bda0d22e844e4cf86833cffaa9a2c4f377c93325f63491c', 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uexp': 'b61f1446b4f8cfc426ceb917f55da7da2023b235829fa7d190ab6b37fead9629', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uasset': '8f2114eefab7ac4945b942a1aef6b95324dd2c523c56c7e5dcf42eb4f0ccc2cc', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uexp': 'ab52031cdab23bcde20fcd0aacd10f3b3c3ae763d8ca450a8ce7ada9efc4ab48', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uasset': 'ebc5af8e957cfa18591b7b4b2f913890d6bb2bd9bdf65db7167f0e85cb268d8b', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uexp': '4f490c10c40e6b40d9f70b55c433c5fb6010cf4fe455058d6456c36a39ae02d8'}


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
