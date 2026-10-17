"""A supplemental delivery must preserve existing assets and skill identities."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from extend_ffbe_library_movies import extend


def digest(raw):return hashlib.sha256(raw).hexdigest()


class SupplementalMoviesTests(unittest.TestCase):
    def test_new_clips_preserve_existing_bytes_and_reject_unverified_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);output=root/'library';work=root/'work';source=root/'source'
            output.mkdir();(work/'movies').mkdir(parents=True);(source/'memorial-source').mkdir(parents=True)
            skill={'key':'lb:123','id':'123','kind':'lb','name':'Example','movies':['new.usm']}
            summary={'cinematicClips':0,'missingCinematicFiles':['new.usm']}
            documents={'catalog.json':{'skills':[skill],'movies':[]},'movies.json':{},
                       'provenance.json':{'summary':summary,'sources':{}},'raw/keep.bmb':b'preserved original'}
            raw={n:(v if isinstance(v,bytes) else json.dumps(v).encode()) for n,v in documents.items()}
            pack=output/'library-01.zip'
            with zipfile.ZipFile(pack,'w') as z:
                for name,value in raw.items():z.writestr(name,value)
            manifest={'schema':1,'summary':summary,'packs':[{'name':pack.name,'bytes':pack.stat().st_size,'sha256':digest(pack.read_bytes())}],
                      'files':{n:{'pack':pack.name,'bytes':len(v),'sha256':digest(v)} for n,v in raw.items()}}
            original=json.dumps(manifest).encode();(output/'manifest.json').write_bytes(original)
            movie={'file':'new.webm','sourceSha256':digest(b'original USM'),'previewSha256':digest(b'preview WebM')}
            (work/'movies/index.json').write_text(json.dumps({'new.usm':movie}))
            (work/'movies/new.usm').write_bytes(b'original USM');(work/'movies/new.webm').write_bytes(b'preview WebM')
            record=source/'memorial-source/new.usm.source.json';record.write_text(json.dumps({'sha256':'changed'}))
            with self.assertRaisesRegex(ValueError,'delivery source'):extend(output,work,source)
            self.assertEqual((output/'manifest.json').read_bytes(),original)
            record.write_text(json.dumps({'sha256':movie['sourceSha256']}))
            with contextlib.redirect_stdout(io.StringIO()):result=extend(output,work,source)
            with zipfile.ZipFile(output/result['files']['catalog.json']['pack']) as z:
                self.assertEqual(json.loads(z.read('catalog.json'))['skills'],[skill])
                self.assertEqual(z.read('raw/keep.bmb'),raw['raw/keep.bmb'])
            for name,data in (('source-movies/new.usm',b'original USM'),('movies/new.webm',b'preview WebM')):
                with zipfile.ZipFile(output/result['files'][name]['pack']) as z:self.assertEqual(z.read(name),data)
            self.assertEqual(result['summary']['missingCinematicFiles'],[])
            self.assertEqual(result['summary']['cinematicClips'],1)
            before=(output/'manifest.json').read_bytes()
            movie['previewSha256']='changed';(work/'movies/index.json').write_text(json.dumps({'new.usm':movie}))
            with contextlib.redirect_stdout(io.StringIO()):extend(output,work,source)
            self.assertEqual((output/'manifest.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
