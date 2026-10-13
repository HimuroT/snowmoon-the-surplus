#!/usr/bin/env python3
# Modified 2026-10-13: public source packaging and documentation; image/audio generation unchanged.
"""The Surplus • original 12-second animation proof.
SPDX-License-Identifier: GPL-3.0-only
Original adaptation drawings, rig, staging, timing and renderer driver: OpenAI assistant, 2026-10-12.
Adapted from Snowmoon Chapter 5 by Vitalik Buterin.
No remote assets or executables. Requires Python 3 and Inkscape 1.4.
"""
import math, json, os, subprocess, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
W,H,FPS,N=1920,1080,24,288
PAPER='#e7d9c4'; INK='#18212c'; PLUM='#6b536f'; AMBER='#dfa65e'
def e(v): return f'{v:.3f}'
def sm(a,b,x):
 z=max(0,min(1,(x-a)/(b-a))); return z*z*(3-2*z)
def bell(t,c,w): return max(0,1-abs(t-c)/w)
def path(d,fill='none',stroke=INK,sw=3,extra=''):
 return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
def ell(x,y,rx,ry,fill,extra=''):
 return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'
def rect(x,y,w,h,fill,extra=''):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'

def defs():
 return '''<defs>
 <linearGradient id="sky" x2="0.1" y2="1"><stop stop-color="#7d8190"/><stop offset=".58" stop-color="#d7bba0"/><stop offset="1" stop-color="#f0ce9d"/></linearGradient>
 <linearGradient id="wall" x1="0" y1="0" x2="1" y2=".6"><stop stop-color="#b5a091"/><stop offset="1" stop-color="#766b70"/></linearGradient>
 <linearGradient id="glass" x2=".9" y2="1"><stop stop-color="#283847"/><stop offset=".58" stop-color="#54616a"/><stop offset="1" stop-color="#a49183"/></linearGradient>
 <linearGradient id="baiCoat" x2="1" y2=".4"><stop stop-color="#826179"/><stop offset=".7" stop-color="#624b68"/><stop offset="1" stop-color="#473d55"/></linearGradient>
 <linearGradient id="zeiCoat" x2="1" y2=".4"><stop stop-color="#3a4650"/><stop offset=".7" stop-color="#24303c"/><stop offset="1" stop-color="#1a2733"/></linearGradient>
 <linearGradient id="skin" x1="0" y1="0" x2="1" y2=".6"><stop stop-color="#e7b58c"/><stop offset=".63" stop-color="#d79e79"/><stop offset="1" stop-color="#bc8069"/></linearGradient>
 <linearGradient id="skinB" x1="0" y1="0" x2="1" y2=".6"><stop stop-color="#ecc1a0"/><stop offset=".65" stop-color="#dda788"/><stop offset="1" stop-color="#bb826f"/></linearGradient>
 <linearGradient id="rim" x2="1"><stop stop-color="#f1bc76" stop-opacity=".6"/><stop offset="1" stop-color="#f1bc76" stop-opacity="0"/></linearGradient>
 <radialGradient id="vignette"><stop offset=".55" stop-color="#172431" stop-opacity="0"/><stop offset="1" stop-color="#0e192a" stop-opacity=".48"/></radialGradient>
 <clipPath id="frame"><rect x="0" y="80" width="1920" height="920"/></clipPath>
 </defs>'''

