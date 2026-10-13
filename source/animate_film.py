#!/usr/bin/env python3
# Modified 2026-10-13: public source packaging and documentation; image/audio generation unchanged.
"""SPDX-License-Identifier: GPL-3.0-only
The Surplus: original 84-second unofficial Snowmoon Chapter 5 adaptation.
Complete self-authored vector staging, reuse of the approved character rig,
caption placement and deterministic rendering. No remote assets/services.
"""
import math, json, os, subprocess, argparse, html
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import character_rig as r
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS,N=1920,1080,24,2016
DATA=json.loads((ROOT/'source/shotlist.json').read_text()); CUES=DATA['cues']
e,sm,bell,path,rect,ell=r.e,r.sm,r.bell,r.path,r.rect,r.ell

def cue_at(t):
 return next((q for q in CUES if q['start']<=t<q['end']),None)

def performance(name,t):
 bai=name=='Bai'; q=cue_at(t)
 walk=(1-sm(32.1,33,t)) if t<33 else 0
 first=.2+(0 if bai else .14*(1-sm(23,28,t)))
 # Mouth phrases are only visual timing. No voice performance is claimed.
 speaking=False
 if q and q['speaker']==name:
  u=(t-q['start'])/(q['end']-q['start'])
  speaking=(.09<u<.28 or .37<u<.58 or .66<u<.81)
 blink=max([bell(t,c,.10) for c in ([2.7,8.55,13.1,21.1,26.8,31.8,35.4,40.6,46.4,51.0,57.9,62.1,65.2] if bai else [4.0,10.1,17.8,22.8,28.0,32.5,38.8,44.4,48.4,53.5,59.7,64.3])])
 a={'walk':walk,'first_contact':first,'speaking':speaking,'blink':blink,'tilt':.4*math.sin(t*.7),'torso':0,'gaze':1.6,'openness':.96,'brow':0,'smile':.8,'point':0,'breath':0,'eye_y':0}
 if bai:
  if 6<=t<10.5:
   a.update(torso=2.2*sm(6,7,t)*(1-sm(9.2,10.5,t)),tilt=-2.3,brow=-1.6,smile=1.4)
  if 15<=t<23:
   a.update(brow=-3.8*sm(18.9,20.6,t),smile=1.8,tilt=-1.8)
  if 33<=t<38:
   a.update(smile=2.0,brow=-2.0,tilt=-2.4*sm(33,34.2,t)+1.2*sm(36.7,38,t))
  if 49<=t<59:
   a.update(openness=.84,smile=.6,gaze=2.6,tilt=-1.4,brow=-.8)
  if 59<=t<66:
   a.update(openness=.90,smile=.5,tilt=1.2*sm(62.3,63.2,t)-1.6*sm(63.7,65.3,t),breath=sm(62.4,63,t)*(1-sm(63.3,64,t)))
 else:
  if 10.5<=t<20.5:
   a.update(brow=-.8,point=sm(15.2,16,t)*(1-sm(19.0,20.4,t)),tilt=-1.2)
  if 23<=t<33: a.update(brow=-.5,tilt=1.0,point=.2*sm(24,25,t)*(1-sm(28,29,t)))
  if 38<=t<41:
   nod=sm(38.35,38.75,t)*(1-sm(39.10,39.6,t));a.update(tilt=4.8*nod,by=2*nod,brow=-.4)
  if 41<=t<49: a.update(tilt=-8,gaze=.3,eye_y=-1.3)
  if 53<=t<55:
   surprise=sm(53,53.2,t)*(1-sm(54,54.6,t));a.update(brow=-3*surprise,openness=1+.2*surprise,tilt=-5*sm(54,54.8,t),eye_y=-1.1*sm(54,54.8,t))
  if 59<=t<66:
   a.update(tilt=-1.4,gaze=-1+2.9*sm(59,60,t),brow=-2*sm(59,59.7,t)*(1-sm(62,62.8,t)))
 return a

def char(name,t,x,y,scale=1,mirror=False,opacity=1):
 return r.character(name,t,x,y,scale,mirror,opacity=opacity,acting=performance(name,t))

