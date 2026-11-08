"use strict";
function validate(d){if(!d||!Array.isArray(d.players)||!Array.isArray(d.stints))throw Error('Expected players and stints arrays.');const ids=new Set();for(const p of d.players){if(typeof p.id!=='string'||!p.id||typeof p.name!=='string'||!p.name.trim()||ids.has(p.id))throw Error('Invalid or duplicate player ID/name.');ids.add(p.id)}const date=s=>typeof s==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s)&&!isNaN(Date.parse(s))&&new Date(s+'T00:00:00Z').toISOString().slice(0,10)===s;for(const s of d.stints){if(!ids.has(s.playerId)||!s.clubId||!s.clubName||!s.source||!date(s.start)||!date(s.end)||s.start>s.end)throw Error('Invalid stint: player, club, source, or dates.')}if(d.players.length<2)throw Error('Need at least two players.');return d}

self.onmessage=async({data:request})=>{
 try{
  let d=request.data;
  if(request.url){const response=await fetch(request.url);if(!response.ok)throw Error('HTTP '+response.status);d=await response.json()}
  validate(d);
  const graph=new Map(d.players.map(p=>[p.id,new Map()])),clubs=new Map();
  for(const s of d.stints){if(!clubs.has(s.clubId))clubs.set(s.clubId,[]);clubs.get(s.clubId).push(s)}
  for(const stints of clubs.values()){
   stints.sort((a,b)=>a.start.localeCompare(b.start)||a.end.localeCompare(b.end));
   let active=[];
   for(const b of stints){
    active=active.filter(a=>a.end>=b.start);
    for(const a of active)if(a.playerId!==b.playerId&&!graph.get(a.playerId).has(b.playerId)){
     const evidence={club:a.clubName,date:b.start,source:a.source===b.source?a.source:a.source+' | '+b.source};
     graph.get(a.playerId).set(b.playerId,evidence);graph.get(b.playerId).set(a.playerId,evidence);
    }
    active.push(b);
   }
  }
  self.postMessage({players:d.players,stints:d.stints.length,edges:[...graph.values()].reduce((n,m)=>n+m.size,0)/2,graph:[...graph].map(([id,edges])=>[id,[...edges]])});
 }catch(error){self.postMessage({error:error.message})}
};
