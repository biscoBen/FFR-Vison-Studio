"""Checked stat-page layout; the native WidgetTree owns every added label."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uasset': '733d3a846e040c487bda0d22e844e4cf86833cffaa9a2c4f377c93325f63491c', 'FFRS/Content/UI/Common/Info/Unit/SystemStatus/Detail/WBP_UnitParam_Detail.uexp': 'b61f1446b4f8cfc426ceb917f55da7da2023b235829fa7d190ab6b37fead9629', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uasset': '77d6781cd6849d40f9067383c7126becb8fb47e242168327e22727f0cf7a517d', 'FFRS/Content/UI/Studio/Evasion/T_EvasionMagical.uexp': 'ea79bcc647ef0d734ff9c5671ef7744d2150b4330e1df107afae7eb926b31630', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uasset': '1d73966decf9d83494cfa792432683c56f6309a441e7e07703667b9827ef0cde', 'FFRS/Content/UI/Studio/Evasion/T_EvasionPhysical.uexp': '2493f4693cde1fd90c4005e10fd24473ece73b8d9ab9785c76bf85b5ecc01143'}


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
