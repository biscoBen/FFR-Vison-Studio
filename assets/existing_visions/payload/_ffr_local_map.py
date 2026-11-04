"""Checked native local-map configuration; the existing HUD owns its lifetime."""
import hashlib
import io
from pathlib import Path
import zipfile

# Filled from the pinned native SDK's compiled/read-back assets.
ASSETS = {'FFRS/Content/UI/Field/MiniMap/Data/DA_MiniMapProperty.uasset': 'f7da1eb7158e084081e1a8e8abcb1c136b1cd242c9bde5c366fd415c63c5f4af', 'FFRS/Content/UI/Field/MiniMap/Data/DA_MiniMapViewProperty.uasset': '92cc7b5fb01541996cfe26f1456f937894b641339ab9598a2e837ac6e8e86655', 'FFRS/Content/UI/Field/MiniMap/Data/DA_MiniMapProperty.uexp': '017212739b487918202da9091323f3b8253f859c2306bef4c29d1070e29f2e64', 'FFRS/Content/UI/Field/MiniMap/Data/DA_MiniMapViewProperty.uexp': '8f82e8f7605b108784474201917250ec07fd87228498b1d3895b8616cdde702a'}


def validate(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.namelist()) != len(ASSETS) or set(archive.namelist()) != set(ASSETS):
            raise ValueError('Incomplete full local-map assets.')
        files = {name: archive.read(name) for name in ASSETS}
    if any(hashlib.sha256(raw).hexdigest() != ASSETS[name] for name, raw in files.items()):
        raise ValueError('Full local-map asset checksum mismatch.')
    return files


def stage(out):
    from _ffr_field_leader import atomic, checked
    files = validate(Path(__file__).with_name('local_map.zip').read_bytes())
    for name, raw in files.items():
        atomic(checked(out, name), raw)
