"""Собирает одностраничный калькулятор: HTML + встроенные метеоданные."""
import json, io, os

W = json.load(open('/home/claude/calc/weather_min.json', encoding='utf-8'))
DATA = json.dumps(W, ensure_ascii=False, separators=(',', ':'))

HTML = r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Тепловой стенд</title>
<style>
:root{
  --s1:#2a78d6; --s2:#eb6834; --ink:#0b0b0b; --ink2:#52514e; --muted:#8a8983;
  --surf:#fcfcfb; --panel:#ffffff; --grid:#e5e4df; --line:#d8d7d1;
  --good:#1b7f5a; --warn:#b06b00;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --s1:#6ea8f0; --s2:#f5905f; --ink:#f4f3f0; --ink2:#b9b7b1; --muted:#807e78;
    --surf:#141414; --panel:#1c1c1b; --grid:#2e2e2c; --line:#3a3a37;
    --good:#4cc191; --warn:#e0a33a;
  }
}
:root[data-theme="dark"]{
  --s1:#6ea8f0; --s2:#f5905f; --ink:#f4f3f0; --ink2:#b9b7b1; --muted:#807e78;
  --surf:#141414; --panel:#1c1c1b; --grid:#2e2e2c; --line:#3a3a37;
  --good:#4cc191; --warn:#e0a33a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--surf);color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:23px;font-weight:600;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--ink2);font-size:14px;margin:0 0 26px;max-width:70ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px 18px 16px;margin-bottom:18px}
.panel h2{font-size:12px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
  color:var(--muted);margin:0 0 14px}
.ctrls{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px 22px;align-items:end}
label{display:block;font-size:12px;color:var(--ink2);margin-bottom:6px}
label b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
select,input[type=range]{width:100%}
select{background:var(--panel);color:var(--ink);border:1px solid var(--line);
  border-radius:6px;padding:7px 9px;font-size:14px}
input[type=range]{accent-color:var(--s1);height:22px}
.btn{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);
  background:var(--panel);color:var(--ink);border-radius:7px;padding:9px 15px;
  font-size:14px;cursor:pointer;font-weight:500}
.btn:hover{border-color:var(--muted)}
.btn[aria-pressed=true]{background:var(--s2);border-color:var(--s2);color:#fff}
.legend{display:flex;gap:20px;flex-wrap:wrap;margin:0 0 10px;font-size:13px;color:var(--ink2)}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:22px;height:3px;border-radius:2px;display:inline-block}
.chartbox{position:relative}
svg{display:block;width:100%;height:auto;overflow:visible}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:2px;
  background:var(--line);border:1px solid var(--line);border-radius:9px;overflow:hidden}
.tile{background:var(--panel);padding:13px 15px}
.tile .k{font-size:11px;color:var(--muted);letter-spacing:.04em;text-transform:uppercase;margin-bottom:5px}
.tile .v{font-size:25px;font-weight:650;font-variant-numeric:tabular-nums;letter-spacing:-.02em;line-height:1.1}
.tile .u{font-size:12px;color:var(--ink2);margin-top:3px}
.tile.a .v{color:var(--s2)} .tile.b .v{color:var(--s1)}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{text-align:right;padding:7px 10px;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.05em;text-transform:uppercase}
.note{font-size:13px;color:var(--ink2);margin:12px 0 0;max-width:78ch}
.tip{position:absolute;pointer-events:none;background:var(--panel);border:1px solid var(--line);
  border-radius:7px;padding:8px 11px;font-size:12.5px;box-shadow:0 4px 16px rgba(0,0,0,.14);
  opacity:0;transition:opacity .09s;font-variant-numeric:tabular-nums;white-space:nowrap;z-index:5}
.tip b{font-weight:600}
.inside{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;font-size:13px;color:var(--ink2)}
.inside b{display:block;color:var(--ink);font-size:12px;letter-spacing:.05em;
  text-transform:uppercase;margin-bottom:6px;font-weight:600}
.inside ul{margin:0;padding-left:17px} .inside li{margin-bottom:4px}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
  background:var(--grid);padding:1px 5px;border-radius:4px}
