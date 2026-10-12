export default async ({project}) => {
 const p=await project({dir:"/home/user/torque-motion",size:"1280x720",fps:24,background:"#090b0f"});
 const C={white:"#f7f8fa",muted:"#a1abb9",lime:"#c6fa64",panel:"#151b24",line:"#293342",red:"#ff7777"};
 const enter=(delay=0)=>[{property:"opacity",from:0,to:1,at:delay,duration:.45},{property:"offsetY",from:24,to:0,at:delay,duration:.6,easing:"house"}];
 const label=(s,x,y,size=24,color=C.white,delay=0,w=1100)=><text x={x} y={y} width={w} height={size*1.6} fontFamily="Inter" fontWeight={size>40?700:400} fontSize={size} color={color} animate={enter(delay)}>{s}</text>;
 const card=(title,sub,x,y,w=340,delay=0,color=C.lime)=><frame x={x} y={y} width={w} height={155} layout="none" background={C.panel} radius={16} motion={{enter:{from:{y:30,opacity:0},duration:.6,at:delay}}}>
 <rect x={20} y={22} width={28} height={4} fill={color}/>{label(title,20,48,25,C.white,0,w-40)}{label(sub,20,95,17,C.muted,0,w-40)}</frame>;
 let cursor=0;
 const scene=(name,dur,nodes)=>{
 p.compose(<frame width={1280} height={720} layout="none" motion={{exit:{to:{opacity:0},duration:.25,anchor:"end"}}}>
 <rect x={70} y={55} width={36} height={5} fill={C.lime}/>{label("TORQUE",120,40,22,C.white)}
 {label(name.toUpperCase(),920,44,14,C.muted,0,290)}
 <rect x={70} y={653} width={1140} height={1} fill={C.line}/>
 {label("neatHack  /  October 2026",70,671,13,C.muted)}
 {nodes}
 <rect x={70} y={653} width={1140} height={2} fill={C.lime} animate={[{property:"scaleX",from:.001,to:1,duration:dur-.3,easing:"linear"}]}/>
 </frame>,{at:cursor,dur,name}); cursor+=dur;
 };
 scene("Issue to pull request",7,<>
 {label("TORQUE",70,170,112,C.white,0)}
 {label("From GitHub issue",76,325,44,C.white,.35)}
 {label("to verified pull request.",76,390,44,C.lime,.65)}
 {label("Investigate. Implement. Verify. Recover.",78,515,24,C.muted,1)}
 <rect x={1050} y={200} width={10} height={300} radius={5} fill={C.lime} animate={[{property:"rotation",from:-15,to:15,duration:6,easing:"smooth"}]}/>
 </>);
 scene("The problem",7,<>
 {label("An issue is only the beginning.",70,160,49)}
 {card("Understand the code","Find the cause behind the report.",70,300,350,.25)}
 {card("Prove the fix","Run independent acceptance tests.",465,300,350,.6)}
 {card("Handle failure","Inspect what broke. Change strategy.",860,300,350,.95)}
 {label("TORQUE connects these steps in one agent workflow.",70,525,27,C.muted,1.3)}
 </>);
 scene("Agent workflow",10,<>
 {label("One issue. A coordinated workflow.",70,160,45)}
 {["Investigate","Implement","Verify"].map((t,i)=>card(t,["Diagnose and plan","Patch and run tests","Review against the issue"][i],70+i*395,290,350,.3+i*.6))}
 {label("GitHub issue",70,495,24,C.muted,.3)}
 {label("Isolated worktree",465,495,24,C.muted,.9)}
 {label("Verified draft PR",860,495,24,C.lime,1.5)}
 {label("Failed attempt? The recovery agent revises the strategy.",70,565,24,C.muted,2.3)}
 </>);
 scene("Trace-informed recovery",12,<>
 {label("Failure becomes useful evidence.",70,150,47)}
 {label("neatlogs",70,235,30,C.lime,.3)}
 {card("01  Test fails","Independent assertion rejects patch.",70,310,350,.5,C.red)}
 {card("02  Read failed trace","Finalized metadata informs recovery.",465,310,350,1.4)}
 {card("03  Revise and retest","The unchanged assertion passes.",860,310,350,2.3)}
 {label("Controlled recovery drill: deliberately seeded incorrect patch.",70,515,23,C.muted,3)}
 {label("Separate from the GitHub demo, which passed on attempt one.",70,560,21,C.muted,3.3)}
 </>);
 scene("Development evidence",8,<>
 {label("Entire",70,165,72,C.white)}
 {label("A record of agent-assisted development.",70,270,35,C.muted,.3)}
 {card("Checkpoint","Captured work linked to a commit.",70,370,545,.6)}
 {card("Commit context","Review the work behind the change.",665,370,545,1)}
 </>);
 scene("Business planning",9,<>
 {label("cfo.ai",70,155,72)}
 {label("Model the cost of getting to a verified fix.",70,260,35,C.muted,.3)}
 {card("Pricing","Subscriptions and included issue runs.",70,355,350,.6)}
 {card("Costs","Inference, compute and recovery.",465,355,350,1)}
 {card("Sensitivity","Usage, retries and success rate.",860,355,350,1.4)}
 {label("Financial forecasts are planning assumptions.",70,555,22,C.muted,1.9)}
 </>);
 scene("Closing",7,<>
 {label("TORQUE",70,165,104)}
 {label("Fix. Verify. Recover.",76,315,60,C.lime,.4)}
 {label("Real issue-to-PR evidence.",78,435,30,C.white,.8)}
 {label("A separate controlled recovery demonstration.",78,485,28,C.muted,1.2)}
 {label("neatlogs   /   Entire   /   cfo.ai",78,570,22,C.muted,1.6)}
 </>);
 await p.frame(3,"renders/intro.png");
 await p.frame(28,"renders/recovery.png");
};
