"""Package the external session watcher and offline collector without a Lua mod."""
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SOURCES={
    'Run Diagnostic Session.cmd':'scripts/reference/game-crash/Run Diagnostic Session.cmd',
    'Collect Resonance Crash.cmd':'scripts/reference/game-crash/Collect Resonance Crash.cmd',
    'Collect Resonance Crash.ps1':'scripts/reference/game-crash/Collect Resonance Crash.ps1',
    'DiagnosticSession.ps1':'scripts/reference/common/DiagnosticSession.ps1',
    'Read me.txt':'scripts/reference/game-crash/Read me.txt',
}


def build(output):
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,source in SOURCES.items():
            info=zipfile.ZipInfo(name,(2026,10,28,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(ROOT/source).read_bytes())
    return output


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'scripts/reference/game-crash/Game-Diagnostic-Session.zip')
    print(build(parser.parse_args().output))