.top{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap}
.theme{border:1px solid var(--line);background:var(--panel);color:var(--ink2);
  border-radius:6px;padding:5px 10px;font-size:12px;cursor:pointer}
@media (max-width:640px){ .wrap{padding:18px 16px 48px} h1{font-size:20px} .tile .v{font-size:22px} }
</style>
</head>
<body data-palette="#2a78d6,#eb6834">
<div class="wrap">

<div class="top">
  <div>
    <h1>Тепловой стенд: что даёт унаследованный опыт в аварии</h1>
    <p class="sub">Модель дома с тремя тепловыми ёмкостями считается здесь же, в браузере, на настоящих
    метеоданных шести городов. Сравниваются два дома-близнеца: один подобрал расписание сам за первую зиму,
    второй начал с расписания, собранного по сорока домам, каждый из которых пережил свою аварию.</p>
  </div>
  <button class="theme" id="theme">тёмный / светлый</button>
</div>

<div class="panel">
  <h2>Дом и погода</h2>
  <div class="ctrls">
    <div>
      <label for="city">Город</label>
      <select id="city"></select>
    </div>
    <div>
      <label for="uext">Стены, U — <b id="uextv"></b> Вт/м²К</label>
      <input type="range" id="uext" min="0.15" max="0.70" step="0.01" value="0.40">
    </div>
    <div>
      <label for="mass">Тепловая масса — <b id="massv"></b></label>
      <input type="range" id="mass" min="0.5" max="1.8" step="0.05" value="1.0">
    </div>
    <div>
      <label for="marg">Запас мощности — <b id="margv"></b></label>
      <input type="range" id="marg" min="0.85" max="1.35" step="0.01" value="1.05">
    </div>
    <div>
      <button class="btn" id="fail" aria-pressed="true">Авария: отопление вполсилы, 72 часа</button>
    </div>
  </div>
  <p class="note" id="wx"></p>
</div>

<div class="panel">
  <h2>Температура в доме во время самого холодного окна года</h2>
  <div class="legend">
    <span><i class="sw" style="background:var(--s2)"></i>дом подбирал сам</span>
    <span><i class="sw" style="background:var(--s1)"></i>дом начал с фонда</span>
    <span><i class="sw" style="background:var(--grid);height:2px;border-top:2px dashed var(--muted)"></i>норма 21 °C</span>
  </div>
  <div class="chartbox">
    <svg id="ch" viewBox="0 0 900 260" role="img" aria-label="Температура в доме за 72 часа аварии"></svg>
    <div class="tip" id="tip"></div>
  </div>
  <div style="font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:14px 0 4px">на улице, °C</div>
  <div class="chartbox">
    <svg id="cho" viewBox="0 0 900 120" role="img" aria-label="Наружная температура за те же 72 часа"></svg>
    <div class="tip" id="tipo"></div>
  </div>
</div>

<div class="tiles" style="margin-bottom:18px">
  <div class="tile a"><div class="k">сам · самая низкая</div><div class="v" id="tA"></div><div class="u">°C в комнате</div></div>
  <div class="tile a"><div class="k">сам · часов холоднее 19 °C</div><div class="v" id="hA"></div><div class="u">из 72</div></div>
  <div class="tile a"><div class="k">сам · электричество</div><div class="v" id="eA"></div><div class="u">кВт·ч за 72 ч</div></div>
  <div class="tile b"><div class="k">фонд · самая низкая</div><div class="v" id="tB"></div><div class="u">°C в комнате</div></div>
  <div class="tile b"><div class="k">фонд · часов холоднее 19 °C</div><div class="v" id="hB"></div><div class="u">из 72</div></div>
  <div class="tile b"><div class="k">фонд · электричество</div><div class="v" id="eB"></div><div class="u">кВт·ч за 72 ч</div></div>
</div>

<div class="panel">
  <h2>Население: 40 домов этого города, часов холоднее 19 °C за трое суток аварии</h2>
  <div class="legend">
    <span><i class="sw" style="background:var(--s2)"></i>сам</span>
    <span><i class="sw" style="background:var(--s1)"></i>с фондом</span>
  </div>
  <div class="chartbox">
    <svg id="pop" viewBox="0 0 900 220" role="img" aria-label="Часы холоднее 19 градусов по 40 домам"></svg>
    <div class="tip" id="tip2"></div>
  </div>
  <p class="note" id="popnote"></p>
