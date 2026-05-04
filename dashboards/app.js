let DATA = null;
const PREF_LABELS = {
  '東京都':'東京','神奈川県':'神奈川','埼玉県':'埼玉','千葉県':'千葉',
  '茨城県':'茨城','栃木県':'栃木','群馬県':'群馬','兵庫県':'兵庫','京都府':'京都'
};
const GENDER_LABELS = {coed:'共学',boys:'男子',girls:'女子'};
const RELIGION_LABELS = {
  catholic:'カトリック',protestant:'プロテスタント',anglican:'聖公会',
  buddhist:'仏教系',shinto:'神道系',non_religious:'無宗教',other:'その他',unknown:'不明'
};
const SUBFIELD_LABELS = {
  learning_science:'学習科学',motivation_dev:'動機・発達',noncognitive:'非認知能力',
  sel:'SEL',adolescent_dev:'思春期発達',career_dev:'キャリア発達',
  wellbeing:'ウェルビーイング',evidence_based:'エビデンス',comparative:'比較教育',
  japanese_pedagogy:'日本教育学',curriculum:'カリキュラム',assessment:'評価',
  inclusion:'インクルーシブ',sociology_of_ed:'教育社会学'
};
const COLORS = ['#CC1400','#E63D2C','#FF7A4D','#FFA070','#FFC499','#1E5A7A','#3D7FA0','#5FA0BD','#88BFD4','#B0D8E5','#444','#777'];

async function init(){
  DATA = await (await fetch('data.json')).json();
  renderStats();
  renderPrefChart();
  renderGenderChart();
  renderSubfieldChart();
  renderSchoolFilters();
  renderSchools();
  renderTopConcepts();
  renderOutcomes();
  renderTestimonials();
  bindFilters();
}

function renderStats(){
  const m = DATA.meta;
  const items = [
    {num:m.total_schools,label:'学校レコード'},
    {num:m.total_concepts,label:'教育学概念'},
    {num:m.total_outcome_dims,label:'成果次元'},
    {num:m.total_testimonials,label:'関係者発言'},
    {num:m.total_relations,label:'概念関係'},
    {num:m.total_sources,label:'一次出典'},
  ];
  document.getElementById('stats').innerHTML = items.map(i=>
    `<div class="stat"><div class="num">${i.num}</div><div class="label">${i.label}</div></div>`
  ).join('');
}

function renderPrefChart(){
  const counts = DATA.pref_counts;
  new Chart(document.getElementById('prefChart'),{
    type:'bar',
    data:{
      labels:counts.map(p=>PREF_LABELS[p.location_pref]||p.location_pref),
      datasets:[{label:'校数',data:counts.map(p=>p.count),backgroundColor:'#CC1400'}]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}}
  });
}

function renderGenderChart(){
  const g = DATA.gender_counts;
  const r = DATA.religion_counts;
  new Chart(document.getElementById('genderChart'),{
    type:'doughnut',
    data:{
      labels:[
        ...g.map(x=>'性別: '+(GENDER_LABELS[x.gender_type]||x.gender_type)),
        ...r.map(x=>'系列: '+(RELIGION_LABELS[x.religious_affiliation]||x.religious_affiliation))
      ],
      datasets:[{
        data:[...g.map(x=>x.count),...r.map(x=>x.count)],
        backgroundColor:COLORS
      }]
    },
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{font:{size:11}}}}}
  });
}

function renderSubfieldChart(){
  const counts = DATA.subfield_counts;
  new Chart(document.getElementById('subfieldChart'),{
    type:'bar',
    data:{
      labels:counts.map(s=>SUBFIELD_LABELS[s.subfield]||s.subfield),
      datasets:[{label:'件数',data:counts.map(s=>s.count),backgroundColor:'#CC1400'}]
    },
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',plugins:{legend:{display:false}}}
  });
}

function renderSchoolFilters(){
  const prefs = [...new Set(DATA.schools.map(s=>s.location_pref))].sort();
  const sel = document.getElementById('filter-pref');
  prefs.forEach(p=>{
    const o = document.createElement('option');
    o.value = p;
    o.textContent = p;
    sel.appendChild(o);
  });
  const religions = [...new Set(DATA.schools.map(s=>s.religious_affiliation).filter(Boolean))];
  const rsel = document.getElementById('filter-religion');
  religions.forEach(r=>{
    const o = document.createElement('option');
    o.value = r;
    o.textContent = RELIGION_LABELS[r]||r;
    rsel.appendChild(o);
  });
}

function renderSchools(){
  const q = document.getElementById('search').value.trim();
  const pref = document.getElementById('filter-pref').value;
  const gender = document.getElementById('filter-gender').value;
  const religion = document.getElementById('filter-religion').value;
  let list = DATA.schools.filter(s=>{
    if(q && !s.name_ja.includes(q) && !(s.name_kana||'').includes(q)) return false;
    if(pref && s.location_pref!==pref) return false;
    if(gender && s.gender_type!==gender) return false;
    if(religion && s.religious_affiliation!==religion) return false;
    return true;
  });
  document.getElementById('schools-tbody').innerHTML = list.map(s=>`
    <tr class="school-row" onclick="showSchool('${s.id}')">
      <td><strong>${s.name_ja}</strong></td>
      <td>${s.location_pref} ${s.location_city||''}</td>
      <td><span class="badge ${s.gender_type}">${GENDER_LABELS[s.gender_type]||''}</span></td>
      <td><span class="badge ${s.religious_affiliation||''}">${RELIGION_LABELS[s.religious_affiliation]||''}</span></td>
      <td>${s.establishment_year||'—'}</td>
      <td class="right">
        <div class="progress-bar"><div class="fill" style="width:${s.data_completeness||0}%"></div></div>
      </td>
    </tr>
  `).join('');
}