# Original flat-painted street geometry. All windows and masonry are authored here.
def street(t,close=False,flip=False):
 drift=0 if t<9.6 else -34*sm(10.15,12,t)
 out=rect(0,0,W,H,'url(#sky)')
 out+='<g opacity=".46">'
 for x,y,w,h in [(20,285,176,470),(180,205,92,530),(275,330,146,360),(443,248,128,465),(575,364,160,350),(770,320,145,460),(960,390,90,290),(1068,268,115,490)]:
  out+=rect(x+drift*.1,y,w,h,'#827e86')+path(f'M{x+12} {y} V{y-14} H{x+w-16} V{y}', 'none','#8e8189',3)
  for wy in range(y+28,y+h-20,44): out+=rect(x+18,wy,w-36,5,'#bcaba2')
 out+='</g>'
 out+=path('M0 680 L1920 630 L1920 890 L0 910 Z','#887484','none')
 out+=path('M0 707 L1920 657','#c1a7ae','#c1a7ae',8)
 # Foreground building and shop window.
 out+=f'<g transform="translate({drift},0)">'
 out+=path('M-80 80 H1380 V881 L-80 973 Z','url(#wall)','none')
 out+=rect(-60,148,1390,40,'#72666a')+rect(-60,185,1390,11,'#d7b697')
 out+=rect(18,209,1222,631,'#383a42')+rect(41,229,1178,592,'url(#glass)')
 # Geometry behind glass, not UI.
 out+=path('M42 235 L1209 235 L42 577 Z','#d9c5ad','none',0,'opacity=".08"')
 out+=path('M531 230 L830 230 L224 820 L50 820 Z','#e7c298','none',0,'opacity=".07"')
 out+=path('M878 230 L1218 230 L552 820 L384 820 Z','#eadbc4','none',0,'opacity=".05"')
 out+=rect(55,674,1144,22,'#818086', 'opacity=".32"')
 for x in [390,808]: out+=rect(x,210,14,631,'#383c45')+rect(x,212,3,627,'#c1a88b','opacity=".6"')
 out+=rect(1256,190,84,700,'#b5a08c')+rect(1270,191,11,698,'#dbc3a3')
 out+=path('M1238 860 L1350 865 L1370 904 L1240 909 Z','#776d6c','none')
 # Masonry joints.
 for y in [315,474,635,790]: out+=path(f'M1263 {y} H1337','none','#8b7e77',2)
 out+=path('M1350 865 L1600 788 L1920 822 L1920 1080 L-30 1080 L-30 946 Z','#927d74','none')
 out+=path('M-30 963 L1355 875 L1612 804','none','#d1b99a',5)
 for i in range(6):
  y=902+i*41; out+=path(f'M-20 {y} L1420 {y-82} L1920 {y-110}','none','#756e6c',2,'opacity=".45"')
 out+=path('M1500 80 H1586 V774 L1490 807 Z','#847675','none')
 out+=path('M1588 149 L1920 112 V700 L1588 775 Z','#a59a8f','none')
 for x in [1640,1744,1845]:
  out+=path(f'M{x} 251 l58 -6 v172 l-58 13 Z','#52616b','none')
  out+=path(f'M{x+4} 255 l48 -5 v10 l-48 6 Z','#d9bd98','none')
 out+=path('M1578 664 L1920 590 L1920 644 L1578 720 Z','#8b7078','none')
 # Small empty shop placard with invented geometric engraving, not text.
 out+=path('M1370 212 L1475 194 V302 L1370 320 Z','#d6b28b','#74656b',3)
 out+=path('M1396 279 L1414 247 L1435 272 L1453 238','#c69a76','#695967',4)
 out+='</g>'
 # small far-off rotor silhouette, essentially still in background
 x=1650+(t*4); out+=f'<g opacity=".4" transform="translate({x},188)">'+path('M-8 0 Q0 -7 12 0 L9 7 H-6 Z','#4a4e60','none')+path('M-24 -4 H25 M0 -8 V0','none','#4a4e60',2)+'</g>'
 return out


# Contact-driven gait: one leg supports while the other clears the ground.
def leg_pose(t,first_contact,side,walk):
 phase=((t-first_contact)/1.04 + (0.5 if side==1 else 0))%1
 base_x=-34 if side==0 else 38
 lift=0.0; roll=0.0
 if phase<.58:
  u=phase/.58
  foot_y=430-20*u
  foot_x=base_x+(3 if side==0 else -3)*(u-.5)
  roll=-13*sm(.42,.58,phase)
 else:
  u=(phase-.58)/.42
  lift=28*math.sin(math.pi*u)
  foot_y=410+20*u-lift
  foot_x=base_x+(9 if side==0 else -9)*math.sin(math.pi*u)
  roll=7*math.sin(math.pi*u)
 foot_y=430+(foot_y-430)*walk
 foot_x=base_x+(foot_x-base_x)*walk
 lift*=walk; roll*=walk
 return {'x':foot_x,'y':foot_y,'lift':lift,'roll':roll,'phase':phase}

