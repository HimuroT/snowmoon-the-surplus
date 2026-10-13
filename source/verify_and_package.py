#!/usr/bin/env python3
# Modified 2026-10-13: public source packaging and documentation; image/audio generation unchanged.
"""SPDX-License-Identifier: GPL-3.0-only
Verify encoded film, all caption boundaries and reproducible source;
package corresponding editable materials, without any publication action.
"""
import json, hashlib, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.io import wavfile
from animate_film import frame, cue_at, CUES, FPS, N
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'review/probe.json').read_text())
v=next(s for s in p['streams'] if s['codec_type']=='video');a=next(s for s in p['streams'] if s['codec_type']=='audio')
assert float(p['format']['duration'])==84.0
assert (v['width'],v['height'],v['r_frame_rate'],v['codec_name'],v['pix_fmt'])==(1920,1080,'24/1','h264','yuv420p')
assert (a['codec_name'],a['sample_rate'],a['channels'])==('aac','48000',2)
rows=[l for l in (ROOT/'review/frame_hashes.txt').read_text().splitlines() if l and not l.startswith('#')]
hashes=[r.split(',')[-1].strip() for r in rows];assert len(hashes)==N
adjacent_duplicates=[i for i in range(1,N) if hashes[i]==hashes[i-1]]
# Identical frames are permitted only within the intentional near-black fades.
assert all(i/FPS<.65 or i/FPS>=82.8 for i in adjacent_duplicates),adjacent_duplicates
caption_counts={str(i+1):0 for i in range(len(CUES))}
for i in range(N):
 s=(ROOT/'svg'/f'{i:05}.svg').read_text();assert s==frame(i/FPS),('source mismatch',i)
 root=ET.fromstring(s); texts=[''.join(el.itertext()) for el in root.iter('{http://www.w3.org/2000/svg}text')]
 q=cue_at(i/FPS)
 if q:
  lines=q['subtitle'].split('\n');lines[0]=q['speaker']+': '+lines[0]
  assert all(line in texts for line in lines),('caption missing',i,lines)
  assert sum(tx.startswith(('Bai:','Zei:')) for tx in texts)==1,('caption overlap',i)
  caption_counts[str(CUES.index(q)+1)]+=1
 else: assert not any(tx.startswith(('Bai:','Zei:')) for tx in texts),('unexpected caption',i)
for i,q in enumerate(CUES):assert caption_counts[str(i+1)]==round((q['end']-q['start'])*FPS)
rate,music=wavfile.read(ROOT/'audio/the_surplus_84s_music.wav')
assert rate==48000 and music.shape==(4032000,2) and np.count_nonzero(music[70*rate:int(79.7*rate)])==0
rate,mix=wavfile.read(ROOT/'audio/the_surplus_84s_mix.wav');assert rate==48000 and mix.shape==(4032000,2)
drate,decoded=wavfile.read(ROOT/'review/decoded_mix_for_qa.wav');peak=float(np.max(np.abs(decoded)));assert drate==48000 and peak<1
first=np.array(Image.open(ROOT/'frames/00000.png').convert('RGB'));last=np.array(Image.open(ROOT/'frames/02015.png').convert('RGB'))
assert np.max(first.std(axis=(0,1)))<.001 and np.max(last.std(axis=(0,1)))<.001
assert np.max(abs(first.astype(int)-last.astype(int)))==0
# Representative actual frames at every planned beat and internal reverse cut.
indices=[48,174,282,396,510,642,816,936,1056,1206,1290,1380,1464,1560,1638,1716,1800,1848,1944,2015]
contact=Image.new('RGB',(1440,288*((len(indices)+2)//3)),'#101620');d=ImageDraw.Draw(contact)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for n,i in enumerate(indices):
 im=Image.open(ROOT/'frames'/f'{i:05}.png').convert('RGB');im.thumbnail((480,270));x=(n%3)*480;y=(n//3)*288
 contact.paste(im,(x,y+18));d.text((x+10,y),f'{i/FPS:05.2f}s',fill='#dccab2',font=font)
contact.save(ROOT/'review/all-shots-contact.jpg',quality=94)
qa={'delivery':'84-second public source edition; picture and audio unchanged from reviewed export','objective_checks':{'duration_seconds':84.0,'dimensions':[1920,1080],'fps':'24/1','decoded_video_frames':len(rows),'unique_decoded_frame_hashes':len(set(hashes)),'adjacent_identical_frames_only_in_intentional_fades':adjacent_duplicates,'video_codec':'H.264','pixel_format':'yuv420p','audio_codec':'AAC','audio_sample_rate':48000,'audio_channels':2,'source_audio_frames':4032000,'decoded_audio_peak_dbfs':round(20*np.log10(peak),3),'full_decode_errors':False,'caption_cue_count':len(CUES),'caption_frame_counts':caption_counts,'all_2016_svg_caption_boundaries_checked':True,'source_reproduces_all_2016_svg_frames':True,'first_and_last_frames_same_uniform_dark':True,'music_exact_silence_seconds':[70.0,79.7],'representative_still_seconds':71.5,'representative_still_dimensions':list(Image.open(ROOT/'The_Surplus_84s_still.png').size)},'visual_review':{'planned_story_beats':11,'contact_sheet_frame_numbers':indices,'reviewed_before_full_export':True,'approved_excerpt_preserved':'66–78s poses/staging, with proof label removed','adjustments':['Wider walking-shot spacing keeps shoes clear of captions','Static background/reflection framing aligned across 65–66s continuation','Credits include modification date, source author, GPLv3 and corresponding-source notice'],'limitations':['Stylized limited-animation 2.5D rigs','Graphic reflections and lighting','Subtitle phrase timing rather than voiced lip sync','Realtime synchronized playback and perceptual audio listening not interactively auditioned','No assessment of competition eligibility or release readiness']},'sources':['https://vitalik.eth.limo/snowmoon/html/chapter-5.html','https://vitalik.eth.limo/snowmoon/'],'license':'GPL-3.0-only; full license bundled in source/COPYING'}
for name in ['The_Surplus_84s.mp4','The_Surplus_84s_still.png']:
 qa.setdefault('deliverable_sha256',{})[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
(ROOT/'review/qa_report.json').write_text(json.dumps(qa,indent=2)+'\n')
# No intermediate PNGs, platform-delivery helpers, credentials or earlier proof
# are needed. Full editable SVG output plus both generators are included.
archive=ROOT/'The_Surplus_84s_source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for rel in ['README.txt','CREDITS.txt','DELIVERY_README.txt','The_Surplus_84s_still.png','review/qa_report.json','review/all-shots-contact.jpg']:
  z.write(ROOT/rel,'The_Surplus_84s/'+rel)
 for folder in ['source','svg','audio']:
  for f in sorted((ROOT/folder).iterdir()):
   if f.is_file() and f.suffix!='.log':z.write(f,'The_Surplus_84s/'+str(f.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(qa['objective_checks'],indent=2));print('Source ZIP bytes',archive.stat().st_size)
