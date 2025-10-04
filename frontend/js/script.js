

/************ helpers ************/
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp01 = v => Math.max(0, Math.min(1, v));
const round = (x, d = 0) => Number.parseFloat(x ?? 0).toFixed(d);

/************ DOM ************/
const cityInput   = $('#cityInput');
const searchBtn   = $('#searchBtn');
const infoText    = $('.info-text');
const appContent  = $('#appContent');

const heroTempEl  = $('.temp');
const heroIconEl  = $('.weather-icon');
const heroMetaEls = $$('.details-meta .list-meta');
const forecastWrap= $('.forecast');

const ageEl       = $("input[aria-label='Age']");
const weightEl    = $("input[aria-label='Weight']");
const heightEl    = $("input[aria-label='Height']");
const genderEl    = $("select[aria-label='Gender']");

const dateInput   = $('#datePicker');
const openDateBtn = $('#openDate');
const analysisBtn = $('#analysisBtn');

const recoRoot    = $('#illnessDropdown'); 
const capsules    = $$('.capsules .capsule__fill'); 
const circleVal   = $('.circle__value');
const comfortSection = $('.comfort'); 

/************ state ************/
const State = {
  apiBaseUrl: null,
  city: '',
  forecast: [],
  selectedDate: null,
  comfortModel: null,
  comfortReady: false, 
};

/************ config / backend ************/
async function getApiBaseUrl() {
  
  if (State.apiBaseUrl) return State.apiBaseUrl;
  try {
    const r = await fetch('data/config.json', { cache: 'no-cache' });
    if (r.ok) {
      const cfg = await r.json();
      State.apiBaseUrl = cfg.API_BASE_URL;
      return State.apiBaseUrl;
    }
  } catch(_) {}
 
  State.apiBaseUrl = 'http://127.0.0.1:8000';
  return State.apiBaseUrl;
}

async function getForecast(city){
  const base = await getApiBaseUrl();
  const url = `${base}/weather/forecast?city=${encodeURIComponent(city)}`;
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error('backend error');
    return await r.json();
  } catch(_) {

    const local = `data/${city.toLowerCase()}.json`;
    const r2 = await fetch(local);
    if (!r2.ok) throw new Error(`no local data: ${local}`);
    return await r2.json();
  }
}

/************ comfort model  ************/
async function loadComfortModel(){
  try {
    const r = await fetch('data/simple_comfort_formulas.json');
    if (r.ok) return await r.json();
  } catch(_) {}
  return null; 
}

const getIntercept = s => {
  const m = String(s||'').match(/comfort\s*=\s*([\-0-9.]+)/i);
  return m ? Number(m[1]) : 0;
};
const z = (x, mean, std) => std ? (x - mean) / std : 0;

function readUserProfile(){
  const age    = Number(ageEl.value || 0);
  const weight = Number(weightEl.value || 0);
  const height = Number(heightEl.value || 0);
  const sexStr = (genderEl.value || '').toLowerCase();
  const sex    = sexStr === 'male' ? 1 : 0;
  const bmi    = height > 0 ? weight / Math.pow(height/100, 2) : 0;
  return { age, weight, height, bmi, sex };
}