</div>

<div class="panel">
  <h2>Два расписания, которые сравниваются</h2>
  <table>
    <thead><tr><th>Что задаёт</th><th>дом сам</th><th>фонд по 40 домам</th></tr></thead>
    <tbody id="sched"></tbody>
  </table>
  <p class="note">Левая колонка подобрана прямо сейчас, на этой странице: дом сделал 40 попыток
  на обычных днях до аварии. Правая — медиана расписаний сорока домов,
  каждый из которых прожил свою зиму со своей аварией. Они сошлись на том, что ночное снижение
  надо отменить, держать выше нормы и реагировать резче.</p>
</div>

<div class="panel">
  <h2>Что внутри</h2>
  <div class="inside">
    <div><b>Модель</b><ul>
      <li>три тепловые ёмкости: воздух с мебелью, оболочка, внутренние стены</li>
      <li>теплонасос: и КПД, и доступная мощность падают с морозом</li>
      <li>солнце по четырём фасадам от настоящего положения солнца</li>
      <li>шаг управления 15 минут, физика решается точно внутри шага</li>
    </ul></div>
    <div><b>Данные</b><ul>
      <li>метеофайлы шести городов, 75 суток зимы, часовой шаг</li>
      <li>прямая и рассеянная радиация отдельно</li>
      <li>мощность отопления выбирается по DIN 18599-2</li>
    </ul></div>
    <div><b>Проверка</b><ul>
      <li>та же модель сверена с BuilDa — открытым Modelica-генератором
      Fraunhofer, проверенным на двух настоящих домах в Хольцкирхене</li>
      <li>расхождение по расходу тепла 2 %, по средней температуре 0.2 К,
      на 12 домах в двух городах</li>
    </ul></div>
  </div>
</div>

</div>

<script>
const WX = __DATA__;

/* ---------- модель ---------- */
const HIN=2.7, RHOCP=1.2*1005, COMFORT=21.0, KENV=0.65, KWIN=1.08;
const SUB=4, DT=3600/SUB;

function capFactor(T){ return Math.min(1.15, Math.max(0.50, 1-0.0235*(7-T))); }

function makeHouse(uext, massK, marg){
  const L=8.5, W=8.0, NF=2, H=3.04*NF;
  const Awg=2*(L+W)*H, AwinF=Awg/4*0.14, Awin=AwinF*4, Aw=Awg-Awin;
  const Ar=L*W*1.636, Ag=L*W, Ai=1.238*Awg, V=L*W*H, Af=L*W*NF;
  const ser=(A,U)=>{ const hin=HIN*A, Rt=1/Math.max(U*A,1e-9), Ri=1/hin;
                     const Ro=Math.max(Rt-Ri, Rt*0.05); return [hin, 1/Ro]; };
  const [h1,u1]=ser(Aw,uext), [h2,u2]=ser(Ar,0.40), [h3,u3]=ser(Ag,0.51);
  const hEnv=h1+h2+h3, uaEnv=(u1+u2+u3)*KENV;
  const Cenv=(Aw*192000 + Ar*81240 + Ag*483840)*massK;
  const hInt=HIN*Ai, Cint=Ai*145154*massK;
  const uaWin=(Awin*2.0 + V*0.35*RHOCP/3600)*KWIN;
  const Cair=V*RHOCP + Af*2230;
  const uaDin=Aw*uext + Awin*2.0 + Ag*0.51*0.6 + Ar*0.40 + V*0.35*RHOCP/3600;
  return {hEnv,uaEnv,Cenv,hInt,Cint,uaWin,Cair,uaDin,AwinF,marg,steep:0.8,eta:0.45};
}

function sizePower(h, Tdes){ return h.uaDin*(21-Tdes)/capFactor(Tdes)*h.marg; }