def leg(hip,hip_y,pose,side):
 ax,ay=pose['x'],pose['y']-21
 kx=(hip+ax)*.5 + (-3 if side==0 else 3) + pose['lift']*.23
 ky=(hip_y+ay)*.52-pose['lift']*.25
 fill='#373743' if side==0 else '#42404a'
 out=path(f'M{hip-23} {hip_y-10} Q{kx-22} {ky-14} {kx-19} {ky+12} L{ax-16} {ay+4} Q{ax} {ay+13} {ax+17} {ay+4} L{kx+19} {ky+10} Q{kx+18} {ky-6} {hip+22} {hip_y-10} Z',fill,INK,2.8)
 out+=path(f'M{kx-14} {ky+4} Q{kx} {ky+10} {kx+13} {ky+4}','none','#252936',1.5)
 out+=path(f'M{hip-3} {hip_y+8} Q{kx-3} {ky-12} {kx} {ky-2}','none','#69606a',1.2,'opacity=".32"')
 out+=f'<g transform="translate({ax},{pose["y"]}) rotate({pose["roll"]})">'
 out+=path('M-16 -24 Q-4 -29 15 -23 L20 -9 Q27 0 22 5 Q6 12 -20 7 Q-25 2 -21 -7 Z','#272b36',INK,2.5)
 out+=path('M-21 5 Q0 10 23 4','none','#696471',2)
 out+=path('M-11 -16 Q0 -12 12 -15 M-9 -10 Q1 -7 13 -10','none','#67616b',1.5)
 out+='</g>'
 return out

def arm_shape(side,swing,coat,skin,roll=0,point=0):
 # Two real joints: the hand lags the upper arm. Arms counter the leg rhythm.
 sx=-64 if side<0 else 57
 ex=sx+side*(24+5*abs(swing))
 ey=89-16*swing
 hx=sx+side*(21+13*swing)
 hy=184-35*max(0,swing)+10*min(0,swing)
 hx=hx*(1-point)+52*point
 hy=hy*(1-point)+83*point
 ey=ey*(1-point)+110*point
 out=f'<g transform="rotate({roll},{sx},20)">'
 out+=path(f'M{sx-21} 17 Q{sx} 4 {sx+20} 25 L{ex+16} {ey-10} Q{ex+22} {ey+8} {hx+14} {hy-10} L{hx-12} {hy-10} Q{ex-17} {ey+8} {ex-15} {ey} Z',coat,INK,3)
 out+=path(f'M{ex-10} {ey+2} Q{ex} {ey+7} {ex+10} {ey+1}','none','#1f2b37',1.5,'opacity=".6"')
 out+=f'<g transform="translate({hx},{hy}) rotate({-swing*10})">'
 if point<.05:
  out+=path('M-12 -15 Q-16 -2 -12 11 L-7 25 Q-2 29 1 21 L0 7 L5 8 L6 23 Q12 26 14 13 L14 -7 L10 -15 Z',skin,INK,2.4)
 else:
  fy=-15-28*point
  out+=path(f'M-12 -15 Q-17 -3 -11 11 L-5 19 L-3 {fy+5} Q1 {fy-7} 5 {fy+4} L7 5 L11 1 Q21 2 18 13 L14 23 Q1 29 -10 20 Z',skin,INK,2.4)
 out+=path('M-7 -2 Q0 -2 1 7 M7 0 L8 11','none','#a86b5e',1.4)
 out+='</g></g>'
 return out

