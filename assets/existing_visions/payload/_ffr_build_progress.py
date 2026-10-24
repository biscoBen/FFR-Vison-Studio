"""Low-overhead build timings; native commands retain their original behavior."""
import atexit
from datetime import datetime
import functools
import json
import os
from pathlib import Path
import time
import subprocess

_current=None


def stamp(line, started, now=None):
    now=time.time() if now is None else now
    elapsed=max(0,now-started)
    wall=datetime.fromtimestamp(now).astimezone().isoformat(timespec='milliseconds')
    return f'[{wall} +{int(elapsed//60):02d}:{elapsed%60:04.1f}] {line}'


class Profile:
    def __init__(self,root,stage,clock=time.perf_counter):
        self.root=Path(root);self.original_stage=stage;self.clock=clock
        self.started=clock();self.stage_started=self.started;self.label=None
        self.stages=[];self.operations=[];self.depth=0;self.failed=False;self.closed=False
        self.folder=Path(os.environ.get('FFR_LOG_DIR') or self.root/'logs');self.folder.mkdir(parents=True,exist_ok=True)
        self.run_id=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.events=(self.folder/('build-events-'+self.run_id+'.jsonl')).open('w',encoding='utf-8',buffering=1)

    def event(self,**fields):
        item={'at':datetime.now().astimezone().isoformat(timespec='milliseconds'),
              'elapsed':round(self.clock()-self.started,4),'stage':self.label,**fields}
        if self.events is not None:
            try:self.events.write(json.dumps(item,ensure_ascii=False)+'\n')
            except OSError:self.events.close();self.events=None

    def stage(self,label):
        now=self.clock()
        if self.label is not None:
            duration=now-self.stage_started;self.stages.append({'name':self.label,'seconds':round(duration,4)})
            print(f'  Stage time: {self.label}: {duration:.2f}s',flush=True)
        self.label=label;self.stage_started=now
        self.event(event='stage-start',name=label)
        self.original_stage(label)

    def operation(self,label,action):
        import _ffr_build_cache
        cache=_ffr_build_cache._active
        counts=lambda: {k:(v['reused'],v['built']) for k,v in cache.stats.items()} if cache else {}
        before=counts();start=self.clock();depth=self.depth;self.depth+=1
        self.event(event='operation-start',name=label,depth=depth)
        print('  Operation start: '+label,flush=True)
        status='ok'
        try:
            result=action()
            if getattr(result,'returncode',0):status='failed';self.failed=True
            return result
        except BaseException:
            status='failed';self.failed=True;raise
        finally:
            self.depth-=1;duration=self.clock()-start;after=counts()
            reused=sum(v[0]-before.get(k,(0,0))[0] for k,v in after.items())
            built=sum(v[1]-before.get(k,(0,0))[1] for k,v in after.items())
            item={'name':label,'seconds':round(duration,4),'status':status,'depth':depth,
                  'cacheReused':reused,'cacheBuilt':built,'stage':self.label}
            self.operations.append(item);self.event(event='operation-end',**item)
            print(f'  Operation {status}: {label}: {duration:.2f}s; cache {reused} reused / {built} built',flush=True)

    def finish(self):
        if self.closed:return
        self.closed=True;now=self.clock()
        if self.label is not None:
            self.stages.append({'name':self.label,'seconds':round(now-self.stage_started,4)})
            print(f'  Stage time: {self.label}: {now-self.stage_started:.2f}s',flush=True)
        import _ffr_build_cache
        cache=_ffr_build_cache._active
        totals={}
        for item in self.stages:
            key=item['name'].split(':',1)[0];totals[key]=totals.get(key,0)+item['seconds']
        print('  Build phase timings:',flush=True)
        for label,seconds in totals.items():print(f'    {label}: {seconds:.2f}s',flush=True)
        print('  Slowest operations (nested work is included in its parent):',flush=True)
        for item in sorted((i for i in self.operations if i['depth']==0),key=lambda i:i['seconds'],reverse=True)[:8]:
            print(f"    {item['seconds']:.2f}s {item['name']} ({item['cacheReused']} reused / {item['cacheBuilt']} built)",flush=True)
        report={'schema':1,'seconds':round(now-self.started,4),'operationFailed':self.failed,
                'cacheContext':cache.context[:16] if cache else None,
                'stages':self.stages,'phaseTotals':totals,'operations':self.operations,'cache':cache.stats if cache else {}}
        try:
            target=self.folder/('build-profile-'+self.run_id+'.json');target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            # Record completed cache work on failed builds too. Do not prune or
            # clear it: retries should reuse the successfully generated assets.
            if cache:
                (self.root/'build').mkdir(parents=True,exist_ok=True)
                (self.root/'build/reuse-report.json').write_text(json.dumps({'schema':1,'seconds':report['seconds'],'stages':cache.stats},indent=2)+'\n',encoding='utf-8')
            self.event(event='profile-end',seconds=report['seconds'],operationFailed=self.failed)
            print('  Detailed build profile: '+str(target),flush=True)
        except OSError as error:
            print('  Build profile could not be saved: '+str(error),flush=True)
        finally:
            if self.events is not None:self.events.close()


