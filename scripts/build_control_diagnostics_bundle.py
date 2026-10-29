"""Package the existing read-only session watcher for Studio control traces."""
import argparse
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def build(destination):
    folder=ROOT/'scripts/reference/game-crash'
    files={
        'Collect Resonance Crash.ps1':(folder/'Collect Resonance Crash.ps1').read_bytes(),
        'DiagnosticSession.ps1':(ROOT/'scripts/reference/common/DiagnosticSession.ps1').read_bytes(),
        'Run Control Diagnostic Session.cmd':(
            '@echo off\r\n'
            'powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Collect Resonance Crash.ps1" -WatchGame -OpenOutput %*\r\n'
            'if errorlevel 1 (\r\n  echo.\r\n  pause\r\n)\r\n').encode(),
        'Read me.txt':(
            'Use Studio 1.2.132 or later. Rebuild/install with the desired in-game controls ON, then close the game.\n'
            'Extract this entire ZIP and run Run Control Diagnostic Session.cmd.\n'
            'Leave its window open and launch Resonance normally.\n\n'
            'Turn encounters OFF, walk until a random battle starts (if one does), and test auto-battle.\n'
            'With auto-battle OFF, choose new skills manually, then turn it ON to test the remembered choices.\n'
            'Close the game normally. The helper exports and opens Downloads\\FFR Mod automatically.\n'
            'Upload the new Resonance-Diagnostic-Session-...zip. No F8 is required.\n\n'
            'This installs/enables no observer and changes no game files or saves.\n'
            'The updated normal Studio runtime logs command memory and encounter state at the relevant events.\n'
            'The session helper collects those existing logs, runtime source/config and crash reports after exit.\n'
            'If game discovery cannot find this PC, supply the folder containing FFRS when prompted.\n'
        ).replace('\n','\r\n').encode(),
    }
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,raw in files.items():archive.writestr(name,raw)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None or set(archive.namelist())!=set(files):raise ValueError('Incomplete control diagnostic bundle')
        for name,raw in files.items():
            if archive.read(name)!=raw:raise ValueError('Control diagnostic source mismatch')
    return destination


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args();print(build(args.output))