/* точный переход за шаг: матричная экспонента 3x3 через масштабирование и возведение */
function expm3(A, dt){
  // A*dt, затем exp через ряд с масштабированием
  let m=[[A[0][0]*dt,A[0][1]*dt,A[0][2]*dt],
         [A[1][0]*dt,A[1][1]*dt,A[1][2]*dt],
         [A[2][0]*dt,A[2][1]*dt,A[2][2]*dt]];
  let nrm=0; for(let i=0;i<3;i++){let s=0;for(let j=0;j<3;j++)s+=Math.abs(m[i][j]); nrm=Math.max(nrm,s);}
  let k=Math.max(0, Math.ceil(Math.log2(nrm/0.25))||0);
  const sc=Math.pow(2,-k);
  for(let i=0;i<3;i++)for(let j=0;j<3;j++)m[i][j]*=sc;
  let R=[[1,0,0],[0,1,0],[0,0,1]], term=[[1,0,0],[0,1,0],[0,0,1]];
  for(let n=1;n<=12;n++){
    const t2=[[0,0,0],[0,0,0],[0,0,0]];
    for(let i=0;i<3;i++)for(let j=0;j<3;j++){let s=0;for(let q=0;q<3;q++)s+=term[i][q]*m[q][j]; t2[i][j]=s/n;}
    term=t2; for(let i=0;i<3;i++)for(let j=0;j<3;j++)R[i][j]+=term[i][j];
  }
  for(let s=0;s<k;s++){
    const t2=[[0,0,0],[0,0,0],[0,0,0]];
    for(let i=0;i<3;i++)for(let j=0;j<3;j++){let v=0;for(let q=0;q<3;q++)v+=R[i][q]*R[q][j]; t2[i][j]=v;}
    R=t2;
  }
  return R;
}

function discretise(h, dt){
  const Ca=h.Cair, Ce=h.Cenv, Ci=h.Cint;
  const A=[[-(h.hEnv+h.hInt+h.uaWin)/Ca, h.hEnv/Ca, h.hInt/Ca],
           [ h.hEnv/Ce, -(h.hEnv+h.uaEnv)/Ce, 0],
           [ h.hInt/Ci, 0, -h.hInt/Ci]];
  const Ad=expm3(A,dt);
  // Bd = A^{-1}(Ad - I) B, считаем численно через ряд: Bd ≈ dt*(I + Adt/2 + ...)*B
  let m=[[A[0][0]*dt,A[0][1]*dt,A[0][2]*dt],[A[1][0]*dt,A[1][1]*dt,A[1][2]*dt],[A[2][0]*dt,A[2][1]*dt,A[2][2]*dt]];
  let S=[[dt,0,0],[0,dt,0],[0,0,dt]], term=[[dt,0,0],[0,dt,0],[0,0,dt]];
  for(let n=1;n<=14;n++){
    const t2=[[0,0,0],[0,0,0],[0,0,0]];
    for(let i=0;i<3;i++)for(let j=0;j<3;j++){let s=0;for(let q=0;q<3;q++)s+=term[i][q]*m[q][j]; t2[i][j]=s/(n+1);}
    term=t2; for(let i=0;i<3;i++)for(let j=0;j<3;j++)S[i][j]+=term[i][j];
  }
  const Bd=[[S[0][0]/Ca,S[0][1]/Ce,S[0][2]/Ci],
            [S[1][0]/Ca,S[1][1]/Ce,S[1][2]/Ci],
            [S[2][0]/Ca,S[2][1]/Ci===0?0:S[2][1]/Ce,S[2][2]/Ci]];
  Bd[2][1]=S[2][1]/Ce;
  return [Ad,Bd];
}

function solarVert(lat, n, hr, dir, dif){
  const d=23.45*Math.PI/180*Math.sin(2*Math.PI*(284+n)/365);
  const om=15*(hr-12)*Math.PI/180, la=lat*Math.PI/180;
  const sa=Math.sin(la)*Math.sin(d)+Math.cos(la)*Math.cos(d)*Math.cos(om);
  const alt=Math.asin(Math.max(-1,Math.min(1,sa)));
  const az=Math.atan2(Math.sin(om), Math.cos(om)*Math.sin(la)-Math.tan(d)*Math.cos(la));
  if(alt<=0) return dif*0.5*4;
  let s=0;
  for(const g of [0, Math.PI/2, Math.PI, -Math.PI/2]){
    const ci=Math.max(0, Math.cos(alt)*Math.cos(az-g));
    s += dir*ci + dif*0.5;
  }
  return s;
}

