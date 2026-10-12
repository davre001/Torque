"""Low-storage renderer of the locked TORQUE motion design. No network or secrets."""
from pathlib import Path
import json, math, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
PUBLIC=HERE/'remotion/public'
OUT=HERE/'final'
OUT.mkdir(exist_ok=True)
FF=Path('C:/Users/USER/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe')
W,H,FPS=1280,720,24
BG='#101410'; LIME='#CAEF72'; WHITE='#F4F5EC'; MUTED='#9AA292'
def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',n)
shots=[
 (7,'TORQUE / ISSUE TO EVIDENCE','A fix you can trust.','Turn GitHub issues into tested, independently verified pull requests.','intro',None),
 (10,'01 / THE AGENT','One issue. A coordinated team.','Investigate, implement, test and independently verify.','pipeline',None),
 (12,'02 / REAL ISSUE','Respect reduced motion.','The demo autoplayed despite a visitor’s reduced-motion preference.','media','issue.mp4'),
 (10,'03 / COMPLETED RUN','The patch is backed by evidence.','Run 6634790a… completed on attempt 1.','media','run.mp4'),
 (9,'04 / INDEPENDENT TESTS','Three browser checks passed.','The verifier approved the change against the original requirements.','media','verified.mp4'),
 (12,'05 / REVIEWABLE PULL REQUEST','A targeted fix. Ready for review.','kokon PR #1 · controlled demo repository; no upstream PR created.','media','pr.mp4'),
 (22,'06 / NEATLOGS CRITICAL INCIDENTS','Find the failure. Verify the fix.','Neatlogs: original generic error → incident → named failure → passing trace.','media','incident.mp4'),
 (12,'07 / DIAGNOSIS TO RESOLUTION','Make the failing check visible.','We added named child spans, captured output and assertion details.','diagnostic',None),
 (9,'08 / VERIFIED AND SHIPPED','The incident is resolved.','Instrumentation shipped in TORQUE PR #1; remote browser checks verified.','resolved',None),
 (8,'09 / ENTIRE','Keep the work behind the change.','Agent-assisted development captured in checkpoints linked to commits.','entire',None),
 (11,'10 / CFO.AI','Model the economics.','Pricing, inference and recovery costs. Forecasts are planning assumptions.','media','cfo-summary.png'),
 (6,'TORQUE','From issue to evidence.','From patch to verified pull request.','outro',None),
]
def ease(t):return 1-(1-max(0,min(1,t)))**4
def reveal(d,xy,text,size,frame,delay=0,color=WHITE,bold=False):
 p=ease((frame-delay)/12); y=xy[1]+round(20*(1-p))
 rgb=tuple(round(int(color[k:k+2],16)*p+int(BG[k:k+2],16)*(1-p)) for k in (1,3,5))
 d.text((xy[0],y),text,font=font(size,bold),fill=rgb)
def canvas(i,f,transparent=False):
 s=shots[i];im=Image.new('RGBA' if transparent else 'RGB',(W,H),(0,0,0,0) if transparent else BG);d=ImageDraw.Draw(im)
 if not transparent:
  for x in range(0,W,54):d.line((x,0,x,H),fill='#1A2318')
  for y in range(0,H,54):d.line((0,y,W,y),fill='#1A2318')
 reveal(d,(70,38),s[1],16,f,color=LIME,bold=True)
 reveal(d,(70,72),s[2],43,f,2,bold=True)
 reveal(d,(70,130),s[3],21,f,4,color=MUTED)
 d.text((70,684),'TORQUE / PRODUCT DEMO',font=font(12),fill=MUTED)
 d.text((1155,684),f'{i+1:02d} / 12',font=font(12),fill=MUTED)
 d.rectangle((0,717,round(W*(i+f/(s[0]*FPS))/len(shots)),719),fill=LIME)
 return im
def card(d,x,y,w,label,number,f,delay=0):
 p=ease((f-delay)/12);dy=round((1-p)*20)
 if p<=0:return
 d.rounded_rectangle((x,y+dy,x+w,y+dy+150),radius=16,fill='#182017',outline='#384332',width=1)
 d.text((x+24,y+dy+23),number,font=font(18),fill=LIME)
 d.text((x+24,y+dy+79),label,font=font(24,True),fill=WHITE)
