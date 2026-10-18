"""Explicit, resumable installation of the independent public FFBE source library."""
import hashlib
import json
from pathlib import Path
import re
import threading
import urllib.error
import urllib.request

REVISION='memorial-en-v208-1'
RELEASE_TAG='ffbe-library-memorial-en-v208-1'
BASE_URL='https://github.com/biscoBen/FFR-Vison-Studio/releases/download/'+RELEASE_TAG+'/'
MANIFEST='ffbe_library_manifest.json'


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


class DownloadCancelled(Exception):pass


class Installation:
    def __init__(self,root,manifest=None,opener=None,on_ready=None):
        self.root=Path(root)/'library/ffbe'
        self.manifest=manifest if manifest is not None else json.loads(Path(__file__).with_name(MANIFEST).read_bytes())
        if self.manifest.get('schema')!=1 or self.manifest.get('revision')!=REVISION:raise ValueError('Unsupported animation library manifest.')
        self.packs=self.manifest['packs']
        names=set()
        for pack in self.packs:
            if (not re.fullmatch(r'library-\d{2}\.zip',pack['name']) or pack['name'] in names
                    or type(pack['bytes']) is not int or not 0<pack['bytes']<=128*1024*1024
                    or not re.fullmatch(r'[a-f0-9]{64}',pack['sha256'])):raise ValueError('Invalid library pack metadata.')
            names.add(pack['name'])
        self.opener=opener or urllib.request.urlopen;self.on_ready=on_ready
        self.lock=threading.RLock();self.cancel_event=threading.Event();self.thread=None;self.verified={}
        self.progress={'state':'idle','error':'','bytesDone':0,'filesDone':0}
        self.total=sum(p['bytes'] for p in self.packs)

    def path(self,relative):
        path=self.root/relative
        for node in (path,*path.parents):
            if node.is_symlink():raise ValueError('The animation library path is a symbolic link.')
            if node==self.root.parent.parent:break
        return path

    def valid(self,pack):
        path=self.path(REVISION+'/'+pack['name'])
        if not path.is_file():return False
        stat=path.stat();fingerprint=(stat.st_size,stat.st_mtime_ns)
        if stat.st_size!=pack['bytes']:return False
        if self.verified.get(pack['name'])==fingerprint:return True
        if digest(path)!=pack['sha256']:return False
        self.verified[pack['name']]=fingerprint;return True

    def status(self):
        with self.lock:
            running=self.thread is not None and self.thread.is_alive()
            if running:
                return {**self.progress,'ready':False,'running':True,'totalBytes':self.total,'totalFiles':len(self.packs),'revision':REVISION}
            valid=[p for p in self.packs if self.valid(p)]
            installed=False;path=self.path('manifest.json')
            if path.is_file():
                try:installed=json.loads(path.read_bytes())==self.manifest
                except (ValueError,OSError):pass
            ready=len(valid)==len(self.packs) and installed
            return {**self.progress,'state':'ready' if ready else self.progress['state'],
                    'ready':ready,'running':False,'totalBytes':self.total,'totalFiles':len(self.packs),
                    'bytesDone':sum(p['bytes'] for p in valid),'filesDone':len(valid),
                    'neededBytes':sum(p['bytes'] for p in self.packs if p not in valid),'revision':REVISION}

    def start(self):
        with self.lock:
            if self.thread is not None and self.thread.is_alive():return self.status()
            if self.status()['ready']:return self.status()
            self.cancel_event.clear();self.progress={'state':'downloading','error':'','bytesDone':0,'filesDone':0}
            self.thread=threading.Thread(target=self.run,daemon=True,name='FFBE-library-download');self.thread.start()
            return self.status()

    def cancel(self):
        self.cancel_event.set()
        with self.lock:
            if self.thread and self.thread.is_alive():self.progress['state']='cancelling'
        return self.status()

    def fetch(self,pack):
        target=self.path(REVISION+'/'+pack['name']);target.parent.mkdir(parents=True,exist_ok=True)
        partial=self.path(REVISION+'/'+pack['name']+'.part')
        for attempt in range(3):
            if self.cancel_event.is_set():raise DownloadCancelled()
            have=partial.stat().st_size if partial.exists() else 0
            if have>pack['bytes']:partial.unlink();have=0
            if have==pack['bytes']:
                if digest(partial)==pack['sha256']:partial.replace(target);return
                partial.unlink();have=0
            headers={'Accept-Encoding':'identity','User-Agent':'Sephira-Studio-Animation-Library'}
            if have:headers['Range']=f'bytes={have}-'
            request=urllib.request.Request(BASE_URL+pack['name'],headers=headers)
            try:
                with self.opener(request,timeout=20) as response:
                    if response.status==206:
                        expected=f'bytes {have}-{pack["bytes"]-1}/{pack["bytes"]}'
                        if response.headers.get('Content-Range')!=expected:raise ValueError('The library server returned an invalid download range.')
                    elif response.status==200:have=0
                    else:raise ValueError('The library server returned HTTP '+str(response.status)+'.')
                    with partial.open('ab' if have else 'wb') as stream:
                        while True:
                            if self.cancel_event.is_set():raise DownloadCancelled()
                            block=response.read(256*1024)
                            if not block:break
                            have+=len(block)
                            if have>pack['bytes']:raise ValueError('A library file exceeds its expected size.')
                            stream.write(block)
                            with self.lock:self.progress['bytesDone']=self.completed_bytes+have
                if have!=pack['bytes']:raise OSError('The library download was interrupted.')
                if digest(partial)!=pack['sha256']:
                    partial.unlink();raise ValueError('A downloaded library file failed its checksum. Retry the download.')
                partial.replace(target);self.verified.pop(pack['name'],None);return
            except (OSError,urllib.error.URLError) as e:
                if attempt==2:raise OSError('The library download could not finish. Retry to resume verified files.') from e
                if self.cancel_event.wait(1+attempt):raise DownloadCancelled()
        raise OSError('The library download did not finish.')

    def run(self):
        try:
            self.completed_bytes=0;completed=0
            for pack in self.packs:
                if self.cancel_event.is_set():raise DownloadCancelled()
                if not self.valid(pack):self.fetch(pack)
                self.completed_bytes+=pack['bytes'];completed+=1
                with self.lock:self.progress.update(bytesDone=self.completed_bytes,filesDone=completed)
            if self.cancel_event.is_set():raise DownloadCancelled()
            path=self.path('manifest.json');path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path('manifest.json.part');temporary.write_text(json.dumps(self.manifest,ensure_ascii=False,indent=1)+'\n',encoding='utf-8');temporary.replace(path)
            if self.on_ready:self.on_ready()
            with self.lock:self.progress.update(state='ready',error='')
        except DownloadCancelled:
            with self.lock:self.progress.update(state='cancelled',error='Download paused. You can resume it here.')
        except Exception as e:
            with self.lock:self.progress.update(state='error',error=str(e))
