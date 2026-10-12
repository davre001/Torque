import React from 'react';
import {AbsoluteFill, Composition, Easing, Img, OffthreadVideo, Sequence, interpolate, registerRoot, staticFile, useCurrentFrame} from 'remotion';
import {z} from 'zod';

const lime='#CAEF72', muted='#9AA292';
const ease=Easing.bezier(.2,0,0,1);
const shots=[
 {seconds:7,tag:'TORQUE / ISSUE TO EVIDENCE',title:'A fix you can trust.',body:'Turn GitHub issues into tested, independently verified pull requests.',kind:'intro'},
 {seconds:10,tag:'01 / THE AGENT',title:'One issue. A coordinated team.',body:'Investigate → implement → run acceptance tests → independently verify.',kind:'pipeline'},
 {seconds:12,tag:'02 / REAL ISSUE',title:'Respect reduced motion.',body:'The demo video autoplayed despite a visitor’s reduced-motion preference.',media:'issue.mp4'},
 {seconds:10,tag:'03 / COMPLETED RUN',title:'The patch is backed by evidence.',body:'Saved run 6634790a… · reduced-motion fix completed on attempt 1.',media:'run.mp4'},
 {seconds:9,tag:'04 / INDEPENDENT TESTS',title:'Three browser checks passed.',body:'The verifier approved the change against the original requirements.',media:'verified.mp4'},
 {seconds:12,tag:'05 / REVIEWABLE PULL REQUEST',title:'A targeted fix. Ready for review.',body:'davre001/kokon · PR #1 · controlled demo repository, no upstream PR created.',media:'pr.mp4'},
 {seconds:22,tag:'06 / NEATLOGS CRITICAL INCIDENTS',title:'Find the failure. Verify the fix.',body:'Neatlogs: original generic error → incident → named failure → passing trace.',media:'incident.mp4'},
 {seconds:12,tag:'07 / DIAGNOSIS → RESOLUTION',title:'Make the failing check visible.',body:'Named child spans + captured output + bounded assertion details.',kind:'diagnostic'},
 {seconds:9,tag:'08 / VERIFIED AND SHIPPED',title:'The incident is resolved.',body:'Remote browser workflow verified. Instrumentation merged in TORQUE PR #1.',kind:'resolved'},
 {seconds:8,tag:'09 / ENTIRE',title:'Keep the work behind the change.',body:'Agent-assisted development captured in checkpoints linked to commits.',kind:'entire'},
 {seconds:11,tag:'10 / CFO.AI',title:'Model the economics.',body:'Pricing, inference and recovery costs. Forecasts are planning assumptions.',media:'cfo-summary.png'},
 {seconds:6,tag:'TORQUE',title:'From issue to evidence.',body:'From patch to verified pull request.',kind:'outro'},
];
const durations=shots.map(s=>s.seconds*30);
const total=durations.reduce((a,b)=>a+b,0);
const schema=z.object({title:z.string()});

