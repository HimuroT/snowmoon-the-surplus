#!/usr/bin/env python3
# Modified 2026-10-13: public source packaging and documentation; image/audio generation unchanged.
"""SPDX-License-Identifier: GPL-3.0-only
2026-10-13: package complete source and full-length audio into independent
small ZIPs. Float32 masters remain unchanged; delivery audio is PCM24 FLAC.
"""
from pathlib import Path
import json, subprocess, hashlib, zipfile
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'delivery-small'; AUDIO=OUT/'audio_delivery'
AUDIO.mkdir(parents=True,exist_ok=True)
report={}
for stem in ['mix','ambience','effects','music']:
 source=ROOT/'audio'/f'the_surplus_84s_{stem}.wav'
 flac=AUDIO/f'the_surplus_84s_{stem}_24bit.flac'
 subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(source),'-c:a','flac','-sample_fmt','s32','-bits_per_raw_sample','24','-compression_level','12',str(flac)],check=True)
 decoded=AUDIO/f'{stem}_decoded_for_qa.wav'
 subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(flac),'-c:a','pcm_f32le',str(decoded)],check=True)
 a,x=wavfile.read(source);b,y=wavfile.read(decoded)
 assert a==b==48000 and x.shape==y.shape==(4032000,2)
 err=float(np.max(np.abs(x.astype(float)-y.astype(float))))
 assert err<=2**-23
 report[stem]={'duration_seconds':84.0,'sample_rate':a,'channels':2,'bits_per_sample':24,'max_absolute_error_vs_float32_source':err,'max_error_dbfs':float(20*np.log10(max(err,1e-20))),'size_bytes':flac.stat().st_size,'sha256':hashlib.sha256(flac.read_bytes()).hexdigest()}
(AUDIO/'format_and_qa.json').write_text(json.dumps(report,indent=2)+'\n')
archives={}
def write_zip(name,files):
 p=OUT/name
 with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  z.write(ROOT/'DELIVERY_README.txt','The_Surplus_84s/DELIVERY_README.txt')
  if not any(rel=='CREDITS.txt' for _,rel in files):z.write(ROOT/'CREDITS.txt','The_Surplus_84s/CREDITS.txt')
  if not any(rel=='source/COPYING' for _,rel in files):z.write(ROOT/'source/COPYING','The_Surplus_84s/source/COPYING')
  for actual,rel in files:z.write(actual,'The_Surplus_84s/'+rel)
 with zipfile.ZipFile(p) as z: assert z.testzip() is None
 assert p.stat().st_size<20_000_000,(p.name,p.stat().st_size)
 archives[name]={'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'entries':[rel for _,rel in files]}
core=[]
for name in ['README.txt','CREDITS.txt','The_Surplus_84s_still.png','review/qa_report.json','review/all-shots-contact.jpg']:
 core.append((ROOT/name,name))
for folder in ['source','svg']:
 for f in sorted((ROOT/folder).iterdir()):
  if f.is_file():core.append((f,str(f.relative_to(ROOT))))
for f in sorted((ROOT/'audio').iterdir()):
 if f.is_file() and f.suffix in ['.json','.txt']:core.append((f,str(f.relative_to(ROOT))))
write_zip('The_Surplus_84s_source_core.zip',core)
for name,stems in [('The_Surplus_84s_audio_mix.zip',['mix']),('The_Surplus_84s_audio_ambience.zip',['ambience']),('The_Surplus_84s_audio_effects_music.zip',['effects','music'])]:
 files=[(AUDIO/f'the_surplus_84s_{s}_24bit.flac',f'audio_delivery/the_surplus_84s_{s}_24bit.flac') for s in stems]
 files.append((AUDIO/'format_and_qa.json','audio_delivery/format_and_qa.json'))
 write_zip(name,files)
(OUT/'delivery_manifest.json').write_text(json.dumps(archives,indent=2)+'\n')
print(json.dumps({n:{k:v for k,v in d.items() if k!='entries'} for n,d in archives.items()},indent=2))
