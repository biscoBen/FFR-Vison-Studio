"""Checked stat-page layout; the native WidgetTree owns every added label."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uasset': '733d3a846e040c487bda0d22e844e4cf86833cffaa9a2c4f377c93325f63491c', 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uexp': 'b61f1446b4f8cfc426ceb917f55da7da2023b235829fa7d190ab6b37fead9629', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uasset': 'c97a6839fa4de58f64a51694467470ddf9bf9f73e9ba0bb6ff27750a65eb82aa', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uexp': 'a7183bc631981af34aad8a7b2236833185f4c31b857e8fdf018bc822f1bb50e4', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uasset': 'ebc25a20c649b26aec78e0d3106299cf6a2ddcf7f504642a0d4faa6bee5ee30a', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uexp': '38438799dc1097f8189762abe2676bc9ec341ceec38feeb2f7c9a129e0351b2a'}


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