def describe(cmd):
    args=list(map(str,cmd))
    for op in ('tojson','fromjson','clone-package','patch','make-ss6','make-texture','rows','seqdump'):
        if op in args:
            index=args.index(op)
            return op+' '+Path(args[index+1]).name if len(args)>index+1 else op
    script=next((Path(arg).name for arg in args if arg.endswith('.py')),None)
    return script or Path(args[0]).name if args else 'process'


def runner(original):
    original=getattr(original,'_profile_original',original)
    @functools.wraps(original)
    def run(cmd,*args,**kwargs):
        if _current is None or _current.closed:return original(cmd,*args,**kwargs)
        return _current.operation(describe(cmd),lambda:original(cmd,*args,**kwargs))
    run._profile_original=original
    return run


def install(env):
    global _current
    if _current and not _current.closed:_current.finish()
    original_stage=getattr(env['stage'],'_profile_original',env['stage'])
    try:profile=Profile(env['ROOT'],original_stage)
    except OSError as error:
        _current=None;print('Build profiling is unavailable: '+str(error),flush=True);return None
    _current=profile
    def stage(label):profile.stage(label)
    stage._profile_original=original_stage;env['stage']=stage
    import _ffr_build_cache
    cache=_ffr_build_cache._active
    if cache is not None:
        restore=getattr(cache.restore,'_profile_original',cache.restore)
        def observed_restore(entry,fingerprint,targets):
            started=profile.clock();exists=entry.is_dir()
            hit=restore(entry,fingerprint,targets)
            profile.event(event='cache-lookup',key=fingerprint[:16],outputs=len(targets),
                          result='hit' if hit else 'miss-invalid' if exists else 'miss-new',
                          seconds=round(profile.clock()-started,4))
            return hit
        observed_restore._profile_original=restore;cache.restore=observed_restore
    env['run']=runner(env['run'])
    sprites=getattr(env['generate_sprites'],'_profile_original',env['generate_sprites'])
    def sprite_set(unit):return profile.operation('Sprite/icon set: '+unit['en'],lambda:sprites(unit))
    sprite_set._profile_original=sprites;env['generate_sprites']=sprite_set
    atexit.register(profile.finish)
    return profile


def capture(cmd, *, log, **kwargs):
    """Stream verification output so timestamps reflect arrival, not a late buffer."""
    kwargs.pop('capture_output',None)
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,**kwargs)
    try:
        for line in process.stdout:log(line.rstrip('\r\n'))
    finally:process.stdout.close()
    process.wait()
    return subprocess.CompletedProcess(cmd,process.returncode,stdout='',stderr='')


def finish():
    if _current is not None:_current.finish()