def background(t):
 if 59<=t<78:return r.street(0)
 # Slight camera movement while walking; stop before uninterrupted eye contact.
 travel=min(t,33)*1.0
 if t>=59: travel=31
 pan=-18+10*math.sin(travel*.16)
 return f'<g transform="translate({e(-48+pan)},-20) scale(1.05)">'+r.street(0)+'</g>'

def reflection(t,large_bai=False):
 if 59<=t<66:
  out='<defs><clipPath id="filmReflection"><rect x="41" y="229" width="1178" height="592"/></clipPath></defs><g clip-path="url(#filmReflection)" opacity=".14">'
  out+=char('Bai',t,378,516,1.13)+char('Zei',t,890,504,1.16,True)
  return out+'</g>'+rect(390,211,14,630,'#343c46')+rect(808,211,14,630,'#343c46')+path('M42 784 L1218 711','none','#d7c3aa',2,'opacity=".28"')
 # This clip follows the scaled street pane, and keeps reflected shoes off ground.
 out='<defs><clipPath id="filmReflection"><rect x="0" y="221" width="1220" height="621"/></clipPath></defs><g clip-path="url(#filmReflection)" opacity=".125">'
 if large_bai: out+=char('Bai',t,458,603,1.59)
 else:
  out+=char('Bai',t,330,506,1.12)
  out+=char('Zei',t,885,497,1.15,True)
 out+='</g>'
 out+=rect(342,202,15,665,'#343c46')+rect(781,202,15,665,'#343c46')
 return out

def skyline(t):
 u=t-41; out=rect(0,0,W,H,'url(#sky)')
 out+=f'<g transform="translate(0,{e(20*sm(41,49,t))})">'
 # Distinct stone, glass and concrete districts, all original vector geometry.
 buildings=[(-40,410,230,500,'#a29391'),(205,308,155,620,'#6f7884'),(370,464,236,450,'#baab96'),(627,358,132,560,'#899399'),(772,259,235,680,'#778993'),(1031,435,224,490,'#b5a294'),(1280,335,172,615,'#8c8287'),(1479,224,152,720,'#637a8b'),(1650,401,300,570,'#b5a695')]
 for i,(x,y,w,h,c) in enumerate(buildings):
  out+=path(f'M{x} {y} L{x+w*.85} {y-10-i%3*10} L{x+w} {y+20} V{y+h} H{x} Z',c,'#686a75',2)
  out+=path(f'M{x+w*.85} {y-10-i%3*10} L{x+w} {y+20} V{y+h} L{x+w*.85} {y+h} Z','#555f6e','none',0,'opacity=".28"')
  for wy in range(y+45,min(y+h-20,810),53):
   for wx in range(x+22,x+w-30,42): out+=rect(wx,wy,18,27,'#526574','opacity=".65"')
  out+=path(f'M{x} {y+22} L{x+w*.85} {y+8}','none','#ded0b6',3,'opacity=".72"')
 # The canonical distant gray-and-purple wall remains modest background geography.
 out+=path('M0 745 Q650 685 1230 700 L1920 727 V922 H0 Z','#796b84','none')
 out+=path('M0 747 Q650 687 1230 702 L1920 729','none','#b8a9ae',7)
 for x in range(0,1921,88):out+=path(f'M{x} {730+int(15*math.cos(x/250))} V850','none','#675f75',3)
 out+=rect(0,850,W,230,'#a58d7c')
 out+='</g>'
 # One tiny copter crosses with a restrained visual rotor blur.
 cx=425+u*114; cy=218-10*math.sin(u*.4)
 out+=f'<g transform="translate({e(cx)},{e(cy)})" opacity=".68">'
 out+=path('M-24 4 Q-7 -12 24 -4 L32 4 L20 15 H-20 Z','#455366','#344152',2)
 out+=path('M-41 -8 H44 M-3 -15 V-3 M-27 12 L-35 21 M20 14 L29 21','none','#3d4b60',3)
 out+=ell(0,-8,54,3,'#576377','opacity=".18"')+'</g>'
 # Over-shoulder silhouette, original back-view of Zei rather than a front pose.
 out+='<g transform="translate(-45,12)">'
 out+=path('M0 1080 L26 817 Q99 695 297 703 Q444 724 575 919 L641 1080 Z','#263540','#172733',4)
 out+=path('M122 702 L159 661 L272 650 L336 731 L270 781 L193 733 Z','#52616a','#1f2d39',4)
 out+=path('M151 555 Q118 493 145 427 Q188 359 270 371 Q349 379 363 452 L346 568 L308 651 L202 670 L169 625 Z','#2c3540','#182633',4)
 out+=path('M141 457 L122 414 L162 414 L147 375 L205 391 L254 343 L262 377 L318 365 L365 406 L364 462 L329 439 L294 466 L257 432 L222 462 L187 448 L175 505 Z','#25313c','#182633',4)
 out+=path('M162 414 Q209 377 265 386','none','#a68e77',3,'opacity=".55"')
 out+=path('M346 489 Q372 477 371 503 L351 534 Z','#bf8c72','#182633',3)
 out+=path('M176 625 Q231 658 308 621 L308 655 L201 679 Z','#bc866c','#27303a',2)
 out+='</g>'
 return out

