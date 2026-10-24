"""Reuse verified generated assets while assembling a clean output every build."""
import functools
import hashlib
import json
import inspect
import sys
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

REVISION = 1
SIDECARS = ('.uasset', '.uexp', '.ubulk', '.uptnl')
PACKAGES = ('.uasset', '.umap')

def sidecars(path):
    return (Path(path).suffix, '.uexp', '.ubulk', '.uptnl')
_active = None


def canonical(value):
    if isinstance(value, dict): return {str(k): canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [canonical(v) for v in value]
    if isinstance(value, Path): return str(value)
    return value


def digest(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


class Cache:
    def __init__(self, root, context, tool=(), usmap=None):
        self.root = Path(root).resolve()
        self.tool = list(map(str, tool)); self.usmap = usmap
        self.context = digest({'revision':REVISION, 'context':context})
        # Short paths also work in deeply nested portable Windows installs.
        self.directory = self.root / 'build/reuse' / self.context[:16]
        self.memo = {}; self.stats = {}; self.started = time.monotonic()
        self.dependencies = set()

    def file(self, path):
        path = Path(path).resolve(); self.dependencies.add(str(path))
        if not path.is_file(): return [str(path), None]
        st = path.stat(); stamp = (st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        old = self.memo.get(path)
        if old is None or old[0] != stamp: self.memo[path] = (stamp, sha(path))
        return [str(path), self.memo[path][1]]

    def inputs(self, paths):
        result = []
        for p in sorted({str(Path(p).resolve()) for p in paths}):
            path = Path(p)
            if path.suffix.lower() in PACKAGES:
                result.extend(self.file(path.with_suffix(s)) for s in sidecars(path))
            else: result.append(self.file(path))
        return result

    def outputs(self, targets):
        result = []
        for i, target in enumerate(targets):
            p = Path(target).absolute()
            if not p.resolve().is_relative_to(self.root) or p.is_symlink():
                raise ValueError('Generated output escapes the Studio engine.')
            if p.suffix in PACKAGES:
                paths = [(s,p.with_suffix(s)) for s in sidecars(p) if p.with_suffix(s).is_file()]
                if not {p.suffix,'.uexp'} <= {s for s,_ in paths}: return None
            else: paths = [('',p)] if p.is_file() else []
            if not paths: return None
            for suffix, file in paths:
                if file.is_symlink() or file.stat().st_size <= 0: return None
                result.append((i,suffix,file))
        return result

    def restore(self, entry, fingerprint, targets):
        try:
            meta = json.loads((entry/'manifest.json').read_bytes())
            if meta.get('schema') != 1 or meta.get('fingerprint') != fingerprint: return False
            records = meta['files']; seen = set(); groups = {}
            for n,r in enumerate(records):
                i,s = r['index'],r['suffix']
                if type(i) is not int or not 0 <= i < len(targets) or s not in ('',*SIDECARS,'.umap') or (i,s) in seen: return False
                target=Path(targets[i]); expected = sidecars(target) if target.suffix in PACKAGES else ('',)
                destination=target.with_suffix(s) if s else target
                if destination.is_symlink() or not destination.resolve().is_relative_to(self.root): return False
                if s not in expected: return False
                seen.add((i,s)); groups.setdefault(i,set()).add(s)
                file=entry/(str(n)+'.bin')
                if file.is_symlink() or file.stat().st_size!=r['size'] or sha(file)!=r['sha256']: return False
            for i,target in enumerate(targets):
                required={Path(target).suffix,'.uexp'} if Path(target).suffix in PACKAGES else {''}
                if not required<=groups.get(i,set()): return False
                p=Path(target).absolute()
                if p.is_symlink() or not p.resolve().is_relative_to(self.root): return False
            # Verify the entire entry before writing any part of it. Never use
            # hard links: subsequent timeline/material edits must not alter cache.
            for n,r in enumerate(records):
                target=Path(targets[r['index']]); target=target.with_suffix(r['suffix']) if r['suffix'] else target
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(entry/(str(n)+'.bin'),target)
            for i,target in enumerate(targets):
                if Path(target).suffix in PACKAGES:
                    for s in set(sidecars(target))-groups[i]: Path(target).with_suffix(s).unlink(missing_ok=True)
            os.utime(entry,None)
            return True
        except (OSError, ValueError, KeyError, TypeError): return False

    def execute(self, kind, value, inputs, targets, action):
        before=self.inputs(inputs)
        fingerprint=digest({'context':self.context,'kind':kind,'value':value,'inputs':before})
        entry=self.directory/fingerprint[:32]
        stat=self.stats.setdefault(kind,{'reused':0,'built':0,'seconds':0.0})
        start=time.monotonic()
        if self.restore(entry,fingerprint,targets):
            stat['reused']+=1;stat['seconds']+=time.monotonic()-start
            return True
        action()
        stat['built']+=1;stat['seconds']+=time.monotonic()-start
        mutable={str((Path(p).with_suffix(s) if s else Path(p)).resolve())
                 for p in targets for s in (sidecars(p) if Path(p).suffix in PACKAGES else ('',))}
        stable=lambda records:[r for r in records if r[0] not in mutable]
        if stable(self.inputs(inputs))!=stable(before):
            raise ValueError('Build inputs changed during generation. Retry the build.')
        outputs=self.outputs(targets)
        if not outputs: return False
        try:
            self.directory.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='w-',dir=self.directory) as temporary:
                folder=Path(temporary); records=[]
                for n,(i,s,p) in enumerate(outputs):
                    shutil.copyfile(p,folder/(str(n)+'.bin'))
                    records.append({'index':i,'suffix':s,'size':p.stat().st_size,'sha256':sha(p)})
                (folder/'manifest.json').write_text(json.dumps({'schema':1,'fingerprint':fingerprint,'files':records}))
                if entry.exists(): shutil.rmtree(entry)
                os.replace(folder,entry)
        except OSError:
            # The generated files are valid even if the optional cache is full.
            pass
        return False

    def command(self, cmd):
        """Recognize only commands with explicitly known inputs and outputs."""
        args=list(map(str,cmd))
        if not self.tool or args[:len(self.tool)]!=self.tool: return None
        args=args[len(self.tool):]
        if not args: return None
        op=args[0]; inputs=[]; outputs=[]
        if '--usmap' in args: inputs.append(args[args.index('--usmap')+1])
        if op in ('tojson','rows','seqdump') and len(args)>=3:
            inputs.append(args[1]);outputs.append(Path(args[2]))
        elif op in ('fromjson','clone-package') and len(args)>=3:
            inputs.append(args[1]);outputs.append(Path(args[2]))
        elif op=='make-ss6' and len(args)>=4:
            inputs+=args[1:3];outputs.append(Path(args[3]))
        elif op=='make-texture' and len(args)>=6:
            inputs+=args[1:3];outputs.append(Path(args[5]))
        elif op=='patch' and len(args)>=2:
            recipe=json.loads(Path(args[1]).read_text(encoding='utf-8-sig'))
            if set(recipe)-{'legacyRoot','outRoot','tables','objects','clones','frames','retime','bytecode','sequenceData','atomBanks'}: return None
            legacy=Path(recipe['legacyRoot']);out=Path(recipe['outRoot']);inputs.append(args[1])
            for category,items in recipe.items():
                if category in ('legacyRoot','outRoot'): continue
                for item in items:
                    if category in ('clones','atomBanks'):
                        source=item['from'];target=item['to']
                    else: source=target=item['asset']
                    inputs.append(legacy/(source+'.uasset'));outputs.append(out/(target+'.uasset'))
                    if category=='sequenceData': inputs.append(item['json'])
                    if category=='atomBanks': inputs.append(item['acb'])
        else: return None
        # JSON serialization may refer to the native asset for retained data.
        for p in list(inputs):
            if Path(p).suffix=='.json':
                try:
                    doc=json.loads(Path(p).read_text(encoding='utf-8-sig'))
                    def paths(v):
                        if isinstance(v,str) and len(v)<1024 and Path(v).is_absolute() and Path(v).is_file(): inputs.append(v)
                        elif isinstance(v,dict):
                            for x in v.values():paths(x)
                        elif isinstance(v,list):
                            for x in v:paths(x)
                    paths(doc)
                except (OSError, ValueError): return None
        if not outputs: return None
        if any(not p.absolute().resolve().is_relative_to(self.root) for p in outputs): return None
        return op,args,inputs,list(dict.fromkeys(outputs))

    def run(self, cmd, original):
        try: spec=self.command(cmd)
        except (OSError,ValueError,KeyError,TypeError): spec=None
        if spec is None: return original(cmd)
        kind,value,inputs,targets=spec
        result=[]
        hit=self.execute(kind,value,inputs,targets,lambda:result.append(original(cmd)))
        return None if hit else (result[0] if result else None)

    def prune(self, limit=4*1024**3):
        """Bound optional disk use; oldest unreferenced entries go first."""
        entries=[]; total=0
        base=self.root/'build/reuse'
        for folder in base.glob('*/*'):
            try:
                if not folder.is_dir() or folder.is_symlink(): continue
                size=sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
                entries.append((folder.stat().st_mtime,folder,size));total+=size
            except OSError: continue
        for _,folder,size in sorted(entries):
            if total<=limit: break
            try: shutil.rmtree(folder);total-=size
            except OSError: pass

    def finish(self):
        self.prune()
        report={'schema':1,'seconds':round(time.monotonic()-self.started,3),'stages':self.stats}
        path=self.root/'build/reuse-report.json';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2)+'\n')
        print('Build reuse: '+', '.join(f'{s["reused"]} reused / {s["built"]} rebuilt {k}' for k,s in self.stats.items()),flush=True)
        return report