function computeComfortForParam(paramName, weatherVal, user, node, normRequired){
  if (!node) {
 
    const ranges = {
      temperature: [0, 35],
      humidity:    [20, 90],
      wind_speed:  [0,  15],
      UVA:         [0,  12],
      AOD:         [0,  1],
    };
    const [lo, hi] = ranges[paramName] || [0, 1];
    const v = (weatherVal - lo) / (hi - lo);

    return clamp01(1 - Math.abs(v - 0.5) * 2);
  }

  const { coefficients, normalization, formula } = node;
  const intercept = getIntercept(formula);
  const means = normalization?.means || {};
  const stds  = normalization?.stds  || {};

  const Z = {
    temperature: paramName==='temperature' ? (normRequired ? z(weatherVal, means.temperature, stds.temperature) : weatherVal) : 0,
    humidity:    paramName==='humidity'    ? (normRequired ? z(weatherVal, means.humidity,    stds.humidity)    : weatherVal) : 0,
    wind_speed:  paramName==='wind_speed'  ? (normRequired ? z(weatherVal, means.wind_speed,  stds.wind_speed)  : weatherVal) : 0,
    UVA:         paramName==='UVA'         ? (normRequired ? z(weatherVal, means.UVA,         stds.UVA)         : weatherVal) : 0,
    AOD:         paramName==='AOD'         ? (normRequired ? z(weatherVal, means.AOD,         stds.AOD)         : weatherVal) : 0,

    age:         normRequired ? z(user.age,    means.age,    stds.age)    : user.age,
    BMI:         normRequired ? z(user.bmi,    means.BMI,    stds.BMI)    : user.bmi,
    height:      normRequired ? z(user.height, means.height, stds.height) : user.height,
    weight:      normRequired ? z(user.weight, means.weight, stds.weight) : user.weight,
    sex_numeric: user.sex,
  };

  const terms = {
    temperature_age: Z.temperature * Z.age,
    temperature_BMI: Z.temperature * Z.BMI,
    humidity_age:    Z.humidity    * Z.age,
    humidity_BMI:    Z.humidity    * Z.BMI,
    wind_speed_age:  Z.wind_speed  * Z.age,
    wind_speed_BMI:  Z.wind_speed  * Z.BMI,
    UVA_age:         Z.UVA         * Z.age,
    UVA_BMI:         Z.UVA         * Z.BMI,
    AOD_age:         Z.AOD         * Z.age,
    AOD_BMI:         Z.AOD         * Z.BMI,
  };

  let comfort = intercept;
  for (const [k, coef] of Object.entries(coefficients||{})){
    const v = (k in Z) ? Z[k] : (k in terms ? terms[k] : 0);
    comfort += coef * v;
  }
  return clamp01(comfort);
}

function calcAllComfortCaps(day, user){
  const m = State.comfortModel?.comfort_models || {};
  const needNorm = !!State.comfortModel?.normalization_required;

  const res = {
    temperature: computeComfortForParam('temperature', day.temperature,   user, m.comfort_temperature, needNorm),
    UV:          computeComfortForParam('UVA',         day.uv_index,      user, m.comfort_UVA,         needNorm),
    wind:        computeComfortForParam('wind_speed',  day.windspeed,     user, m.comfort_wind,        needNorm),
    humidity:    computeComfortForParam('humidity',    day.humidity,      user, m.comfort_humidity,    needNorm),
    AOD:         computeComfortForParam('AOD',         day.aod ?? 0,      user, m.comfort_AOD,         needNorm),
  };
  const total = (res.temperature + res.UV + res.wind + res.humidity + res.AOD) / 5;
  return { caps: res, total };
}

function renderCaps(result){
  const order = ['temperature','UV','wind','humidity','AOD'];
  order.forEach((k, i) => {
    const val = Math.round((result.caps[k] ?? 0) * 100);
    capsules[i].style.setProperty('--fill', `${val}%`);
  });
  circleVal.textContent = `${Math.round(result.total*100)}%`;
}

/************ weather UI ************/
function pickIcon({ temperature, precipitation_prob, cloudcover }){
  if ((precipitation_prob ?? 0) >= 50) return 'images/rain.png';
  if ((cloudcover ?? 0) >= 80)        return 'images/clouds.png';
  if ((temperature ?? 0) <= 0)        return 'images/snow.png';
  if ((temperature ?? 0) >= 28)       return 'images/clear.png';
  return 'images/mist.png';
}