def subtitle(t):
 q=cue_at(t)
 if not q:return ''
 lines=q['subtitle'].split('\n'); lines[0]=q['speaker']+': '+lines[0]
 widths=[len(v)*18 for v in lines];bw=min(1470,max(540,max(widths)+80))
 top=873 if len(lines)==2 else 909
 out=rect((W-bw)/2,top,bw,100 if len(lines)==2 else 64,'#111b29','rx="10" opacity=".88"')
 for i,line in enumerate(lines):
  out+=f'<text x="960" y="{top+43+i*43}" text-anchor="middle" fill="#f4ecdf" font-family="DejaVu Sans" font-size="35" font-weight="500">{html.escape(line)}</text>'
 return out

def finish(out,t):
 out+=path('M0 80 L480 80 L1450 1000 L1260 1000 Z','#e8b778','none',0,'opacity=".035"')
 out+=rect(0,80,W,920,'url(#vignette)')
 for i in range(11):
  xx=(i*173+math.sin(i*5)*50+t*(3+i%4))%1920; yy=170+(i*119)%650+math.sin(t*.8+i)*7
  out+=ell(e(xx),e(yy),1.05,1.05,'#ecd0a3','opacity=".18"')
 out+='</g>'+rect(0,0,W,80,'#101620')+rect(0,1000,W,80,'#101620')
 out+='<text x="76" y="47" fill="#d4c4b3" font-family="DejaVu Sans" font-size="21" letter-spacing="4">THE SURPLUS</text>'
 out+='<text x="960" y="1047" text-anchor="middle" fill="#939299" font-family="DejaVu Sans" font-size="17" letter-spacing="1.4">UNOFFICIAL SNOWMOON ADAPTATION · CHAPTER 5 · VITALIK BUTERIN · GPLv3</text>'
 out+=subtitle(t)
 if t<.65:out+=rect(0,0,W,H,'#101620',f'opacity="{1-sm(0,.65,t)}"')
 return out+'</svg>'