def code_identity(root, tool):
    # Native serialized results depend on the native writer, not on unrelated
    # UI or acquisition changes. Python generators add their own source inputs.
    root=Path(root);paths=[Path(__file__)]
    directory=root/'bin'
    if directory.is_dir():
        paths.extend(p for p in directory.rglob('*') if p.is_file() and p.suffix.lower() in ('.dll','.exe'))
    paths.extend(Path(p) for p in tool if Path(p).is_file())
    return digest([(str(p.relative_to(root)) if p.is_relative_to(root) else str(p),sha(p)) for p in sorted(set(paths))])


def sprite_targets(out, uid):
    out=Path(out)/'FFRS/Content'
    stems=[out/'Chara'/kind/f'summon{uid}'/(f'summon{uid}'+suffix+'.uasset')
           for kind,suffixes in (('summon',('','_tex','_normal','_mreo')),('menu',('','_tex')))
           for suffix in suffixes]
    stems.extend(out/'UI/Textures/Icon'/folder/(prefix+f'_summon{uid}.uasset')
                 for folder,prefix in (('Vision_Face','ICON_UnitFace'),('Unit_Face_Timeline','ICON_UnitFace'),('menu','ICON_Ability')))
    return stems


def install_reader(root, ffrenv):
    global _active
    try:
        import _ffr_deck_sync
        context={'game':_ffr_deck_sync.game_identity(Path(ffrenv.game_root())),
                 'code':code_identity(root,ffrenv.FFRDT)}
    except (AttributeError,OSError,ValueError): return
    _active=Cache(root,context,ffrenv.FFRDT,Path(root)/'extracted/Mappings.usmap')


