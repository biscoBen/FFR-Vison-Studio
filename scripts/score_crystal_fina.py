"""Render a light piano opening building into an intense, suspended organ ending.

Developer-only: FluidSynth and a supplied General MIDI SoundFont. No instrument
library or synthesizer is installed with Studio. The existing movie stays 6.4 s.
"""
import argparse
import ctypes as ct
import ctypes.util
import hashlib
import json
from pathlib import Path
import wave

import numpy as np

RATE, SAMPLES = 48000, 307200


def arrangement():
    events = []
    def note(start, channel, pitch, velocity, length):
        events.extend([(round(start*RATE), 'noteon', channel, pitch, velocity),
                       (round((start+length)*RATE), 'noteoff', channel, pitch)])
    # A spacious D-minor/add9 opening, with breathing room instead of a regular
    # upbeat arpeggio. The figure gathers momentum as the camera approaches.
    for start,pitch,velocity in [(0.,62,47),(.06,69,41),(.82,76,45),
            (1.65,77,48),(2.43,81,51),(3.,77,54),(3.45,79,56),
            (3.85,81,58),(4.18,82,61),(4.45,81,64),(4.7,79,67),
            (4.95,76,70),(5.15,73,73)]:
        note(start,0,pitch,velocity,1.15)
    for start,chord,velocity in [(1.5,(50,57),35),(3.2,(38,45,50),45),
                                  (4.2,(34,41,50),50),(5.2,(33,40,55,58,61,64),64)]:
        for i,pitch in enumerate(chord):note(start+i*.018,0,pitch,velocity,.95)
    # The organ grows from a breath into an A7(b9) dominant at the eye opening.
    # Never follow it with the bright tonic resolution used in the first draft.
    for start,chord,length,velocity in [(3.2,(38,45,50,53,57,64),.98,55),
            (4.2,(34,41,46,50,53,57,64),.98,66),
            (5.2,(33,40,45,55,58,61,64,70),1.18,79)]:
        for pitch in chord:note(start,1,pitch,velocity,length)
    for pitch in (69,76):note(5.95,1,pitch,78,.43)
    for sample in range(round(3.2*RATE), round(6.39*RATE), 480):
        t=sample/RATE;level=round(12+109*min(1.,max(0.,(t-3.2)/2.9))**1.4)
        events.append((sample,'cc',1,11,level))
    return sorted(events, key=lambda e:e[0])


def render(soundfont, destination):
    library = ctypes.util.find_library('fluidsynth')
    if not library: raise RuntimeError('Install FluidSynth for developer score rendering.')
    fluid = ct.CDLL(library); ptr=ct.c_void_p
    def bind(name, result, args):
        fn=getattr(fluid,name);fn.restype=result;fn.argtypes=args;return fn
    settings=bind('new_fluid_settings',ptr,[])()
    number=bind('fluid_settings_setnum',ct.c_int,[ptr,ct.c_char_p,ct.c_double])
    integer=bind('fluid_settings_setint',ct.c_int,[ptr,ct.c_char_p,ct.c_int])
    for key,value in [('synth.sample-rate',RATE),('synth.gain',.6),
                       ('synth.reverb.room-size',.65),('synth.reverb.damp',.4),
                       ('synth.reverb.width',.8),('synth.reverb.level',.24)]:
        number(settings,key.encode(),value)
    integer(settings,b'synth.chorus.active',0)
    synth=bind('new_fluid_synth',ptr,[ptr])(settings)
    try:
        if bind('fluid_synth_sfload',ct.c_int,[ptr,ct.c_char_p,ct.c_int])(
                synth,str(soundfont.resolve()).encode(),1)<0:
            raise ValueError('Cannot load supplied SoundFont')
        program=bind('fluid_synth_program_change',ct.c_int,[ptr,ct.c_int,ct.c_int])
        program(synth,0,0);program(synth,1,19)  # Grand piano; church organ.
        funcs={name:bind('fluid_synth_'+name,ct.c_int,[ptr]+[ct.c_int]*n)
               for name,n in [('noteon',3),('noteoff',2),('cc',3)]}
        funcs['cc'](synth,0,7,100);funcs['cc'](synth,1,7,92)
        funcs['cc'](synth,0,10,56);funcs['cc'](synth,1,10,70)
        write=bind('fluid_synth_write_float',ct.c_int,
            [ptr,ct.c_int,ptr,ct.c_int,ct.c_int,ptr,ct.c_int,ct.c_int])
        pcm=np.zeros((SAMPLES,2),dtype=np.float32);position=0
        for sample,kind,*args in [*arrangement(),(SAMPLES,'end')]:
            end=min(sample,SAMPLES)
            if end>position:
                count=end-position;left=(ct.c_float*count)();right=(ct.c_float*count)()
                if write(synth,count,left,0,1,right,0,1)!=0: raise ValueError('Score render failed')
                pcm[position:end,0]=left;pcm[position:end,1]=right;position=end
            if kind!='end' and sample<SAMPLES: funcs[kind](synth,*args)
        # Keep the unresolved final chord strong, with a short click-free fade
        # into the original sprite/heal sounds instead of a gentle cadence.
        t=np.arange(SAMPLES)/RATE
        pcm*=np.minimum(t/.015,1)[:,None]*np.clip((6.4-t)/.09,0,1)[:,None]
        peak=float(np.max(np.abs(pcm)))
        if peak<=0: raise ValueError('Empty score')
        pcm*=.84/peak
        destination.parent.mkdir(parents=True,exist_ok=True)
        with wave.open(str(destination),'wb') as output:
            output.setparams((2,2,RATE,SAMPLES,'NONE','not compressed'))
            output.writeframes(np.rint(pcm*32767).astype('<i2').tobytes())
        spec={'revision':'piano-organ-2','seconds':6.4,'sampleRate':RATE,'samples':SAMPLES,'channels':2,
              'tempo':64,'rubato':True,'pianoProgram':0,'organProgram':19,'organStart':3.2,'climax':5.2,
              'ending':'unresolved A7(b9) organ crescendo; no tonic cadence',
              'soundfont':soundfont.name,'soundfontSha256':hashlib.sha256(soundfont.read_bytes()).hexdigest(),
              'waveSha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
              'peakDbfs':float(20*np.log10(np.max(np.abs(pcm)))),
              'rmsDbfs':float(20*np.log10(np.sqrt(np.mean(pcm**2)))), 'events':arrangement()}
        destination.with_suffix('.json').write_text(json.dumps(spec,indent=2)+'\n')
        return spec
    finally:
        bind('delete_fluid_synth',None,[ptr])(synth)
        bind('delete_fluid_settings',None,[ptr])(settings)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--soundfont',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(render(args.soundfont,args.output),indent=2))