/* расписания: 5 чисел */
const DEFAULT = {Tocc:21.0, Taway:18.0, lead:1.0, band:0.50, gain:0.35};
const FUND    = {Tocc:23.4, Taway:21.0, lead:0.97, band:0.34, gain:0.68};
const LO={Tocc:18,Taway:12,lead:0,band:0.10,gain:0.02};
const HI={Tocc:24,Taway:21,lead:5,band:2.00,gain:1.00};
const KEYS=['Tocc','Taway','lead','band','gain'];

/* дом подбирает расписание сам, на ОБЫЧНЫХ днях до аварии.
   Ровно как в опыте: подстраиваться на самой аварии нельзя. */
function tune(h, wx, start, budget, seedv){
  const a=Math.max(0,start-720), len=720;
  let seed=seedv|0||7; const rnd=()=>{seed=(seed*1103515245+12345)&0x7fffffff; return seed/0x7fffffff;};
  const gauss=()=>{let u=0,v=0;while(!u)u=rnd();while(!v)v=rnd();
                   return Math.sqrt(-2*Math.log(u))*Math.cos(2*Math.PI*v);};
  let best={...DEFAULT};
  const score=s=>{ const r=run(h,wx,s,a,len,false); return r.kwh*0.25 + r.dh*2.0; };
  let bc=score(best), step=0.25;
  for(let k=0;k<budget;k++){
    const cand={};
    for(const key of KEYS){
      const span=HI[key]-LO[key];
      cand[key]=Math.min(HI[key],Math.max(LO[key], best[key]+gauss()*step*span));
    }
    const c=score(cand);
    if(c<bc){ best=cand; bc=c; } else { step=Math.max(step*0.97,0.02); }
  }
  return best;
}

function run(h, wx, sch, from, len, failScale){
  const [Ad,Bd]=discretise(h, DT);
  const Tdes = pct(wx.T, 0.4);
  const Qnom = sizePower(h, Tdes);
  let T=[COMFORT+0.3, COMFORT-1.5, COMFORT-0.3];
  const warm = Math.max(0, from-240);           // разогрев массы перед окном
  const trace=[], out=[];
  let hrsCold=0, hrsBad=0, kwh=0, tmin=99, dh=0;
  for(let k=warm; k<from+len; k++){
    const To=wx.T[k];
    const day=Math.floor(k/24)+1, hr=k%24;
    const Qs=h.AwinF*0.7*0.9*solarVert(wx.lat, day, hr, wx.dir[k], wx.dif[k]);
    const occ = (hr>=7 && hr<17) ? 1 : 0;
    const occNext = ((hr+Math.round(sch.lead))%24>=7 && (hr+Math.round(sch.lead))%24<17)?1:0;
    const target = (occ||occNext) ? sch.Tocc : sch.Taway;
    const Tsup=Math.min(55,Math.max(25, 20+h.steep*(20-To)));
    const cop=Math.min(5.5,Math.max(1.3, h.eta*(Tsup+273.15)/Math.max(Tsup-To,8)));
    let scale=1;
    if(failScale && k>=from && k<from+len) scale=0.5;
    const qcap=Qnom*scale*capFactor(To);
    let eh=0;
    for(let s=0;s<SUB;s++){
      const u=Math.min(1,Math.max(0, sch.gain*(target-T[0])/Math.max(sch.band,1e-6)));
      const Qh=u*qcap;
      const w=[Qh + 320*occ + 0.3*Qs + h.uaWin*To, h.uaEnv*To, 0.7*Qs];
      const nT=[0,0,0];
      for(let i=0;i<3;i++) nT[i]=Ad[i][0]*T[0]+Ad[i][1]*T[1]+Ad[i][2]*T[2]
                                +Bd[i][0]*w[0]+Bd[i][1]*w[1]+Bd[i][2]*w[2];
      T=nT; eh += Qh/cop*DT/3.6e6;
    }
    if(k>=from){
      trace.push(T[0]); out.push(To);
      kwh+=eh;
      const cold=Math.max(0, COMFORT-T[0]);
      if(cold>0.001) hrsCold++;
      if(T[0]<19.0) hrsBad++;
      dh+=cold;
      if(T[0]<tmin) tmin=T[0];
    }
  }
  return {trace,out,hrsCold,hrsBad,kwh,tmin,dh};
}