def install(env):
    global _active
    if env.get('_ffr_reuse_installed'): return
    env['_ffr_reuse_installed']=True
    try:
        import _ffr_deck_sync
        game=_ffr_deck_sync.game_identity(Path(env['ffrenv'].game_root()))
        context={'game':game,'code':code_identity(env['ROOT'],env['FFRDT'])}
    except (AttributeError,OSError,ValueError):
        return  # Minimal fixtures/unsupported engines retain the original path.
    cache=Cache(env['ROOT'],context,env['FFRDT'],env['USMAP']);_active=cache
    original_run=env['run'];env['run']=lambda cmd:cache.run(cmd,original_run)
    original_sprites=env['generate_sprites']
    def sprites(unit):
        root=Path(env['ROOT']);legacy=Path(env['LEGACY']);ff=unit['ffbe'];uid=unit['id'];donor=unit['donor']
        sources=[]
        for rel in (ff['dir'],ff.get('baseDir')):
            if rel:
                folder=root/rel;sources.extend(p for p in folder.rglob('*') if p.is_file())
        sources.extend(root/'tools'/name for name in ('_ffr_build_sprites.py','_ffr_build_icons.py',
            '_ffr_animation_repair.py','_ffr_ability_modes.py','_ffr_sephira.py','_ffr_shrine_challenges.py'))
        sources.extend((root/'tools/ffbe2ss6').glob('*.py'))
        sources.extend((root/'mods/EstherTsukiko/icon_layout.json',root/'mods/EstherTsukiko/ability-modes.json',root/'build/barrage-trial.json',Path(env['USMAP'])))
        sources.extend(p for folder in (legacy/'FFRS/Content/Chara/summon'/f'summon{donor}',legacy/'FFRS/Content/Chara/summon/summon13110',
                        legacy/'FFRS/Content/Chara/menu'/f'summon{donor}',legacy/'FFRS/Content/Chara/menu/summon13110')
                       for p in folder.rglob('*') if p.is_file())
        for folder,prefix in (('Vision_Face','ICON_UnitFace'),('Unit_Face_Timeline','ICON_UnitFace'),('menu','ICON_Ability')):
            sources.append(legacy/'FFRS/Content/UI/Textures/Icon'/folder/(prefix+'_summon13110.uasset'))
        sources.extend(p for p in (root/'build/icons/donors').glob('*') if p.is_file())
        import _ffr_sephira
        projection={k:unit.get(k) for k in ('id','key','donor','ffbe','icon','native','sephiraVision','bundledPreset')}
        try: projection['generator']=inspect.getsource(original_sprites)
        except (OSError,TypeError): projection['generator']=code_identity(root,env['FFRDT'])
        projection['python']=sys.version
        import PIL
        projection['pillow']=PIL.__version__
        projection['nativeCaster']=_ffr_sephira.runtime_membership(unit) is not None
        projection['nativeMotions']=_ffr_sephira.native_motion_names(unit)
        hit=cache.execute('sprites',projection,sources,sprite_targets(env['OUT'],uid),lambda:original_sprites(unit))
        if hit: print('  Reused sprites and icons: '+unit['en'],flush=True)
    env['generate_sprites']=sprites
    import ffbe_resonance,ffbe_audio
    sequence=getattr(ffbe_resonance.build,'_reuse_original',ffbe_resonance.build)
    audio=getattr(ffbe_audio.build,'_reuse_original',ffbe_audio.build)
    def timeline(job,out,work,command,usmap,run):
        path=Path(out)/(job['asset']+'.uasset')
        cache.execute('timelines',job,[path,usmap,Path(env['ROOT'])/'tools/ffbe_resonance.py',Path(env['ROOT'])/'tools/ffbe_lb.py'],[path],lambda:sequence(job,out,work,command,usmap,run))
    def sound(bank,out,work,command,usmap,run,legacy):
        inputs=[bank['path'],usmap,Path(legacy)/(ffbe_audio.SHELL+'.uasset'),
                Path(env['ROOT'])/'tools/ffbe_audio.py',Path(env['ROOT'])/'tools/ffbe_audio_assets.py']
        inputs.extend((Path(env['ROOT'])/'tools/ffbe_effects').glob('*.py'))
        doc=bank.get('audioManifest')
        if doc:
            parent=Path(bank['path']).parent
            if parent.name=='lb':parent=parent.parent
            inputs.extend(parent/'samples'/(r['sha256']+'.hca') for r in doc['waves'].values())
        cache.execute('audio',bank,inputs,[Path(out)/(bank['asset']+'.uasset')],lambda:audio(bank,out,work,command,usmap,run,legacy))
    timeline._reuse_original=sequence; sound._reuse_original=audio
    ffbe_resonance.build=timeline;ffbe_audio.build=sound