def frame(t):
 # Preserve the approved late-scene poses and staging, with only proof slates removed.
 if 66<=t<78:
  return r.frame(t-66).replace('REFINED ANIMATION PROOF · 66–78s','')
 out=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+r.defs()+rect(0,0,W,H,'#0e1520')+'<g clip-path="url(#frame)">'
 if t>=78:
  out+=background(t)+rect(0,80,W,920,'#121c2a','opacity=".67"')
  alpha=sm(78.0,78.75,t)*(1-sm(82.8,83.958333,t))
  out+=f'<g opacity="{alpha}">'
  out+='<text x="960" y="385" text-anchor="middle" fill="#ead8bd" font-family="DejaVu Sans" font-size="78" letter-spacing="6">THE SURPLUS</text>'
  out+='<text x="960" y="455" text-anchor="middle" fill="#d6c8b9" font-family="DejaVu Sans" font-size="30" letter-spacing="2">An unofficial Snowmoon adaptation</text>'
  out+='<text x="960" y="564" text-anchor="middle" fill="#b9b2b2" font-family="DejaVu Sans" font-size="27">Adapted from Chapter 5 by Vitalik Buterin</text>'
  out+='<text x="960" y="613" text-anchor="middle" fill="#b9b2b2" font-family="DejaVu Sans" font-size="23">Original adaptation visuals, staging and synthesized sound</text>'
  out+='<text x="960" y="654" text-anchor="middle" fill="#b9b2b2" font-family="DejaVu Sans" font-size="23">Created with OpenAI assistance · 13 October 2026</text>'
  out+='<text x="960" y="730" text-anchor="middle" fill="#d5b88f" font-family="DejaVu Sans" font-size="24">GNU GPL version 3 · Corresponding source supplied</text></g></g>'
  out+=rect(0,0,W,80,'#101620')+rect(0,1000,W,80,'#101620')
  out+=rect(0,0,W,H,'#101620',f'opacity="{sm(82.8,83.958333,t)}"')
  return out+'</svg>'
 if 41<=t<49: out+=skyline(t)
 else:
  out+=background(t)
  if t<33 or 59<=t<66:out+=reflection(t,15<=t<23)
  if t<6:
   # Low tracking: faces stay above the frame, establishing shoes and jointed gait.
   out+=char('Bai',t,579,-270,2.65)
   out+=char('Zei',t,1270,-279,2.70,True)
   a=sm(.7,1.4,t)*(1-sm(4.8,5.7,t))
   out+=f'<g opacity="{a}"><text x="110" y="200" fill="#e6d4bb" font-family="DejaVu Sans" font-size="25" letter-spacing="5">FREETOWN</text><text x="112" y="244" fill="#c1b3a7" font-family="DejaVu Sans" font-size="20" letter-spacing="2">UNITED CITIES</text></g>'
  elif t<15:
   out+=char('Bai',t,629,542,1.55)
   out+=char('Zei',t,1276,527,1.59,True)
  elif t<23:
   out+=char('Zei',t,1044,661,2.56+.025*sm(15,23,t),True)
  elif t<33:
   zoom=1.15+.055*sm(23,33,t)
   out+=char('Bai',t,575,957-440*zoom,zoom)
   out+=char('Zei',t,1340,957-440*(zoom+.03),zoom+.03,True)
  elif t<38:
   out+=char('Bai',t,839,664,2.57)
   out+=path('M1680 999 Q1690 747 1843 650 Q1960 644 2000 782 V999 Z','#222f3a','none')
  elif t<41:
   out+=char('Zei',t,1044,661,2.59,True)
   out+=path('M-100 999 V728 Q20 606 153 618 Q234 644 273 999 Z','#463b4e','none')
  elif t<59:
   if 53<=t<55:
    out+=char('Zei',t,1044,661,2.59,True)
    out+=path('M-100 999 V728 Q20 606 153 618 Q234 644 273 999 Z','#463b4e','none')
   else:
    out+=char('Bai',t,839,664,2.58+.035*sm(49,59,t))
    out+=path('M1680 999 Q1690 747 1843 650 Q1960 644 2000 782 V999 Z','#222f3a','none')
  else:
   out+=char('Bai',t,629,542,1.55)
   out+=char('Zei',t,1276,527,1.59,True)
 return finish(out,t)

def export(i):
 svg=ROOT/'svg'/f'{i:05}.svg';png=ROOT/'frames'/f'{i:05}.png'
 svg.write_text(frame(i/FPS))
 p=subprocess.run(['inkscape',str(svg),'--export-type=png',f'--export-filename={png}','--export-width=1920','--export-height=1080'],env={**os.environ,'HOME':str(ROOT/'inkscape-home'),'XDG_CACHE_HOME':str(ROOT/'inkscape-home/.cache')},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 if p.returncode:raise RuntimeError(p.stderr.decode())
 return i
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--preview',action='store_true');ap.add_argument('--workers',type=int,default=6);a=ap.parse_args()
 for d in ['svg','frames','inkscape-home/.cache']:(ROOT/d).mkdir(parents=True,exist_ok=True)
 indices=[48,174,282,396,510,642,816,936,1056,1206,1290,1380,1464,1560,1638,1716,1800,1848,1944,2015] if a.preview else range(N)
 with ThreadPoolExecutor(max_workers=a.workers) as ex:
  for n,i in enumerate(ex.map(export,indices)):
   if a.preview or n%96==0:print(f'Rendered {i+1}/{N}',flush=True)