function pct(arr,p){ const a=[...arr].sort((x,y)=>x-y); return a[Math.floor(a.length*p/100)]; }
function coldestWindow(T,len){
  let best=0,bs=Infinity,s=0;
  for(let i=0;i<len;i++) s+=T[i];
  bs=s;
  for(let i=len;i<T.length;i++){ s+=T[i]-T[i-len]; if(s<bs){bs=s;best=i-len+1;} }
  return best;
}

/* ---------- отрисовка ---------- */
const P={l:46,r:16,t:14,b:30};
function line(svg, data, series, yLab, tipEl, fmt, showNorm){
  const VB=svg.viewBox.baseVal, Wd=VB.width, Ht=VB.height;
  const n=data.length;
  let lo=Infinity,hi=-Infinity;
  for(const s of series) for(const v of s.v){ if(v<lo)lo=v; if(v>hi)hi=v; }
  lo=Math.floor(lo-1); hi=Math.ceil(hi+1);
  const X=i=>P.l+(Wd-P.l-P.r)*i/(n-1), Y=v=>P.t+(Ht-P.t-P.b)*(1-(v-lo)/(hi-lo));
  const g=[];
  const step=Math.max(1,Math.ceil((hi-lo)/5));
  for(let v=Math.ceil(lo/step)*step; v<=hi; v+=step){
    g.push(`<line x1="${P.l}" x2="${Wd-P.r}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--grid)" stroke-width="1"/>`);
    g.push(`<text x="${P.l-8}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--ink2)">${v}</text>`);
  }
  if(showNorm){
    g.push(`<line x1="${P.l}" x2="${Wd-P.r}" y1="${Y(COMFORT).toFixed(1)}" y2="${Y(COMFORT).toFixed(1)}" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 4"/>`);
    g.push(`<text x="${Wd-P.r}" y="${(Y(COMFORT)-7).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--muted)">норма 21 °C</text>`);
  }
  for(let d=0;d<=3;d++){
    const i=Math.min(n-1, Math.round(d*24));
    g.push(`<text x="${X(i).toFixed(1)}" y="${Ht-8}" text-anchor="middle" font-size="11" fill="var(--ink2)">${d===0?'начало':d+' сут'}</text>`);
  }
  for(const s of series){
    let p='';
    s.v.forEach((v,i)=>{ p += (i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)+' '; });
    g.push(`<path d="${p}" fill="none" stroke="${s.c}" stroke-width="${s.w||2}" stroke-linejoin="round" stroke-linecap="round" ${s.dash?`stroke-dasharray="${s.dash}"`:''}/>`);
  }
  g.push(`<rect id="hit" x="${P.l}" y="${P.t}" width="${Wd-P.l-P.r}" height="${Ht-P.t-P.b}" fill="transparent"/>`);
  g.push(`<line id="cross" x1="0" x2="0" y1="${P.t}" y2="${Ht-P.b}" stroke="var(--muted)" stroke-width="1" opacity="0"/>`);
  svg.innerHTML=g.join('');
  const hit=svg.querySelector('#hit'), cross=svg.querySelector('#cross');
  const move=e=>{
    const r=svg.getBoundingClientRect();
    const px=(e.clientX-r.left)/r.width*Wd;
    let i=Math.round((px-P.l)/(Wd-P.l-P.r)*(n-1));
    i=Math.max(0,Math.min(n-1,i));
    cross.setAttribute('x1',X(i)); cross.setAttribute('x2',X(i)); cross.setAttribute('opacity','1');
    tipEl.innerHTML = `<b>час ${i}</b><br>` + series.map(s=>
      `<span style="color:${s.c}">■</span> ${s.n}: <b>${fmt(s.v[i])}</b>`).join('<br>');
    tipEl.style.opacity=1;
    const box=svg.parentElement.getBoundingClientRect();
    let lx=e.clientX-box.left+14;
    if(lx+170>box.width) lx=e.clientX-box.left-180;
    tipEl.style.left=lx+'px'; tipEl.style.top=(e.clientY-box.top-10)+'px';
  };
  hit.addEventListener('mousemove',move);
  hit.addEventListener('mouseleave',()=>{tipEl.style.opacity=0;cross.setAttribute('opacity','0');});
}

