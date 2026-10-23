"""Package an existing reviewed 6.4-second movie without rerendering its artwork.

Developer tool: requires FFmpeg and WannaCRI 0.3.3. Supply the matching original
score already encoded as mono HCA; the browser preview remains byte-identical to
the reviewed MP4. The game copy uses the tested 1280x720 VP9/USM format.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from build_crystal_fina_cinematic import FPS, FRAMES, HEIGHT, ROOT, SECONDS, WIDTH, package
from cri_usm_movie import normalize


def import_movie(source, scene_path, score_hca, output, destination):
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
    shutil.copyfile(source, preview)
    shutil.copyfile(score_hca, output / 'score.hca')
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
    raw, container = normalize(raw)
    (output / 'crystal-fina.usm').write_bytes(raw)
    report = {
        **scene, 'width': WIDTH, 'height': HEIGHT,
        'artSha256': hashlib.sha256((ROOT / 'artwork/crystal_fina_cinematic.png').read_bytes()).hexdigest(),
        'eyeColor': 'red', 'audioEnding': 'soft awakening chord; no breaking sound',
        'usmCodec': 'VP9', 'audio': 'Matching original score in a separate native HCA bank',
        'maxPictureDataSize': container['maxPictureDataSize'], 'container': container,
        'sourceMovie': {'name': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'width': videos[0]['width'], 'height': videos[0]['height'],
                        'fps': FPS, 'frames': FRAMES, 'seconds': SECONDS},
        'previewMatchesSource': preview.read_bytes() == source.read_bytes(),
        'artworkRerendered': False,
    }
    (output / 'render.json').write_text(json.dumps(report, indent=2) + '\n')
    package(output, destination)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scene', type=Path, required=True)
    parser.add_argument('--score-hca', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    import_movie(args.source, args.scene, args.score_hca, args.output, args.package)