def with_runner(runner):
    return functools.partial(subprocess_run, _runner=runner)


def subprocess_run(cmd, _runner=None, **kwargs):
    runner=_runner or subprocess.run
    if _active is None: return runner(cmd,**kwargs)
    result=[]
    def action(args):
        r=runner(args,**kwargs);result.append(r)
        if r.returncode: raise subprocess.CalledProcessError(r.returncode,args,output=r.stdout,stderr=r.stderr)
        return r
    try:
        reused=_active.run(cmd,action)
        return result[0] if result else subprocess.CompletedProcess(cmd,0,
            stdout='Reused unchanged game assets.\n' if kwargs.get('text') or kwargs.get('encoding') else b'',
            stderr='' if kwargs.get('text') or kwargs.get('encoding') else b'')
    except subprocess.CalledProcessError as error:
        if kwargs.get('check'): raise
        return subprocess.CompletedProcess(cmd,error.returncode,stdout=error.stdout,stderr=error.stderr)


def finish():
    if _active is not None:return _active.finish()


def unchanged_files(source, destination, files):
    """Compare actual installed bytes, rather than trusting a prior ledger."""
    result=set()
    for name in files:
        left,right=Path(source)/name,Path(destination)/name
        if (left.is_file() and right.is_file() and not right.is_symlink()
                and left.stat().st_size==right.stat().st_size and sha(left)==sha(right)):
            result.add(name)
    return result