def frame(i,f):
 s=shots[i];im=canvas(i,f);d=ImageDraw.Draw(im);kind=s[4]
 if kind in ('intro','outro'):
  p=ease(f/24);d.arc((92,246,312,466),-90,-90+359*p,fill=LIME,width=14)
  if p>.3:d.line((202,262,202,356,269,395),fill=LIME,width=14)
  reveal(d,(365,259),'TORQUE.',100,f,8,bold=True)
  reveal(d,(370,385),'BUILT TO SHOW ITS WORK',19,f,14,color=LIME)
 if kind=='pipeline':
  for j,label in enumerate(['Investigate','Implement','Test','Verify']):
   card(d,70+j*291,240,267,label,f'0{j+1}',f,8+j*2)
   if j<3:d.text((342+j*291,300),'›',font=font(28),fill=LIME)
  reveal(d,(70,475),'Bounded recovery when an attempt fails.',29,f,26,color=LIME)
  d.text((70,526),'The recorded reduced-motion run succeeded on its first attempt.',font=font(19),fill=MUTED)
 if kind=='diagnostic':
  d.rounded_rectangle((70,220,1210,447),radius=16,fill='#1B2418',outline='#455138')
  reveal(d,(100,249),'CONTROLLED INSTRUMENTATION VERIFICATION / EVIDENCE GRAPHIC',15,f,6,color=MUTED)
  reveal(d,(100,295),'test.name: result-equals-10',28,f,10,color=LIME)
  reveal(d,(100,349),'AssertionError: expected 10, actual 8',38,f,14,bold=True)
  reveal(d,(70,491),'Corrected fixture → unchanged check passes.',29,f,72,color=LIME)
  d.text((70,550),'Verifies diagnostic visibility; separate from the issue-to-PR run.',font=font(20),fill=MUTED)
 if kind=='resolved':
  for j,label in enumerate(['Named test spans','Output + stack trace','Remote checks passed']):card(d,70+j*387,224,363,label,f'0{j+1}',f,8+j*2)
  reveal(d,(70,427),'RESOLVED / d5d9ddaa…',32,f,32,color=LIME,bold=True)
  d.text((70,489),'Controlled failing and passing traces verified in hosted Neatlogs.',font=font(22),fill=WHITE)
  d.text((70,532),'Remote browser logs were checked separately; not uploaded to Neatlogs.',font=font(19),fill=MUTED)
 if kind=='entire':
  for j,label in enumerate(['Agent session','Entire checkpoint','Linked commit']):card(d,70+j*387,224,363,label,f'0{j+1}',f,8+j*2)
  reveal(d,(70,431),'01M4K5QBAVZ507XR140XFW7586',31,f,20,color=LIME)
  d.text((70,487),'commit c081469dacf1…',font=font(24),fill=WHITE)
  d.text((70,537),'Recorded development evidence / graphic',font=font(19),fill=MUTED)
 return im
def run(args):subprocess.run([str(FF),'-hide_banner','-loglevel','error','-y',*args],check=True)
enc=['-c:v','libx264','-threads','1','-preset','veryfast','-crf','20','-pix_fmt','yuv420p']
for i,s in enumerate(shots):
 target=OUT/f'scene-{i:02d}.mp4'
 if target.exists() and target.stat().st_size>1000:continue
 print(f'Rendering {i+1}/{len(shots)}: {s[2]}',flush=True)
 if s[4]=='media':
  overlay=OUT/f'overlay-{i}.png';canvas(i,s[0]*FPS-1,True).save(overlay)
  source=PUBLIC/s[5];still=source.suffix=='.png'
  inputs=(['-loop','1'] if still else [])+['-threads','1','-i',str(source),'-loop','1','-i',str(overlay)]
  # Letterboxed captured evidence remains readable; only the frame receives animation.
  filt=f'[0:v]fps={FPS},scale=1140:488:force_original_aspect_ratio=decrease,pad=1140:488:(ow-iw)/2:(oh-ih)/2:color=0x182017,tpad=stop_mode=clone:stop_duration={s[0]}[screen];color=c=0x101410:s={W}x{H}:r={FPS}:d={s[0]}[bg];[bg][screen]overlay=70:180[stage];[stage][1:v]overlay=0:0[v]'
  run(['-filter_complex_threads','1',*inputs,'-filter_complex',filt,'-map','[v]','-t',str(s[0]),'-an',*enc,str(target)])
 else:
  proc=subprocess.Popen([str(FF),'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-an',*enc,str(target)],stdin=subprocess.PIPE)
  for f in range(s[0]*FPS):proc.stdin.write(frame(i,f).tobytes())
  proc.stdin.close()
  if proc.wait()!=0:raise RuntimeError('Frame renderer failed')
 if i in (0,1,5,7,10):
  if s[4]!='media':frame(i,100).save(OUT/f'preview-{i}.jpg')
  else:run(['-threads','1','-ss','3','-i',str(target),'-frames:v','1','-threads','1',str(OUT/f'preview-{i}.jpg')])
concat=OUT/'concat.txt';concat.write_text('\n'.join("file '"+f'scene-{i:02d}.mp4'+"'" for i in range(len(shots))))
run(['-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(OUT/'TORQUE-demo.mp4')])
(OUT/'timeline.json').write_text(json.dumps([dict(seconds=s[0],title=s[2],source=s[5]) for s in shots],indent=2))
print('Finished: '+str(OUT/'TORQUE-demo.mp4'),flush=True)