function drawHero(day){
  heroTempEl.textContent = `${Math.round(day.temperature)}°C`;
  heroIconEl.src = pickIcon({
    temperature: day.temperature,
    precipitation_prob: day.percipitation_probability ?? 0,
    cloudcover: day.cloudcover ?? 0
  });

  const meta = [
    `Cloud: ${Math.round(day.cloudcover ?? 0)}%`,
    `UV: ${Math.round(day.uv_index ?? 0)}`,
    `Wind: ${round(day.windspeed ?? 0,1)} km/h`,
    `Humidity: ${Math.round(day.humidity ?? 0)}%`,
    `AOD: ${round(day.aod ?? 0,2)}`,
    `Rainfall: ${Math.round(day.percipitation_probability ?? 0)}%`,
  ];
  heroMetaEls.forEach((el, i) => el.textContent = meta[i] || '');
}

function drawForecastCards(days){
  forecastWrap.innerHTML = '';
  days.slice(0,5).forEach((d, idx)=>{
    const img = pickIcon({
      temperature:d.temperature,
      precipitation_prob:d.percipitation_probability ?? 0,
      cloudcover:d.cloudcover ?? 0
    });
    const card = document.createElement('article');
    card.className = 'daycard daycard--mist';
    card.innerHTML = `
      <h3 class="daycard__title">Day ${idx+1}</h3>
      <img src="${img}" width="88" height="88" alt="">
      <div class="daycard__temp">${Math.round(d.temperature)}°C</div>
      <div class="daycard__desc">${(d.cloudcover??0)>=80?'cloudy':(d.percipitation_probability??0)>=50?'rain':'clear'}</div>
    `;
    forecastWrap.appendChild(card);
  });
}

/************ recommendations ************/
async function loadAdviceRules(){

  try{
    const r = await fetch('data/recommendations.json', { cache: 'no-cache' });
    if (r.ok) return await r.json();
  }catch(_){}
  return null;
}

function ensureRecoUI(){
  if (!recoRoot.classList.contains('reco')) {
    recoRoot.className = 'reco';
    recoRoot.innerHTML = `
      <div class="reco__head" id="recoHead" hidden>
        <span id="recoLabel">Recommendations</span>
        <span>▾</span>
      </div>
      <ul class="reco__menu" id="recoMenu"></ul>
      <div class="reco__box" id="recoBox" hidden></div>
    `;
    $('#recoHead').addEventListener('click', ()=> {
      recoRoot.classList.toggle('is-open');
    });
    document.addEventListener('click', (e)=>{
      if (!recoRoot.contains(e.target)) recoRoot.classList.remove('is-open');
    });
  }
}

function evalRule(op, current, ruleValue){
  if (op === '>')  return current >  ruleValue;
  if (op === '>=') return current >= ruleValue;
  if (op === '<')  return current <  ruleValue;
  if (op === '<=') return current <= ruleValue;
  if (op === '==') return current == ruleValue;
  return false;
}

async function showRecommendations(currentDay){
  ensureRecoUI();
  const rules = await loadAdviceRules();
  const head  = $('#recoHead');
  const menu  = $('#recoMenu');
  const box   = $('#recoBox');
  const label = $('#recoLabel');


  if (!State.comfortReady) {
    head.hidden = true;
    box.hidden = true;
    menu.innerHTML = '';
    return;
  }

  head.hidden = false; 
  menu.innerHTML = '';
  box.hidden = true;   

  const options = [
    { key:'wind',        label:'Wind',        value: currentDay.windspeed },
    { key:'aod',         label:'AOD',         value: currentDay.aod ?? 0 },
    { key:'uv',          label:'UV',          value: currentDay.uv_index },
    { key:'humidity',    label:'Humidity',    value: currentDay.humidity },
    { key:'temperature', label:'Temperature', value: currentDay.temperature },
  ];

  options.forEach(opt=>{
    const li = document.createElement('li');
    li.className = 'reco__option';
    li.textContent = opt.label;
    li.addEventListener('click', ()=>{
      recoRoot.classList.remove('is-open');
      label.textContent = opt.label;

      const arr = rules?.[opt.key] || [];
      const hit = arr.find(r => evalRule(r.operator, opt.value, r.value));

      if (hit?.text) {
        box.textContent = hit.text;
        box.hidden = false;
      } else {
       
        box.hidden = true;
      }
    });
    menu.appendChild(li);
  });
}

