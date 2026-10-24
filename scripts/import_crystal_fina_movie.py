"""Package an existing reviewed 6.4-second movie without rerendering its artwork.

Developer tool: requires FFmpeg and WannaCRI 0.3.3. Supply the matching original
score encoded as stereo ADX v4 plus its clean WAV. The browser preview retains
the reviewed MP4 video. The game copy uses native 1920x1080 VP9 color and a constant
Sofdec opacity channel for the game's translucent battle movie material.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from build_crystal_fina_cinematic import FPS, FRAMES, ROOT, SECONDS, package
from cri_usm_movie import with_opaque_alpha, with_soundtrack, native_adx

WIDTH, HEIGHT = 1920, 1080


def import_movie(source, scene_path, score_adx, score_wave, output, destination):
    source = source.resolve()
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-count_frames', '-show_streams',
        '-show_format', '-of', 'json', str(source)], text=True))
    videos = [s for s in probe['streams'] if s['codec_type'] == 'video']
    if (len(videos) != 1 or videos[0]['nb_read_frames'] != str(FRAMES)
            or videos[0]['r_frame_rate'] != '30/1'
            or videos[0]['width'] * 9 != videos[0]['height'] * 16
            or abs(float(probe['format']['duration']) - SECONDS) > .001):
        raise ValueError('Expected one 16:9, 30 fps, 192-frame, 6.4-second reviewed movie')
    scene = json.loads(scene_path.read_text())
    if (scene['width'], scene['height'], scene['fps'], scene['frames']) != (
            videos[0]['width'], videos[0]['height'], FPS, FRAMES):
        raise ValueError('Scene provenance does not describe the reviewed movie')
    output.mkdir(parents=True, exist_ok=True)
    preview = output / 'Crystal-Fina-Cinematic-Preview.mp4'
    from rescore_crystal_fina_movie import preview_with_score, video_hash
    preview_with_score(source, score_wave, preview)
    (output / 'score.adx').write_bytes(native_adx(score_adx.read_bytes()))
    shutil.copyfile(score_wave, output / 'score.wav')
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(source), '-map', '0:v:0',
        '-vf', f'scale={WIDTH}:{HEIGHT}:flags=lanczos', '-frames:v', str(FRAMES),
        '-an', '-c:v', 'libvpx-vp9', '-crf', '29', '-b:v', '0', '-row-mt', '1',
        '-threads', '4', '-cpu-used', '3', '-g', '30', '-pix_fmt', 'yuv420p',
        str(output / 'crystal-fina.ivf')], check=True)
    subprocess.run([
        'ffmpeg', '-v', 'error', '-y', '-i', str(source), '-frames:v', '1',
        '-vf', f'scale={WIDTH}:{HEIGHT}:flags=lanczos',
        str(output / 'frame-0001.png')], check=True)
    from wannacri.usm import OpMode, Usm, Vp9
    video = Vp9(str(output / 'crystal-fina.ivf'))
    movie = Usm(videos=[video], version=video.crid_page['fmtver'].val)
    raw = b''.join(movie.stream(OpMode.NONE))
    raw, container = with_opaque_alpha(raw, ROOT / 'scripts/fixtures/fina_opaque_alpha')
    raw, container = with_soundtrack(raw, score_adx.read_bytes())
    (output / 'crystal-fina.usm').write_bytes(raw)
    report = {
        **scene, 'revision': 'crystal-fina-film-3', 'width': WIDTH, 'height': HEIGHT,
        'artSha256': hashlib.sha256((ROOT / 'artwork/crystal_fina_cinematic.png').read_bytes()).hexdigest(),
        'eyeColor': 'red', 'audioEnding': 'light piano opening building into an intense suspended organ ending; no breaking sound',
        'usmCodec': 'VP9', 'alphaCodec': 'SofdecPrime', 'opaqueAlpha': True,
        'alphaFrameSha256': '5d7aecb273db8cebabf70319bdd35c11731bb85312330034dfc45f93994067d3',
        'audio': 'Stereo ADX score embedded in the native Mana movie',
        'embeddedAudio': {'codec': 'Adx', 'channels': 2, 'sampleRate': 48000, 'samples': 307200},
        'maxPictureDataSize': container['maxPictureDataSize'], 'container': container,
        'sourceMovie': {'name': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'width': videos[0]['width'], 'height': videos[0]['height'],
                        'fps': FPS, 'frames': FRAMES, 'seconds': SECONDS},
        'previewMatchesSource': False, 'previewVideoMatchesSource': video_hash(preview)==video_hash(source),
        'previewVideoSha256': video_hash(preview), 'audioReplaced': True,
        'artworkRerendered': False,
        'soundtrack': json.loads(score_wave.with_suffix('.json').read_text()),
    }
    (output / 'render.json').write_text(json.dumps(report, indent=2) + '\n')
    package(output, destination)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--score-adx', type=Path, required=True)
    parser.add_argument('--score-wav', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    import_movie(args.source, args.scene, args.score_adx, args.score_wav, args.output, args.package)
