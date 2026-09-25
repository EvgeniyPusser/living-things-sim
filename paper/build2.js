const {Document,Packer,Paragraph,TextRun,HeadingLevel,Table,TableRow,TableCell,WidthType,ShadingType}=require('docx');
const fs=require('fs');

const src=fs.readFileSync('paper_v2.md','utf8').split(/\r?\n/);

const P=(t,o={})=>new Paragraph({spacing:{after:140,line:300},...o,children:runs(t,o.run||{})});
const H1=(t)=>new Paragraph({text:t,heading:HeadingLevel.HEADING_1,spacing:{before:320,after:140}});
const H2=(t)=>new Paragraph({text:t,heading:HeadingLevel.HEADING_2,spacing:{before:240,after:120}});
const H3=(t)=>new Paragraph({text:t,heading:HeadingLevel.HEADING_3,spacing:{before:200,after:100}});
const B=(t)=>new Paragraph({spacing:{after:80},bullet:{level:0},children:runs(t,{})});
const MONO=(t)=>new Paragraph({spacing:{after:40},children:[new TextRun({text:t,font:"Consolas",size:18})]});
const REF=(t)=>new Paragraph({spacing:{after:100},indent:{left:360,hanging:360},children:runs(t,{size:20})});
const CAP=(t)=>new Paragraph({spacing:{before:60,after:200},children:[new TextRun({text:t,italics:true,size:18})]});

// **bold** inside a line
function runs(t,base){
  const out=[]; let rest=t;
  const re=/\*\*([^*]+)\*\*/;
  let m;
  while((m=re.exec(rest))){
    if(m.index>0) out.push(new TextRun({text:rest.slice(0,m.index),...base}));
    out.push(new TextRun({text:m[1],bold:true,...base}));
    rest=rest.slice(m.index+m[0].length);
  }
  if(rest) out.push(new TextRun({text:rest,...base}));
  return out.length?out:[new TextRun({text:"",...base})];
}

function mkTable(rows){
  const n=Math.max(...rows.map(r=>r.length));
  const total=9100;
  const first=Math.round(total*0.34);
  const other=Math.round((total-first)/(n-1));
  const w=[first,...Array(n-1).fill(other)];
  w[w.length-1]+= total - w.reduce((a,b)=>a+b,0);
  const cell=(t,b,ww)=>new TableCell({width:{size:ww,type:WidthType.DXA},
    shading:b?{type:ShadingType.CLEAR,fill:"EFEFEF"}:undefined,
    children:[new Paragraph({spacing:{before:40,after:40},children:[new TextRun({text:String(t),bold:b,size:18})]})]});
  return new Table({columnWidths:w,width:{size:total,type:WidthType.DXA},
    rows:rows.map((r,i)=>new TableRow({
      children:Array.from({length:n},(_,j)=>cell(r[j]===undefined?"":r[j],i===0,w[j])),
      tableHeader:i===0}))});
}

const kids=[];
let tbl=null, code=null, tnum=0, inRefs=false;
const splitRow=(l)=>l.replace(/^\||\|$/g,'').split('|').map(s=>s.trim());

for(let i=0;i<src.length;i++){
  const l=src[i];
  const t=l.trim();

  if(t.startsWith('```')){
    if(code){ code.forEach(x=>kids.push(MONO(x))); kids.push(new Paragraph({spacing:{after:140}})); code=null; }
    else code=[];
    continue;
  }
  if(code!==null){ code.push(l); continue; }

  // tables
  if(t.startsWith('|')){
    if(/^\|[\s:\-|]+\|$/.test(t)) continue;      // separator row
    (tbl=tbl||[]).push(splitRow(t));
    continue;
  }
  if(tbl){ kids.push(mkTable(tbl)); tnum++; if(/^Table \d+\./.test(t)){ kids.push(CAP(t)); tbl=null; continue; } kids.push(CAP("Table "+tnum+".")); tbl=null; }

  if(!t){ continue; }
  if(t.startsWith('# ')){ kids.push(new Paragraph({text:t.slice(2),heading:HeadingLevel.TITLE,spacing:{after:160}})); continue; }
  if(t.startsWith('## ')){ inRefs=/References/i.test(t); kids.push(H1(t.slice(3))); continue; }
  if(t.startsWith('### ')){ kids.push(H2(t.slice(4))); continue; }
  if(t.startsWith('#### ')){ kids.push(H3(t.slice(5))); continue; }
  if(t.startsWith('- ')){ kids.push(B(t.slice(2))); continue; }
  if(inRefs && /^\[\d+\]/.test(t)){ kids.push(REF(t)); continue; }
  kids.push(P(t));
}
if(tbl){ kids.push(mkTable(tbl)); tnum++; kids.push(CAP("Table "+tnum+".")); }

const doc=new Document({
  styles:{default:{document:{run:{font:"Calibri",size:22}}}},
  sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1440,bottom:1440,left:1440,right:1440}}},children:kids}]});

Packer.toBuffer(doc).then(b=>{fs.writeFileSync("What_is_worth_inheriting_v2.docx",b);console.log("ok, blocks:",kids.length,"tables:",tnum);});
