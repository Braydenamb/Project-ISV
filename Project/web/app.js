"use strict";
const $ = id => document.getElementById(id);
const canvas = $("viewer"), ctx = canvas.getContext("2d");
let photos = [], active = 0, view = "overlay", revision = 0, timer, drag = null;
const states = new Map();
const current = () => states.get(active);
function status(message, kind = "") { $("status").textContent = message; $("status").className = kind; }
async function api(path, body) {
  const response = await fetch(path, body ? {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function payload() { return {id:active, ...current().params}; }
function library() {
  $("photos").replaceChildren();
  for (const photo of photos) {
    const button = document.createElement("button"); button.className = "photo" + (photo.id === active ? " selected" : "");
    const img = document.createElement("img"); img.src = `/api/image?id=${photo.id}`; img.alt = ""; img.loading = "lazy";
    const text = document.createElement("span"), name = document.createElement("span"), label = document.createElement("span");
    name.className = "name"; name.textContent = photo.name; label.className = "state";
    const state = states.get(photo.id); label.textContent = state?.saved ? "Saved" : state ? "Not saved / changed" : "Not analyzed";
    text.append(name,label); button.append(img,text); button.onclick = () => select(photo.id); $("photos").append(button);
  }
}
function syncControls() {
  const p = current().params;
  $("threshold").value = $("thresholdNumber").value = p.threshold;
  $("minimum").value = p.min_area; $("blur").value = p.blur; $("invert").checked = p.invert;
  $("filename").textContent = photos[active].name; $("position").textContent = `${active+1} / ${photos.length}`;
  $("saveState").textContent = current().saved ? "Saved" : "Not saved / changed";
  $("roiLabel").textContent = p.roi ? `ROI: ${p.roi.join(", ")} (original pixels)` : "ROI: full image";
}
function invalidate() {
  revision++; current().saved = false; current().result = null;
  $("save").disabled = true; ["count","border","mean"].forEach(id => $(id).textContent = "—");
  $("results").replaceChildren(); $("histogram").replaceChildren(); $("rowCount").textContent = "Updating";
  $("imageHint").textContent = "Updating analysis…"; syncControls(); library();
  status("Settings changed · waiting to analyze…", "busy");
}
function changed() { invalidate(); clearTimeout(timer); timer = setTimeout(analyze, 220); }
async function select(id) {
  clearTimeout(timer); revision++; active = id;
  status("Loading photo…", "busy");
  if (!states.has(id)) states.set(id,{params:{threshold:photos[id].threshold,min_area:photos[id].min_area,blur:5,invert:false,roi:null},saved:false,result:null});
  syncControls(); library(); ctx.clearRect(0,0,canvas.width,canvas.height);
  const state = current();
  if (state.result) { render(state.result); status("Restored this photo’s session settings and analysis."); return; }
  await analyze();
}
async function analyze() {
  const token = ++revision, id = active;
  $("save").disabled = true; status("Processing original-resolution image…", "busy");
  try {
    const data = await api("/api/analyze",payload());
    if (token !== revision || id !== active) return;
    current().result = data; render(data); status("Analysis ready · Inspect the mask before accepting the detected count.");
  } catch(error) { if (token === revision) status(error.message,"error"); }
}
function imageDraw() {
  const data = current()?.result; if (!data) return;
  canvas.dataset.ready = "false";
  const id = active, token = revision, image = new Image();
  image.onload = () => {
    if (id !== active || token !== revision) return;
    canvas.width = image.width; canvas.height = image.height; ctx.drawImage(image,0,0);
    canvas.dataset.ready = "true";
    if (view === "original" && current().params.roi) {
      const [x,y,w,h] = current().params.roi, sx=canvas.width/data.width, sy=canvas.height/data.height;
      ctx.strokeStyle="#42e2b1"; ctx.lineWidth=2; ctx.strokeRect(x*sx,y*sy,w*sx,h*sy);
    }
  };
  image.src = view === "original" ? `/api/image?id=${active}` : data.images[view];
}
function histogram(data) {
  const svg = $("histogram"); svg.replaceChildren();
  const add = (tag, attrs, text) => { const el=document.createElementNS("http://www.w3.org/2000/svg",tag); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); if(text!==undefined)el.textContent=text; svg.append(el); };
  const {counts,edges} = data.histogram;
  if (!counts.length) { add("text",{x:200,y:100,fill:"#839087"},"No accepted particles"); return; }
  const max=Math.max(...counts,1), left=40, width=540, top=15, height=165;
  for(let tick=0;tick<=4;tick++) { const y=top+height-tick*height/4;
    add("line",{x1:left,y1:y,x2:580,y2:y,stroke:"#e8eeea"});
    add("text",{x:30,y:y+4,"text-anchor":"end",fill:"#839087","font-size":10},(max*tick/4).toFixed(1)); }
  counts.forEach((n,i)=>add("rect",{x:left+i*width/counts.length+2,y:top+height-n/max*height,width:width/counts.length-4,height:n/max*height,rx:3,fill:"#18876d"}));
  [0,Math.floor((edges.length-1)/2),edges.length-1].forEach(i=>add("text",{x:left+i/(edges.length-1)*width,y:205,"text-anchor":"middle",fill:"#839087","font-size":10},Math.round(edges[i]).toLocaleString()));
}
function render(data) {
  $("count").textContent=data.particles.length; $("border").textContent=data.border_excluded;
  const mean=data.particles.reduce((sum,p)=>sum+p.area_px2,0)/data.particles.length;
  $("mean").textContent=Number.isFinite(mean)?mean.toLocaleString(undefined,{maximumFractionDigits:1}):"—";
  $("results").replaceChildren();
  for(const p of data.particles) { const row=document.createElement("tr");
    [p.id,p.area_px2,p.cx_px,p.cy_px].forEach(v=>{const td=document.createElement("td");td.textContent=v.toLocaleString(undefined,{maximumFractionDigits:1});row.append(td);}); $("results").append(row); }
  $("rowCount").textContent=`${data.particles.length} objects`; $("save").disabled=false;
  $("imageHint").textContent=`${data.width} × ${data.height} px · Drag to select ROI`;
  syncControls(); histogram(data); imageDraw();
}
async function save() {
  if (!current()?.result || $("save").disabled) return;
  const id=active, snapshot=JSON.stringify(current().params), token=revision;
  $("save").disabled=true; status("Saving per-photo measurements and images…","busy");
  try { const response=await api("/api/save",payload());
    if(JSON.stringify(states.get(id).params)===snapshot)states.get(id).saved=true;
    if(id===active && token===revision) {syncControls();status(`Saved to ${response.output}`);} library();
  } catch(error) {status(error.message,"error");}
  finally { if(id===active && token===revision)$("save").disabled=!current().result; }
}
$("threshold").oninput = event => {current().params.threshold=Number(event.target.value); changed();};
$("thresholdNumber").onchange = event => {const n=Number(event.target.value); if(Number.isInteger(n)&&n>=0&&n<=255){current().params.threshold=n;changed();}else syncControls();};
$("minimum").onchange=event=>{const n=Number(event.target.value);if(Number.isFinite(n)&&n>=0){current().params.min_area=n;changed();}else syncControls();};
$("blur").onchange=event=>{current().params.blur=Number(event.target.value);changed();};
$("invert").onchange=event=>{current().params.invert=event.target.checked;changed();};
$("reset").onclick=()=>{current().params.roi=null;changed();};
$("save").onclick=save;
$("previous").onclick=()=>select((active-1+photos.length)%photos.length);
$("next").onclick=()=>select((active+1)%photos.length);
$("auto").onclick=async()=>{const id=active,token=revision;status("Finding starting threshold…","busy");try{const result=await api("/api/auto",payload());if(id===active&&token===revision){current().params.threshold=result.threshold;changed();}}catch(error){status(error.message,"error");}};
document.querySelectorAll("[data-view]").forEach(button=>button.onclick=()=>{view=button.dataset.view;document.querySelectorAll("[data-view]").forEach(b=>b.classList.toggle("active",b===button));imageDraw();});
function coordinate(event) {const r=canvas.getBoundingClientRect(), d=current().result;return [Math.max(0,Math.min(d.width,Math.round((event.clientX-r.left)/r.width*d.width))),Math.max(0,Math.min(d.height,Math.round((event.clientY-r.top)/r.height*d.height)))];}
canvas.onpointerdown=event=>{if(!current()?.result||canvas.dataset.ready!=="true")return;drag={start:coordinate(event),id:active};canvas.setPointerCapture(event.pointerId);event.preventDefault();};
canvas.onpointermove=event=>{if(!drag||!current()?.result||drag.id!==active)return;const end=coordinate(event),d=current().result;
  if(!drag.background)drag.background=ctx.getImageData(0,0,canvas.width,canvas.height);
  ctx.putImageData(drag.background,0,0);const sx=canvas.width/d.width,sy=canvas.height/d.height;
  ctx.strokeStyle="#42e2b1";ctx.lineWidth=3;ctx.strokeRect(drag.start[0]*sx,drag.start[1]*sy,(end[0]-drag.start[0])*sx,(end[1]-drag.start[1])*sy);};
canvas.onpointerup=event=>{if(!drag||!current()?.result||drag.id!==active){drag=null;return;}const end=coordinate(event),start=drag.start;drag=null;const x=Math.min(start[0],end[0]),y=Math.min(start[1],end[1]),w=Math.abs(end[0]-start[0]),h=Math.abs(end[1]-start[1]);if(w>2&&h>2){current().params.roi=[x,y,w,h];changed();}};
canvas.onpointercancel=()=>{drag=null;};
document.addEventListener("keydown",event=>{if(!photos.length||/INPUT|SELECT|TEXTAREA/.test(event.target.tagName)||event.ctrlKey||event.metaKey)return;
  if(["+","=","-"].includes(event.key)){event.preventDefault();current().params.threshold=Math.max(0,Math.min(255,current().params.threshold+(event.key==="-"?-5:5)));changed();}
  else if(event.key==="ArrowRight"){event.preventDefault();$("next").click();}else if(event.key==="ArrowLeft"){event.preventDefault();$("previous").click();}else if(event.key.toLowerCase()==="s"){event.preventDefault();save();}});
api("/api/photos").then(data=>{photos=data.photos;$("photoCount").textContent=photos.length;if(photos.length)select(0);else{status("No photos found in the configured folder.");document.querySelectorAll("button,input,select").forEach(el=>el.disabled=true);}}).catch(error=>status(error.message,"error"));