function bars(svg, rows, tipEl){
  const VB=svg.viewBox.baseVal, Wd=VB.width, Ht=VB.height;
  const n=rows.length, hi=Math.max(...rows.map(r=>Math.max(r.a,r.b)),1);
  const bw=(Wd-P.l-P.r)/n;
  const Y=v=>P.t+(Ht-P.t-P.b)*(1-v/hi);
  const g=[];
  const step=Math.max(6,Math.ceil(hi/5/6)*6);
  for(let v=0;v<=hi;v+=step){
    g.push(`<line x1="${P.l}" x2="${Wd-P.r}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="var(--grid)"/>`);
    g.push(`<text x="${P.l-8}" y="${(Y(v)+4).toFixed(1)}" text-anchor="end" font-size="11" fill="var(--ink2)">${v}</text>`);
  }
  rows.forEach((r,i)=>{
    const x=P.l+i*bw;
    const ha=Y(r.a), hb=Y(r.b);
    g.push(`<rect x="${(x+1).toFixed(1)}" y="${ha.toFixed(1)}" width="${(bw/2-1.5).toFixed(1)}" height="${(Y(0)-ha).toFixed(1)}" fill="var(--s2)" rx="2"/>`);
    g.push(`<rect x="${(x+bw/2+0.5).toFixed(1)}" y="${hb.toFixed(1)}" width="${(bw/2-1.5).toFixed(1)}" height="${(Y(0)-hb).toFixed(1)}" fill="var(--s1)" rx="2"/>`);
    g.push(`<rect class="bh" data-i="${i}" x="${x.toFixed(1)}" y="${P.t}" width="${bw.toFixed(1)}" height="${(Ht-P.t-P.b)}" fill="transparent"/>`);
  });
  g.push(`<text x="${P.l}" y="${Ht-8}" font-size="11" fill="var(--ink2)">хуже всех</text>`);
  g.push(`<text x="${Wd-P.r}" y="${Ht-8}" text-anchor="end" font-size="11" fill="var(--ink2)">лучше всех</text>`);
  svg.innerHTML=g.join('');
  svg.querySelectorAll('.bh').forEach(el=>{
    el.addEventListener('mousemove',e=>{
      const r=rows[+el.dataset.i];
      tipEl.innerHTML=`<b>дом ${(+el.dataset.i)+1}</b><br>`+
        `<span style="color:var(--s2)">■</span> сам: <b>${r.a.toFixed(0)} ч</b><br>`+
        `<span style="color:var(--s1)">■</span> фонд: <b>${r.b.toFixed(0)} ч</b>`;
      tipEl.style.opacity=1;
      const box=svg.parentElement.getBoundingClientRect();
      let lx=e.clientX-box.left+14; if(lx+150>box.width) lx=e.clientX-box.left-160;
      tipEl.style.left=lx+'px'; tipEl.style.top=(e.clientY-box.top-10)+'px';
    });
    el.addEventListener('mouseleave',()=>tipEl.style.opacity=0);
  });
}

/* ---------- сборка ---------- */
const $=id=>document.getElementById(id);
const sel=$('city');
Object.keys(WX).forEach(c=>{ const o=document.createElement('option'); o.value=c; o.textContent=c; sel.appendChild(o); });
sel.value='Мюнхен';

for(const k in WX){
  WX[k].T=WX[k].T.split(',').map(Number);
  WX[k].dir=WX[k].dir.split(',').map(Number);
  WX[k].dif=WX[k].dif.split(',').map(Number);
}

let failOn=true;
$('fail').addEventListener('click',()=>{ failOn=!failOn; $('fail').setAttribute('aria-pressed',failOn); draw(); });
['uext','mass','marg'].forEach(id=>$(id).addEventListener('input',draw));
sel.addEventListener('change',draw);
$('theme').addEventListener('click',()=>{
  const cur=document.documentElement.getAttribute('data-theme');
  const dark=cur? cur==='dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', dark?'light':'dark');
  draw();
});

