// Bundle actual Gallery.tsx with controlled I/O fixtures. Never run repo scripts.
const fs = require('node:fs');
const path = require('node:path');
const esbuild = require('esbuild');
const [workspace, output] = process.argv.slice(2);
const reactDir = path.dirname(require.resolve('react/package.json'));
const reactDomDir = path.dirname(require.resolve('react-dom/package.json'));
const fixtures = `
import React from 'react';
const initial = [{id:'one',prompt:'A blue bird on a branch',favorite:false}, {id:'two',prompt:'A green mountain',favorite:false}];
let items=initial.map(g=>({...g}));
window.fixture={events:[],confirm:true};
export const api={gallery:async()=>({items:items.map(g=>({...g})),total:items.length}),
 setFavorite:async(id,favorite)=>{window.fixture.events.push(['favorite',id,favorite]);let g=items.find(g=>g.id===id);g.favorite=favorite;return {...g};},
 deleteGeneration:async(id)=>{window.fixture.events.push(['delete',id]);items=items.filter(g=>g.id!==id);}};
export const urls={genThumb:()=> 'data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="blue"/></svg>')};
export const native={confirm:async()=>window.fixture.confirm};
export const useStore=selector=>selector({galleryVersion:0});
export const openGeneration=async(g)=>window.fixture.events.push(['open',g.id]);
export const forgetGeneration=(id)=>window.fixture.events.push(['forget',id]);
export const setState=()=>{};
export const toastError=()=>{window.fixture.error=true;};
export const IconButton=({title,children,active,...props})=>React.createElement('button',{...props,title,'aria-label':title},children);
export const Seg=({value,options,onChange})=>React.createElement('div',{},options.map(o=>React.createElement('button',{key:o.value,onClick:()=>onChange(o.value)},o.label)));
const icon=({size=24,...props})=>React.createElement('svg',{...props,width:size,height:size,'aria-hidden':true});
export const ArrowLeft=icon,Heart=icon,Loader2=icon,Search=icon,Trash2=icon;
`;
(async()=>{
  fs.mkdirSync(output,{recursive:true});
  await esbuild.build({stdin:{contents:`import React from 'react';import {createRoot} from 'react-dom/client';import {Gallery} from './src/components/Gallery.tsx';createRoot(document.getElementById('root')).render(React.createElement(Gallery));`,resolveDir:workspace,loader:'tsx'},
    outfile:path.join(output,'app.js'),bundle:true,format:'iife',platform:'browser',jsx:'automatic',define:{'process.env.NODE_ENV':'"production"'},
    plugins:[{name:'reviewed-fixtures',setup(build){
      build.onResolve({filter:/^(react|react-dom)(\/.*)?$/},args=>({path:require.resolve(args.path,{paths:[reactDir,reactDomDir]})}));
      build.onResolve({filter:/^(lucide-react|\.\.\/lib\/(api|native|store|types)|\.\/ui)$/},args=>({path:'fixtures',namespace:'fixture'}));
      build.onLoad({filter:/.*/,namespace:'fixture'},()=>({contents:fixtures,loader:'js',resolveDir:reactDir}));
    }}]});
  const css=fs.readFileSync(path.join(workspace,'src/styles.css'),'utf8').replace(/@import[^;]*;/g,'');
  fs.writeFileSync(path.join(output,'styles.css'),css);
  fs.writeFileSync(path.join(output,'index.html'),'<!doctype html><html><head><link rel="stylesheet" href="styles.css"></head><body><div id="root"></div><script src="app.js"></script></body></html>');
})().catch(()=>{console.error('Gallery harness compilation failed');process.exit(125);});