# Both 3/4 view rigs look toward local +x. Mirror to reverse eye line.
def eye(cx,cy,w,openv,pupil=0,soft=0):
 h=max(.7,7.2*openv)
 o=path(f'M{cx-w/2} {cy} Q{cx} {cy-h} {cx+w/2} {cy} Q{cx+2} {cy+h*.72} {cx-w/2} {cy} Z','#e9d9c3',INK,1.6)
 if openv>.15:
  o+=ell(cx+pupil,cy+soft,3.3,h*.67,'#554d51')+ell(cx+pupil+.5,cy+soft,1.7,h*.65,INK)+ell(cx+pupil-.5,cy-1.2+soft,.85,.8,'#e7d6bd')
 o+=path(f'M{cx-w/2-1} {cy} Q{cx} {cy-h-1.2} {cx+w/2+1} {cy}', 'none',INK,2.7)
 o+=path(f'M{cx-w/2+3} {cy+8} Q{cx} {cy+10} {cx+w/2-3} {cy+7}','none','#ae7766',1.2,'opacity=".5"')
 return o

def character(name,t,x,y,scale=1,mirror=False,phase='neutral',opacity=1,walk=0,acting=None):
 bai=name=='Bai'; skin='url(#skinB)' if bai else 'url(#skin)'; coat='url(#baiCoat)' if bai else 'url(#zeiCoat)'
 # Specific held beats replace continuously oscillating acting.
 breath_in=sm(3.48,4.05,t)*(1-sm(4.30,4.75,t)) if bai else 0
 admit=sm(3.85,4.6,t) if bai else 0
 processing=sm(8.08,8.28,t)*(1-sm(8.52,8.68,t)) if not bai else 0
 release=sm(8.56,9.06,t) if not bai else 0
 recovering=sm(9.65,10.45,t)
 slump=(14*release-6*recovering) if not bai else 0
 first_contact=10.20 if bai else 10.34
 walk=sm(9.62 if bai else 9.76,10.19 if bai else 10.33,t)
 ph=2*math.pi*(t-first_contact)/1.04
 sway=-walk*4.8*math.cos(ph)
 step_down=walk*(3.8*math.cos(2*ph)-2.0)
 tilt=0.2*math.sin(t*1.1)
 if bai and 3<=t<8: tilt=1.8*sm(3.25,3.8,t)-3.1*sm(4.0,4.75,t)+.9*sm(6.8,7.5,t)
 if not bai and 8<=t<9.6: tilt=-1.8*processing+7*release
 if bai and t>=9.6: tilt=-2.2+walk*.5*math.sin(ph-.5)
 if not bai and t<3: tilt=-2.4*sm(1.06,1.38,t)+1.1*sm(2.08,2.6,t)
 torso=walk*1.8*math.sin(ph)+(-1.2*breath_in if bai else 2.5*release)
 stretch=1+.009*breath_in-.025*release
 by=-2.7*breath_in-3*processing+slump+step_down
 theta=math.radians(torso)
 head_x=sway+245*math.sin(theta)
 head_y=by+245-245*math.cos(theta)-245*(stretch-1)
 # Stabilize the head against torso rotation while allowing a delayed nod.
 head_y+=walk*1.1*math.sin(ph-.65)
 blink=max(bell(t,2.55,.09),bell(t,3.40,.12) if bai else 0,bell(t,7.32,.11) if bai else bell(t,8.55,.13),bell(t,10.12 if bai else 10.52,.1))
 openness=1-.94*blink
 if bai and 3<=t<8: openness*=.92-.10*sm(4.05,4.75,t)
 if not bai and 8<=t<9.6: openness*=1+.32*processing-.35*release
 gaze=1.5
 if bai and 3<=t<8: gaze=-1.2+3*sm(3.60,4.0,t)
 if not bai and 8<=t<9.6: gaze=1.5-4.5*sm(8.28,8.62,t)
 if bai and t>=9.6: gaze=2.8
 # Full-film direction overrides the proof's default performance without
 # changing its approved 66–78s poses when acting is omitted.
 if acting is not None:
  walk=acting.get('walk',0); first_contact=acting.get('first_contact',.2)
  ph=2*math.pi*(t-first_contact)/1.04
  sway=-walk*4.8*math.cos(ph); step_down=walk*(3.8*math.cos(2*ph)-2.0)
  tilt=acting.get('tilt',0)+walk*.5*math.sin(ph-.5)
  torso=acting.get('torso',0)+walk*1.8*math.sin(ph)
  stretch=1+acting.get('breath',0)*.009
  by=acting.get('by',0)+step_down-acting.get('breath',0)*2.7
  theta=math.radians(torso)
  head_x=sway+245*math.sin(theta)
  head_y=by+245-245*math.cos(theta)-245*(stretch-1)+walk*1.1*math.sin(ph-.65)
  blink=acting.get('blink',0)
  openness=acting.get('openness',1)*(1-.94*blink)
  gaze=acting.get('gaze',1.5)
  processing=release=0; shoulder_roll=0
 s=f'<g transform="translate({e(x)},{e(y)}) scale({-scale if mirror else scale},{scale})" opacity="{opacity}">'
 lp=leg_pose(t,first_contact,0,walk); rp=leg_pose(t,first_contact,1,walk)
 # Contact shadows grow as each foot settles, rather than following a floating figure.
 for pp in [lp,rp]:
  s+=ell(e(pp['x']),e(pp['y']+10+pp['lift']),e(24-pp['lift']*.22),e(5-pp['lift']*.06),'#1b2430',f'opacity="{.22-pp["lift"]*.004}"')
 s+=leg(-31+sway,245+by,lp,0)+leg(36+sway,245+by,rp,1)
 s+=f'<g transform="translate({e(sway)},{e(by)}) rotate({e(torso)},0,245) translate(0,245) scale(1,{e(stretch)}) translate(0,-245)">'
 swing=walk*.80*math.cos(ph-.15)
 # Low-key preparation and release propagate through the shoulders and elbows.
 shoulder_roll=(5*processing-4*release) if not bai else -2*breath_in
 s+=arm_shape(-1,-swing,coat,skin,-shoulder_roll)
 s+=path('M-25 -49 L-29 11 Q-13 31 17 14 L20 -45 Z',skin,INK,2.8)
 s+=path('M-25 -40 Q-9 -23 18 -27 L18 -13 Q-2 -9 -25 -26 Z','#ad7464','none')
 s+=path('M-28 2 Q-64 -5 -78 29 L-62 114 L-74 251 Q-8 275 72 246 L66 114 L61 24 Q48 2 18 0 L-3 25 Z',coat,INK,3.3)
 s+=path('M-25 0 L-4 25 L18 1 L30 44 L16 89 L-30 55 Z','#dfcbb0',INK,2.2)
 s+=path('M-10 25 L-15 115 L17 121 L16 25 Q2 39 -10 25 Z','#ba9c85','none')
 s+=path('M-28 2 L-45 20 L-19 75 L-7 46 Z','#9c7787' if bai else '#50606a',INK,2.3)
 s+=path('M20 1 L36 12 L40 40 L18 77 L6 48 Z','#936c7c' if bai else '#475963',INK,2.3)
 s+=path('M-8 91 L-3 250','none','#b09096' if bai else '#597078',2,'opacity=".6"')
 s+=path('M-67 126 Q-29 139 6 134 L68 121 L67 144 Q4 161 -69 151 Z','#b28c67' if bai else '#48515b',INK,2.5)
 s+=rect(-5,133,19,17,'#cdb78b', 'rx="3" stroke="#4a424b" stroke-width="2"')
 s+=path('M-51 185 Q-36 194 -20 188 M27 188 Q45 192 55 183','none','#302c3d',2.1)
 s+=arm_shape(1,swing,coat,skin,shoulder_roll,point=(acting or {}).get('point',0))
 s+=path('M-72 25 Q-62 7 -40 5','none','#e1b378',2.8,'opacity=".6"')
 s+='</g>'
 # Head is an original curving 3/4 silhouette with separate expressive features.
 s+=f'<g transform="translate({e(head_x)},{e(head_y)}) rotate({e(tilt)},-7,-36)">'
 if bai:
  # Long back layer tucked under a short side-swept crown.
  s+=path('M-70 -164 Q-96 -132 -77 -73 Q-75 -42 -97 -10 Q-73 1 -48 -25 Q-38 -46 -42 -95 L43 -113 L40 -169 Z','#302936',INK,3)
  s+=path('M-67 -78 Q-67 -27 -86 -16 M-55 -74 Q-46 -43 -63 -18','none','#5b4254',3)
 else:
  s+=path('M-63 -165 L-76 -138 L-70 -91 L-56 -57 L-31 -63 L37 -103 L38 -167 Z','#252b34',INK,3)
 s+=path('M-51 -170 Q-26 -193 14 -182 Q44 -174 50 -149 L49 -113 Q53 -98 66 -89 Q68 -83 51 -79 L48 -57 Q39 -41 16 -31 Q-7 -22 -28 -37 L-49 -62 Q-66 -77 -64 -102 L-67 -144 Z',skin,INK,3)
 # Facial shadow defines volume along far cheek and under jaw.
 s+=path('M-62 -128 Q-63 -86 -41 -68 Q-31 -39 -8 -32 Q-27 -29 -42 -50 L-59 -71 Q-68 -90 -66 -121 Z','#b87e6b','none',0,'opacity=".48"')
 s+=path('M-44 -62 Q-10 -29 15 -37 Q-1 -21 -25 -35 Z','#b57a67','none',0,'opacity=".4"')
 s+=path('M-58 -112 Q-80 -127 -77 -104 Q-76 -83 -59 -82 Z',skin,INK,2.3)
 s+=path('M-66 -105 Q-72 -117 -73 -107 Q-69 -104 -68 -94','none','#a66a60',2)
 s+=path('M40 -115 Q43 -99 39 -85 Q43 -80 49 -82','none','#a66c60',1.7)
 s+=path('M46 -80 L49 -79','none','#73514e',2)
 # Eye positions avoid symmetrical mask-like construction.
 s+=eye(-14,-111,30,openness,gaze,soft=(acting or {}).get('eye_y',0))
 s+=eye(34,-112,17,openness,gaze*.5,soft=(acting or {}).get('eye_y',0))
 # Brow pose: Bai openness in admission; Zei questioning then strained groan.
 brow=0
 if bai: brow=-1.3*admit if t<8 else -2*recovering
 else: brow=-4.0*sm(1,1.7,t) if t<3 else 0
 if not bai and t>=8: brow=-3*processing+2.6*release*(1-.55*recovering)
 if acting is not None: brow=acting.get('brow',0)
 s+=path(f'M-31 {-127+brow} Q-16 {-132+brow} -1 {-127-brow*.45}','none','#47333b' if bai else '#292b34',3.7)
 s+=path(f'M27 {-128-brow*.4} Q35 {-131+brow} 43 {-126+brow}','none','#47333b' if bai else '#292b34',3.1)
 # Mouth acting on original caption beats, no claim of lip sync without voices.
 speaking=(bai and (4.18<t<4.50 or 4.75<t<5.17 or 5.46<t<5.94)) or (not bai and (1.13<t<1.38 or 1.52<t<1.91 or 2.04<t<2.30))
 if acting is not None: speaking=acting.get('speaking',False)
 if speaking:
  a=(.5+.5*math.sin(t*10))*.7
  mh=1.2+3.6*a
  s+=path(f'M11 -60 Q23 {-61-mh*.15} 35 -61 Q25 {-53+mh} 14 -57 Z','#775055','#774e4b',1.3)
  if a>.45: s+=path('M14 -60 L32 -60 L29 -58 L16 -58 Z','#e0c6af','none')
 elif bai:
  smile=(2.3*sm(9.6,10.2,t) if t>=9.6 else .25+.45*sm(6.7,7.5,t))
  if acting is not None: smile=acting.get('smile',.6)
  s+=path(f'M10 -59 Q24 {-56+smile} 36 {-61-smile*.35}','none','#834f4c',1.8)
 else:
  if t>=8 and acting is None:
   strain=sm(8.35,9,t)*(1-.72*sm(9.6,10.25,t))
   s+=path(f'M9 {-58+strain*2} Q22 {-59-strain*2.2} 35 {-59+strain*1.5}','none','#774b48',2.1)
  else: s+=path('M12 -59 Q23 -57 35 -60','none','#80514b',1.8)
 s+=path('M18 -51 Q26 -50 30 -53','none','#b77869',1,'opacity=".6"')
 if bai:
  # Layered, asymmetric hair catches the rim light.
  s+=path('M-75 -107 Q-94 -151 -65 -182 Q-46 -212 -1 -202 Q47 -202 56 -164 Q52 -143 41 -139 Q34 -167 10 -174 Q-16 -142 -57 -136 L-51 -94 L-62 -75 L-64 -121 Z','#352d3a',INK,3.3)
  s+=path('M-65 -179 Q-45 -199 -12 -196 Q-43 -182 -48 -163 Q-61 -154 -72 -141 Z','#514050','none')
  s+=path('M-51 -159 Q-15 -165 9 -188 Q26 -186 39 -173 Q19 -163 7 -155 Q-9 -147 -25 -146 Z','#574153','none')
  s+=path('M-70 -164 Q-59 -187 -33 -193','none','#b99178',2,'opacity=".65"')
  s+=path('M24 -189 Q45 -179 49 -158','none','#99727a',2.7)
  s+=path('M-65 -133 L-54 -138','none','#d7b381',4)
  s+=ell(-69,-84,2.5,4,'#d9b272')
 else:
  s+=path('M-74 -99 L-77 -136 L-87 -156 L-67 -156 L-73 -181 L-49 -173 Q-44 -199 -16 -202 L-21 -188 Q7 -211 35 -196 L29 -186 Q50 -185 57 -161 L45 -140 L27 -151 L10 -166 Q-19 -143 -45 -148 L-54 -114 L-58 -92 Z','#262c36',INK,3.3)
  s+=path('M-61 -175 Q-29 -196 10 -188 Q-12 -171 -41 -163 Z','#3c424b','none')
  s+=path('M8 -174 Q32 -181 47 -157 L36 -158 L23 -168 Z','#41464e','none')
  s+=path('M-62 -170 Q-47 -186 -31 -188','none','#b69b7c',2,'opacity=".6"')
 s+='</g></g>'
 return s