/************ date picker (з хінтом) ************/
const start = new Date();
start.setHours(0,0,0,0);
const end = new Date(start);
end.setDate(end.getDate() + 5);
end.setHours(23,59,59,999);


dateInput.placeholder = 'Оберіть дату';

const fp = flatpickr(dateInput, {
  dateFormat: 'd/m/Y',
  defaultDate: null,         
  minDate: start,
  maxDate: end,
  clickOpens: false,
  allowInput: false,
  locale: 'en',
  disableMobile: true,
  monthSelectorType: 'static',
  onChange: (dates) => {
    State.selectedDate = dates?.[0] ?? null;
    updateAnalysisButtonState();
  }
});
openDateBtn.addEventListener('click', e => { e.preventDefault(); fp.open(); });

/************ flow ************/
function allProfileFilled(){
  return (
    cityInput.value.trim() &&
    ageEl.value.trim() &&
    weightEl.value.trim() &&
    heightEl.value.trim() &&
    (genderEl.value || '').toLowerCase() !== 'gender'
  );
}

function updateAnalysisButtonState(){
  
  const canAnalyze = allProfileFilled() && !!State.selectedDate && State.forecast.length > 0;
  analysisBtn.classList.toggle('is-hidden', !canAnalyze);
}

function resetComfortUI(){
  State.comfortReady = false;
  capsules.forEach(f => f.style.setProperty('--fill', '0%'));
  circleVal.textContent = '0%';

  ensureRecoUI();
  $('#recoHead').hidden = true;
  $('#recoBox').hidden = true;
  $('#recoMenu').innerHTML = '';
}

/************ search & analysis ************/
async function handleSearch(){
  const q = cityInput.value.trim();
  if (!q) return;
  State.city = q;


  if (!State.comfortModel) {
    State.comfortModel = await loadComfortModel();
  }

  try{
    const data = await getForecast(q);
    State.forecast = Array.isArray(data) ? data : (data?.days || []);
  }catch(err){
    alert(`Не знайдено дані для міста "${q}". Додай файл data/${q.toLowerCase()}.json або увімкни бекенд.`);
    return;
  }


  infoText?.classList.add('hidden');
  appContent.hidden = false;
  requestAnimationFrame(()=> appContent.classList.add('is-visible'));

  if (State.forecast.length){
    drawHero(State.forecast[0]);
    drawForecastCards(State.forecast);
  }

  resetComfortUI();
  updateAnalysisButtonState();
}

async function doAnalysis(){

  let day = State.forecast[0];
  if (State.selectedDate && State.forecast.length){
    const iso = State.selectedDate.toISOString().slice(0,10);
    day = State.forecast.find(d => String(d.date).slice(0,10) === iso) || day;
  }


  const user = readUserProfile();
  const result = calcAllComfortCaps(day, user);
  renderCaps(result);
  State.comfortReady = true;

  
  await showRecommendations({
    temperature: day.temperature,
    humidity: day.humidity,
    windspeed: day.windspeed,
    uv_index: day.uv_index,
    aod: day.aod ?? 0
  });


  comfortSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/************ events ************/
cityInput.setAttribute('autocomplete','off');
searchBtn.addEventListener('click', e => { e.preventDefault(); handleSearch(); });
cityInput.addEventListener('keydown', e => { if (e.key === 'Enter'){ e.preventDefault(); handleSearch(); }});

[ageEl, weightEl, heightEl, genderEl].forEach(el => {
  el.addEventListener('input', updateAnalysisButtonState);
  el.addEventListener('change', updateAnalysisButtonState);
});

analysisBtn.addEventListener('click', e => { e.preventDefault(); doAnalysis(); });

/************ init ************/
(function init(){

  updateAnalysisButtonState();
})();


