"""Persist optional skill visibility/repairs without rewriting game definitions."""
import json
import os
from pathlib import Path
import tempfile

CONFIG = 'mods/EstherTsukiko/ability-modes.json'


def validate(value):
    if (not isinstance(value, dict) or set(value) != {'schema', 'showUnverified', 'useChanges'}
            or type(value['schema']) is not int or value['schema'] != 1
            or any(type(value[k]) is not bool for k in ('showUnverified', 'useChanges'))):
        raise ValueError('Invalid ability visibility settings.')
    return dict(value)


def settings(root):
    path = Path(root) / CONFIG
    return validate(json.loads(path.read_bytes())) if path.is_file() else {
        'schema': 1, 'showUnverified': False, 'useChanges': False}


def enabled(root):
    value = settings(root)
    return value['showUnverified'] and value['useChanges']


def catalog_controls(catalog, root):
    review = json.loads(Path(__file__).with_name('ability_hiding_review.json').read_bytes())
    if review.get('schema') != 1:
        raise ValueError('Unsupported ability hiding review.')
    # Check names as well as IDs so a later game cannot hide a repurposed ID.
    names = {s['id']: s.get('name') for s in catalog.get('skills', [])}
    hidden = [s['id'] for s in review['skills'] if names.get(s['id']) == s['name']]
    return {'abilityModes': settings(root), 'reviewedHiddenSkills': hidden}


def prepare_barrage_trial(units, root, rows):
    import _ffr_animation_repair as motion
    # Empty owners replace any stale trial left by an earlier enhanced build.
    return motion.prepare_barrage_trial(units if enabled(root) else [], root, rows)


def prepare_sequences(tables, clones, jobs, units, root, rows, extract, native_support=None):
    import _ffr_animation_repair as motion
    if enabled(root):
        return motion.prepare_sequences(tables, clones, jobs, units, root, rows, extract, native_support)
    # Keep explicit custom/LB jobs and all native bindings. Clear the prior
    # coverage report so verification cannot accept stale donor-row changes.
    report = Path(root) / 'build/animation-repair-report.json'
    report.parent.mkdir(parents=True, exist_ok=True)
    selected, preserved = motion.repair_selection(units)
    report.write_text(json.dumps({'schema': 1, 'mode': 'original_game', 'inGameValidated': False,
        'skills': [{'id': sid, 'status': 'original_game_bindings'} for sid in sorted(selected)],
        'preservedNative': preserved}, indent=2) + '\n', encoding='utf-8')
    return []


def register(app, env):
    from fastapi import HTTPException

    @app.get('/api/abilities/settings')
    def get_settings():
        try: return settings(env['ROOT'])
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e

    @app.put('/api/abilities/settings')
    def put_settings(value: dict):
        try:
            value = validate(value)
            if env.get('state', {}).get('running'):
                raise ValueError('Wait for the current build to finish.')
            path = Path(env['ROOT']) / CONFIG
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix='ability-modes-', dir=path.parent)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(value, f); f.flush(); os.fsync(f.fileno())
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
            return value
        except (OSError, ValueError) as e: raise HTTPException(422, str(e)) from e