def frame(t):
 out=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+defs()+rect(0,0,W,H,'#0e1520')+'<g clip-path="url(#frame)">'
 out+=street(t)
 # Reflection only in wider angles; independent, muted silhouette, not a duplicate overlay on faces.
 if t<1 or t>=9.6:
  drift=sm(10,12,t)*62 if t>=9.6 else 0
  cam=0 if t<9.6 else -34*sm(10.15,12,t)
  out+=f'<defs><clipPath id="reflectionWindow"><rect x="{41+cam}" y="229" width="1178" height="592"/></clipPath></defs><g opacity=".14" clip-path="url(#reflectionWindow)">'
  out+=character('Bai',t,378-drift*.6,516,1.13,False,opacity=1,walk=sm(10,10.6,t))
  out+=character('Zei',t,890-drift*.6,504,1.16,True,opacity=1,walk=sm(10.1,10.7,t))
  out+='</g>'
  # Window mullions occlude reflections; cast light is stable across the cut.
  out+=rect(390+cam,211,14,630,'#343c46')+rect(808+cam,211,14,630,'#343c46')
  out+=path(f'M{42+cam} 784 L{1218+cam} 711','none','#d7c3aa',2,'opacity=".28"')
 # Cut rhythm is explicit, not an automated slideshow.
 if t<1:
  out+=character('Bai',t,629,542,1.55)
  out+=character('Zei',t,1276,527,1.59,True)
 elif t<3:
  zoom=2.56+.035*sm(1,3,t)
  out+=character('Zei',t,1044,661,zoom,True)
  # OTS Bai's shoulder keeps spatial orientation in the closeup.
  out+=path('M-100 999 V728 Q20 606 153 618 Q234 644 273 999 Z','#463b4e','none')
 elif t<8:
  zoom=2.56+.08*sm(3,8,t)
  out+=character('Bai',t,839,664,zoom)
  out+=path('M1680 999 Q1690 747 1843 650 Q1960 644 2000 782 V999 Z','#222f3a','none')
 else:
  if t<9.6:
   out+=character('Zei',t,1053,661,2.6,True)
   out+=path('M-100 999 V728 Q20 606 153 618 Q234 644 273 999 Z','#463b4e','none')
  else:
   walking=sm(9.62,10.19,t); drift=sm(10.2,12,t)*10
   # Tracking resumes as they walk toward the camera; eyelines stay inward.
   out+=character('Bai',t,645+drift,446,1.17,False,walk=walking)
   out+=character('Zei',t,1242+drift*.82,430,1.20,True,walk=sm(9.76,10.33,t))
 # Warm diagonal sunlight and soft edge falloff preserve readable faces.
 out+=path('M0 80 L480 80 L1450 1000 L1260 1000 Z','#e8b778','none',0,'opacity=".045"')
 out+=rect(0,80,W,920,'url(#vignette)')
 # Floating dust is subtle and seeded by deterministic trig, not randomness.
 for i in range(14):
  x=(i*173+math.sin(i*5)*50+t*(3+i%4))%1920
  y=170+(i*119)%650+math.sin(t*.8+i)*7
  out+=ell(e(x),e(y),1.15,1.15,'#ecd0a3','opacity=".22"')
 out+='</g>'
 out+=rect(0,0,W,80,'#101620')+rect(0,1000,W,80,'#101620')
 # Minimal proof slate outside picture, never covering faces.
 out+='<text x="76" y="47" fill="#d4c4b3" font-family="DejaVu Sans" font-size="21" letter-spacing="4">THE SURPLUS</text>'
 out+='<text x="1844" y="47" text-anchor="end" fill="#98979c" font-family="DejaVu Sans" font-size="17" letter-spacing="2">REFINED ANIMATION PROOF · 66–78s</text>'
 sub=''
 if 1<=t<3: sub='Zei: A fair match?'
 if 4<=t<8: sub='Bai: Some time with you.'
 if sub:
  bw=540 if t<3 else 720
  out+=rect((W-bw)/2,909,bw,64,'#111b29','rx="10" opacity=".86"')
  out+=f'<text x="960" y="954" text-anchor="middle" fill="#f4ecdf" font-family="DejaVu Sans" font-size="35" font-weight="500">{sub}</text>'
 out+='<text x="960" y="1047" text-anchor="middle" fill="#939299" font-family="DejaVu Sans" font-size="17" letter-spacing="1.4">UNOFFICIAL SNOWMOON ADAPTATION · CHAPTER 5 · VITALIK BUTERIN · GPLv3</text>'
 return out+'</svg>'

def export(i):
 svg=ROOT/'svg'/f'{i:04}.svg'; png=ROOT/'frames'/f'{i:04}.png'
 svg.write_text(frame(i/FPS))
 p=subprocess.run(['inkscape',str(svg),'--export-type=png',f'--export-filename={png}','--export-width=1920','--export-height=1080'],env={**os.environ,'HOME':str(ROOT/'inkscape-home'),'XDG_CACHE_HOME':str(ROOT/'inkscape-home/.cache')},stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 if p.returncode: raise RuntimeError(p.stderr.decode())
 return i
if __name__=='__main__':
 ap=argparse.ArgumentParser(); ap.add_argument('--preview',action='store_true'); ap.add_argument('--workers',type=int,default=4); a=ap.parse_args()
 for d in ['svg','frames','inkscape-home/.cache']: (ROOT/d).mkdir(parents=True,exist_ok=True)
 indices=[0,42,97,144,200,219,249,279] if a.preview else range(N)
 with ThreadPoolExecutor(max_workers=a.workers) as ex:
  for n,i in enumerate(ex.map(export,indices)):
   if a.preview or n%24==0: print(f'Rendered {i+1}/{N}',flush=True)