function draw(){
  const city=sel.value, wx=WX[city];
  const uext=+$('uext').value, massK=+$('mass').value, marg=+$('marg').value;
  $('uextv').textContent=uext.toFixed(2);
  $('massv').textContent=massK.toFixed(2)+'×';
  $('margv').textContent=(marg*100).toFixed(0)+' %';

  const from=coldestWindow(wx.T,72);
  const wmean=wx.T.slice(from,from+72).reduce((a,b)=>a+b,0)/72;
  const wmin=Math.min(...wx.T.slice(from,from+72));
  $('wx').textContent=`${city}: самое холодное 72-часовое окно начинается на ${Math.floor(from/24)+1}-е сутки января; `+
    `средняя наружная в нём ${wmean.toFixed(1)} °C, минимум ${wmin.toFixed(1)} °C. `+
    `Окно ищется по метеофайлу, а не задаётся.`;

  const h=makeHouse(uext,massK,marg);
  const SELF=tune(h,wx,from,40,11);
  const A=run(h,wx,SELF,from,72,failOn);
  const B=run(h,wx,FUND,from,72,failOn);

  $('hA').textContent=A.hrsBad; $('hB').textContent=B.hrsBad;
  $('tA').textContent=A.tmin.toFixed(1); $('tB').textContent=B.tmin.toFixed(1);
  $('eA').textContent=A.kwh.toFixed(0); $('eB').textContent=B.kwh.toFixed(0);

  line($('ch'), A.trace, [
    {n:'сам', v:A.trace, c:'var(--s2)'},
    {n:'фонд', v:B.trace, c:'var(--s1)'}
  ], '°C', $('tip'), v=>v.toFixed(1)+' °C', true);
  line($('cho'), A.out, [
    {n:'улица', v:A.out, c:'var(--muted)', w:1.8}
  ], '°C', $('tipo'), v=>v.toFixed(1)+' °C', false);

  // население: 60 домов, разброс параметров
  let seed=42; const rnd=()=>{seed=(seed*1103515245+12345)&0x7fffffff; return seed/0x7fffffff;};
  const rows=[];
  for(let i=0;i<40;i++){
    const hh=makeHouse(0.15+rnd()*0.55, 0.55+rnd()*1.2, 0.88+rnd()*0.45);
    const own=tune(hh,wx,from,14,101+i*7);
    const a=run(hh,wx,own,from,72,failOn), b=run(hh,wx,FUND,from,72,failOn);
    rows.push({a:a.hrsBad,b:b.hrsBad});
  }
  rows.sort((x,y)=>y.a-x.a);
  bars($('pop'), rows, $('tip2'));
  const better=rows.filter(r=>r.b<r.a).length;
  const mA=rows.reduce((s,r)=>s+r.a,0)/rows.length, mB=rows.reduce((s,r)=>s+r.b,0)/rows.length;
  $('popnote').textContent=`Фонд лучше у ${better} домов из 40. В среднем ${mA.toFixed(1)} часа холода против ${mB.toFixed(1)}. `+
    `Каждый дом здесь считается заново, с этой погодой и своими стенами.`;

  const rowsS=[['держать днём, °C',SELF.Tocc,FUND.Tocc],
               ['ночью снижать до, °C',SELF.Taway,FUND.Taway],
               ['греть заранее, ч',SELF.lead,FUND.lead],
               ['зона нечувствительности, °C',SELF.band,FUND.band],
               ['коэффициент регулятора',SELF.gain,FUND.gain]];
  $('sched').innerHTML=rowsS.map(r=>`<tr><td>${r[0]}</td><td>${r[1].toFixed(2)}</td><td>${r[2].toFixed(2)}</td></tr>`).join('');
}
draw();
addEventListener('resize',()=>draw());
</script>
</body>
</html>
'''

HTML = HTML.replace('__DATA__', DATA)
open('/home/claude/calc/stend.html', 'w', encoding='utf-8').write(HTML)
print('готово,', round(os.path.getsize('/home/claude/calc/stend.html')/1024), 'КБ')