function Reveal({children,delay=0,style={}}:{children:React.ReactNode,delay?:number,style?:React.CSSProperties}){
 const f=useCurrentFrame(); const p=interpolate(f,[delay,delay+18],[0,1],{easing:ease,extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 return <div style={{opacity:p,transform:`translateY(${(1-p)*28}px)`,...style}}>{children}</div>;
}
function Ring(){const f=useCurrentFrame();const p=interpolate(f,[0,36],[0,1],{easing:ease,extrapolateRight:'clamp'});return <svg width="350" height="350" viewBox="0 0 350 350"><circle cx="175" cy="175" r="125" fill="none" stroke={lime} strokeWidth="22" strokeDasharray="785" strokeDashoffset={785*(1-p)} transform="rotate(-90 175 175)"/><path d="M175 67V175L252 218" fill="none" stroke={lime} strokeWidth="22" style={{opacity:p}}/><circle cx="175" cy="175" r="12" fill={lime}/></svg>}
function Cards({items}:{items:string[]}){return <div style={{display:'flex',gap:24,marginTop:70}}>{items.map((x,i)=><Reveal key={x} delay={12+i*2} style={{flex:1,border:'1px solid #384332',borderRadius:22,padding:34,background:'#182017'}}><div style={{color:lime,fontSize:23,marginBottom:35}}>0{i+1}</div><div style={{fontSize:35,fontWeight:600}}>{x}</div></Reveal>)}</div>}
function Scene({shot,index}:{shot:typeof shots[number],index:number}){
 const f=useCurrentFrame();const zoom=interpolate(f,[0,48],[1,1.025],{easing:Easing.inOut(Easing.cubic),extrapolateRight:'clamp'});
 const media='media' in shot ? shot.media : undefined;
 return <AbsoluteFill style={{padding:'70px 104px',background:'#101410',color:'#F4F5EC',fontFamily:'Segoe UI, Arial, sans-serif',overflow:'hidden'}}>
 <AbsoluteFill style={{opacity:.14,backgroundImage:'linear-gradient(#526343 1px, transparent 1px),linear-gradient(90deg,#526343 1px,transparent 1px)',backgroundSize:'80px 80px',transform:`translateY(${Math.sin(f/600*Math.PI*2)*5}px)`}}/>
 <div style={{position:'relative'}}>
 <Reveal style={{fontSize:22,letterSpacing:4,color:lime,fontWeight:600}}>{shot.tag}</Reveal>
 <Reveal delay={3} style={{fontSize:media?60:76,fontWeight:650,letterSpacing:-2,lineHeight:1.1,marginTop:24}}>{shot.title}</Reveal>
 <Reveal delay={6} style={{fontSize:28,color:muted,marginTop:20,maxWidth:1580,lineHeight:1.4}}>{shot.body}</Reveal>
 {media && <Reveal delay={9} style={{marginTop:32,height:672,borderRadius:18,overflow:'hidden',border:'1px solid #455138',boxShadow:'0 24px 60px #0008',background:'#182017'}}>
 <div style={{height:'100%',transform:`scale(${zoom})`,transformOrigin:'center'}}>{media.endsWith('.png')?<Img src={staticFile(media)} style={{width:'100%',height:'100%',objectFit:'contain'}}/>:<OffthreadVideo src={staticFile(media)} muted style={{width:'100%',height:'100%',objectFit:'contain'}}/>}</div>
 </Reveal>}
 {(shot.kind==='intro'||shot.kind==='outro')&&<div style={{display:'flex',alignItems:'center',marginTop:80,gap:70}}><Ring/><Reveal delay={12}><div style={{fontSize:150,fontWeight:700,letterSpacing:-8}}>TORQUE<span style={{color:lime}}>.</span></div><div style={{fontSize:26,color:muted,letterSpacing:4}}>BUILT TO SHOW ITS WORK</div></Reveal></div>}
 {shot.kind==='pipeline'&&<><Cards items={['Investigate','Implement','Test','Verify']}/><Reveal delay={30} style={{marginTop:90,fontSize:34,color:lime}}>Bounded recovery when an attempt fails.</Reveal><div style={{marginTop:25,fontSize:24,color:muted}}>The recorded reduced-motion run succeeded on its first attempt.</div></>}
 {shot.kind==='diagnostic'&&<><Reveal delay={12} style={{marginTop:60,borderRadius:20,padding:42,background:'#1B2418',border:'1px solid #455138'}}><div style={{fontSize:22,color:muted,letterSpacing:2}}>CONTROLLED INSTRUMENTATION VERIFICATION / EVIDENCE GRAPHIC</div><div style={{fontSize:32,marginTop:35}}>test.name: <span style={{color:lime}}>result-equals-10</span></div><div style={{fontSize:47,marginTop:24,fontFamily:'Consolas, monospace'}}>AssertionError: expected 10, actual 8</div></Reveal><Reveal delay={75} style={{marginTop:50,fontSize:35,color:lime}}>Corrected fixture → unchanged check passes.</Reveal><div style={{marginTop:20,fontSize:24,color:muted}}>This verifies diagnostic visibility; it is separate from the issue-to-PR run.</div></>}
 {shot.kind==='resolved'&&<><Cards items={['Named test spans','Output + stack trace','Verified remote checks']}/><Reveal delay={40} style={{marginTop:70,fontSize:40,color:lime}}>RESOLVED / d5d9ddaa…</Reveal><div style={{marginTop:20,fontSize:27,color:muted}}>Controlled failing and passing traces verified in hosted Neatlogs.</div><div style={{marginTop:15,fontSize:23,color:muted}}>Remote browser logs were verified separately and were not uploaded to Neatlogs.</div></>}
 {shot.kind==='entire'&&<><Cards items={['Agent session','Entire checkpoint','Linked commit']}/><Reveal delay={25} style={{marginTop:65,padding:35,borderLeft:`4px solid ${lime}`,fontFamily:'Consolas, monospace',fontSize:31}}>01M4K5QBAVZ507XR140XFW7586<br/><span style={{color:muted,fontSize:25}}>commit c081469dacf1…</span></Reveal><div style={{marginTop:25,fontSize:23,color:muted}}>Recorded development evidence / graphic</div></>}
 </div>
 <div style={{position:'absolute',bottom:24,left:104,right:104,display:'flex',justifyContent:'space-between',color:muted,fontSize:18}}><span>TORQUE / PRODUCT DEMO</span><span>{String(index+1).padStart(2,'0')} / {shots.length}</span></div>
 <div style={{position:'absolute',bottom:0,left:0,width:`${(index+interpolate(f,[0,durations[index]],[0,1],{extrapolateRight:'clamp'}))/shots.length*100}%`,height:4,background:lime}}/>
 </AbsoluteFill>;
}
function Film(){let start=0;return <AbsoluteFill>{shots.map((shot,index)=>{const from=start;start+=durations[index];return <Sequence key={index} from={from} durationInFrames={durations[index]}><Scene shot={shot} index={index}/></Sequence>;})}</AbsoluteFill>}
registerRoot(()=> <Composition id="TorqueLaunch" component={Film} width={1920} height={1080} fps={30} durationInFrames={total} schema={schema} defaultProps={{title:'TORQUE'}}/>);