function showSchool(id){
  const s = DATA.schools.find(x=>x.id===id);
  if(!s) return;
  const cur = DATA.curricula.find(c=>c.school_id===id);
  const tests = DATA.testimonials.filter(t=>t.school_id===id);
  let html = `
    <button class="close-btn" onclick="closeModal()">閉じる</button>
    <h3>${s.name_ja}</h3>
    <div class="meta">${s.name_kana||''} | ${s.location_pref} ${s.location_city||''} | ${s.establishment_year?s.establishment_year+'年創立':''}</div>
    <div>
      <span class="badge ${s.gender_type}">${GENDER_LABELS[s.gender_type]||''}</span>
      <span class="badge ${s.religious_affiliation||''}">${RELIGION_LABELS[s.religious_affiliation]||''}</span>
      <span class="badge">${s.school_corporation||''}</span>
    </div>
  `;
  if(s.founding_philosophy){
    html += `<div class="philosophy"><strong>建学の精神</strong><br>${s.founding_philosophy}</div>`;
  }
  if(s.education_principle){
    html += `<div class="philosophy"><strong>教育方針</strong><br>${s.education_principle}</div>`;
  }
  if(cur){
    const features = [];
    if(cur.inquiry_learning) features.push('探究学習');
    if(cur.steam) features.push('STEAM');
    if(cur.pbl) features.push('PBL');
    if(cur.international_track) features.push('国際教育');
    if(cur.ib_program && cur.ib_program!=='none') features.push('IB '+cur.ib_program);
    if(cur.ict_strength>=2) features.push('ICT強化');
    if(cur.art_strength>=2) features.push('芸術強化');
    if(cur.sports_strength>=2) features.push('体育強化');
    if(cur.religious_education) features.push('宗教教育');
    if(features.length){
      html += `<p style="margin-top:16px"><strong>カリキュラム特性:</strong> ${features.map(f=>'<span class="badge">'+f+'</span>').join('')}</p>`;
    }
  }
  if(tests.length){
    html += `<div class="testimonials"><h4 style="margin-bottom:12px;color:var(--akashiro-red)">関係者の声 (${tests.length}件)</h4>`;
    tests.forEach(t=>{
      const speakerLabel = {
        principal:'校長',teacher:'教員',student_current:'在校生',student_former:'卒業生',
        parent_current:'保護者',parent_former:'元保護者',external_evaluator:'第三者評価',third_party:'第三者'
      }[t.speaker_category]||t.speaker_category;
      html += `
        <div class="testimonial">
          <div class="who">${speakerLabel} | ${t.theme||''} | ${t.medium||''}</div>
          <div class="quote">${t.excerpt||t.summary||''}</div>
        </div>
      `;
    });
    html += `</div>`;
  }
  if(s.website_url){
    html += `<p style="margin-top:24px;font-size:13px"><a href="${s.website_url}" target="_blank" style="color:var(--akashiro-red)">公式サイト ↗</a></p>`;
  }
  document.getElementById('modal-content').innerHTML = html;
  document.getElementById('modal-bg').classList.add('open');
}

function closeModal(){
  document.getElementById('modal-bg').classList.remove('open');
}

function renderTopConcepts(){
  const top = [...DATA.concepts]
    .filter(c=>c.relevance_to_middle_school)
    .sort((a,b)=>b.relevance_to_middle_school-a.relevance_to_middle_school)
    .slice(0,10);
  document.getElementById('top-concepts').innerHTML = top.map(c=>`
    <tr>
      <td><strong>${c.name_ja}</strong></td>
      <td>${SUBFIELD_LABELS[c.subfield]||c.subfield}</td>
      <td class="right">${c.relevance_to_middle_school}</td>
    </tr>
  `).join('');
}

function renderOutcomes(){
  document.getElementById('outcomes-tbody').innerHTML = DATA.outcome_dimensions.map(o=>`
    <tr>
      <td><strong>${o.name_ja}</strong> <span style="color:var(--ink-soft);font-size:11px">${o.name_en}</span></td>
      <td>${o.framework}</td>
      <td>${o.measurability||''}</td>
      <td>${o.relevance_age||''}</td>
    </tr>
  `).join('');
}

function renderTestimonials(){
  const sample = DATA.testimonials.slice(0,12);
  const speakerLabel = {
    principal:'校長',teacher:'教員',student_current:'在校生',student_former:'卒業生',
    parent_current:'保護者',external_evaluator:'第三者評価'
  };
  document.getElementById('testimonials-list').innerHTML = sample.map(t=>`
    <div class="testimonial">
      <div class="who"><strong>${t.school_name||'—'}</strong> | ${speakerLabel[t.speaker_category]||t.speaker_category} | ${t.theme||''}</div>
      <div class="quote">${(t.excerpt||t.summary||'').slice(0,200)}${(t.excerpt||'').length>200?'...':''}</div>
    </div>
  `).join('');
}

function bindFilters(){
  ['search','filter-pref','filter-gender','filter-religion'].forEach(id=>{
    document.getElementById(id).addEventListener('input',renderSchools);
    document.getElementById(id).addEventListener('change',renderSchools);
  });
}

init();
