// js/script.js

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const round = (x, d = 0) => Number.parseFloat(x).toFixed(d);

// Мапа іконок за погодою (спрощено)
function pickIcon({ temperature, precipitation_prob, cloudcover }) {
  if (precipitation_prob >= 50) return 'images/rain.png';
  if (cloudcover >= 80)        return 'images/clouds.png';
  if (temperature <= 0)        return 'images/snow.png';
  if (temperature >= 28)       return 'images/clear.png';
  return 'images/mist.png';
}

// ======================  ГЛОБАЛЬНИЙ СТАН  ======================
const State = {
  city: '',
  forecast: [],     
  selectedDate: null,
  comfortModel: null, 
};

// ======================  DOM ЕЛЕМЕНТИ  ======================
const infoText      = $('.info-text');
const appContent    = $('#appContent');
const cityInput     = $('#cityInput');
const searchBtn     = $('#searchBtn');

const heroTempEl    = $('.temp');
const heroIconEl    = $('.weather-icon');
const heroMetaEls   = $$('.details-meta .list-meta');

const forecastWrap  = $('.forecast');

const ageEl         = $("input[aria-label='Age']");
const weightEl      = $("input[aria-label='Weight']");
const heightEl      = $("input[aria-label='Height']");
const genderEl      = $("select[aria-label='Gender']");

const dateInput     = $('#datePicker');
const openDateBtn   = $('#openDate');

const analysisBtn   = $('#analysisBtn');


const recoRoot      = $('#illnessDropdown');


const capsulesFills = $$('.capsules .capsule__fill'); 
const circleValEl   = $('.circle__value');

// ======================  FLATPICKR  ======================
const start = new Date();
start.setHours(0,0,0,0);
const end = new Date(start);
end.setDate(end.getDate() + 5);
end.setHours(23,59,59,999);

const fp = flatpickr(dateInput, {
  dateFormat: 'd/m/Y',
  defaultDate: start,
  minDate: start,
  maxDate: end,
  enable: [{ from: start, to: end }],
  clickOpens: false,
  allowInput: false,
  locale: 'en',
  disableMobile: true,
  monthSelectorType: 'static',
  onReady: limitMonthNav,
  onMonthChange: limitMonthNav,
  onChange: () => {
    
    analysisBtn.classList.remove('is-hidden');
    State.selectedDate = fp.selectedDates?.[0] ?? null;
  }
});
function limitMonthNav(_, __, inst){
  const prev = inst.prevMonthNav;
  const next = inst.nextMonthNav;
  const calStart = new Date(inst.currentYear, inst.currentMonth, 1);
  const calEnd   = new Date(inst.currentYear, inst.currentMonth + 1, 0);
  prev.disabled = calStart <= new Date(start.getFullYear(), start.getMonth(), 1);
  next.disabled = calEnd   >= new Date(end.getFullYear(),   end.getMonth() + 1, 0);
}
openDateBtn.addEventListener('click', (e) => { e.preventDefault(); fp.open(); });

// ======================  ЗАВАНТАЖЕННЯ ФОРМУЛ КОМФОРТУ  ======================
async function loadComfortModel() {
  const tries = [
    'data/simple_comfort_formulas.json',    
    '../Analytics/simple_comfort_formulas.json'
  ];
  for (const url of tries) {
    try {
      const r = await fetch(url);
      if (r.ok) return await r.json();
    } catch(_){}
  }
  console.warn('⚠️ Не знайдено simple_comfort_formulas.json');
  return null;
}


function getIntercept(formulaStr){
  const m = String(formulaStr||'').match(/comfort\s*=\s*([\-0-9.]+)/i);
  return m ? Number(m[1]) : 0;
}


function z(x, mean, std){
  if (std === 0) return 0;
  return (x - mean) / std;
}


function readUserProfile(){
  const age    = Number(ageEl.value || 0);
  const weight = Number(weightEl.value || 0);
  const height = Number(heightEl.value || 0);
  const sexStr = (genderEl.value || '').toLowerCase();
  const sex    = sexStr === 'male' ? 1 : 0;
  const bmi    = (height > 0) ? weight / Math.pow(height/100, 2) : 0;
  return { age, weight, height, bmi, sex };
}


function computeComfortForParam(paramName, weatherVal, user, modelNode){
  if (!modelNode) return 0.5;

  const { coefficients, normalization, formula } = modelNode;
  const intercept = getIntercept(formula);


  const useNorm = !!State.comfortModel?.normalization_required;
  const means = normalization?.means || {};
  const stds  = normalization?.stds  || {};


  const Z = {

    temperature:      useNorm ? z((paramName==='temperature'?weatherVal:0), means.temperature, stds.temperature) : (paramName==='temperature'?weatherVal:0),
    humidity:         useNorm ? z((paramName==='humidity'?weatherVal:0),    means.humidity,    stds.humidity)    : (paramName==='humidity'?weatherVal:0),
    wind_speed:       useNorm ? z((paramName==='wind_speed'?weatherVal:0),  means.wind_speed,  stds.wind_speed)  : (paramName==='wind_speed'?weatherVal:0),
    UVA:              useNorm ? z((paramName==='UVA'?weatherVal:0),         means.UVA,         stds.UVA)         : (paramName==='UVA'?weatherVal:0),
    AOD:              useNorm ? z((paramName==='AOD'?weatherVal:0),         means.AOD,         stds.AOD)         : (paramName==='AOD'?weatherVal:0),


    age:              useNorm ? z(user.age,    means.age,    stds.age)    : user.age,
    BMI:              useNorm ? z(user.bmi,    means.BMI,    stds.BMI)    : user.bmi,
    height:           useNorm ? z(user.height, means.height, stds.height) : user.height,
    weight:           useNorm ? z(user.weight, means.weight, stds.weight) : user.weight,
    sex_numeric:      user.sex,
  };

  const terms = {
    temperature_age:      Z.temperature * Z.age,
    temperature_BMI:      Z.temperature * Z.BMI,
    humidity_age:         Z.humidity    * Z.age,
    humidity_BMI:         Z.humidity    * Z.BMI,
    wind_speed_age:       Z.wind_speed  * Z.age,
    wind_speed_BMI:       Z.wind_speed  * Z.BMI,
    UVA_age:              Z.UVA         * Z.age,
    UVA_BMI:              Z.UVA         * Z.BMI,
    AOD_age:              Z.AOD         * Z.age,
    AOD_BMI:              Z.AOD         * Z.BMI,
  };


  let comfort = intercept;
  for (const [key, coef] of Object.entries(coefficients||{})){
    const val = (key in Z) ? Z[key] : (key in terms ? terms[key] : 0);
    comfort += coef * val;
  }


  comfort = Math.max(0, Math.min(1, comfort));
  return comfort;
}


function calcAllComfortCaps(weather, user){
  const model = State.comfortModel?.comfort_models || {};
  const caps = {
    temperature: computeComfortForParam('temperature', weather.temperature, user, model.comfort_temperature),
    UV:          computeComfortForParam('UVA',         weather.uv_index,    user, model.comfort_UVA),
    wind:        computeComfortForParam('wind_speed',  weather.windspeed,   user, model.comfort_wind),
    humidity:    computeComfortForParam('humidity',    weather.humidity,    user, model.comfort_humidity),
    AOD:         computeComfortForParam('AOD',         weather.aod ?? 0,    user, model.comfort_AOD),
  };

  const avg = (caps.temperature + caps.UV + caps.wind + caps.humidity + caps.AOD) / 5;
  return { caps, total: avg };
}

function renderCapsulesAndCircle(result){
  const order = ['temperature','UV','wind','humidity','AOD'];
  order.forEach((key, i) => {
    const val = Math.round((result.caps[key] ?? 0) * 100);
    capsulesFills[i].style.setProperty('--fill', `${val}%`);
  });
  circleValEl.textContent = `${Math.round(result.total*100)}%`;
}

// ======================  РЕКОМЕНДАЦІЇ  ======================
async function loadAdviceRules(){

  const tries = [
    'data/recommendations.json'       
  ];
  for (const url of tries){
    try {
      const r = await fetch(url);
      if (r.ok) return await r.json();
    } catch(_){}
  }
  return null;
}

function evalRule(operator, currentValue, ruleValue){
  if (operator === '>')  return currentValue >  ruleValue;
  if (operator === '>=') return currentValue >= ruleValue;
  if (operator === '<')  return currentValue <  ruleValue;
  if (operator === '<=') return currentValue <= ruleValue;
  if (operator === '==') return currentValue == ruleValue;
  return false;
}

function ensureRecoUI(){
  if (!recoRoot.classList.contains('reco')){
    recoRoot.className = 'reco';
    recoRoot.innerHTML = `
      <div class="reco__head" id="recoHead">
        <span id="recoLabel">Recommendations</span>
        <span>▾</span>
      </div>
      <ul class="reco__menu" id="recoMenu"></ul>
      <div class="reco__box" id="recoBox" hidden></div>
    `;
    // toggle menu
    $('#recoHead').addEventListener('click', ()=>{
      recoRoot.classList.toggle('is-open');
    });
    document.addEventListener('click', (e)=>{
      if (!recoRoot.contains(e.target)) recoRoot.classList.remove('is-open');
    });
  }
}

async function buildRecommendationsUI(currentWeather){
  ensureRecoUI();
  const menu = $('#recoMenu');
  const box  = $('#recoBox');
  const label= $('#recoLabel');
  menu.innerHTML = '';

  const rules = await loadAdviceRules();

  const options = [
    { key:'wind',        label:'Wind',  value: currentWeather.windspeed },
    { key:'aod',         label:'AOD',   value: currentWeather.aod ?? 0 },
    { key:'uv',          label:'UV',    value: currentWeather.uv_index },
    { key:'humidity',    label:'Humidity', value: currentWeather.humidity },
    { key:'temperature', label:'Temperature', value: currentWeather.temperature },
  ];

  options.forEach(opt=>{
    const li = document.createElement('li');
    li.className = 'reco__option';
    li.textContent = opt.label;
    li.addEventListener('click', ()=>{
      recoRoot.classList.remove('is-open');
      label.textContent = opt.label;

      
      const list = (rules?.[opt.key] || []);
      const matched = list.find(r => evalRule(r.operator, opt.value, r.value));

      
      box.hidden = false;
      box.textContent = matched ? matched.text : 'No recommendations at the moment.';

      
      const user = readUserProfile();
      const result = calcAllComfortCaps(currentWeather, user);
      renderCapsulesAndCircle(result);

      
    });
    menu.appendChild(li);
  });
}

// ======================  ПРОГНОЗ / РЕНДЕР  ======================
async function getForecast(city){
  const url = `http://127.0.0.1:8000/weather/forecast?city=${encodeURIComponent(city)}`;
  try{
    const r = await fetch(url);
    if (!r.ok) throw new Error('backend error');
    return await r.json();
  }catch(_){

    const local = `data/${city.toLowerCase()}.json`;
    const r2 = await fetch(local);
    if (!r2.ok) throw new Error(`no local data: ${local}`);
    return await r2.json();
  }
}

function drawHero(day){
  heroTempEl.textContent = `${Math.round(day.temperature)}°C`;
  heroIconEl.src = pickIcon({
    temperature: day.temperature,
    precipitation_prob: day.percipitation_probability ?? 0,
    cloudcover: day.cloudcover ?? 0
  });


  const cloud    = `Cloud: ${Math.round(day.cloudcover ?? 0)}%`;
  const uv       = `UV: ${Math.round(day.uv_index ?? 0)}`;
  const wind     = `Wind: ${round(day.windspeed ?? 0,1)} km/h`;
  const humid    = `Humidity: ${Math.round(day.humidity ?? 0)}%`;
  const aod      = `AOD: ${round(day.aod ?? 0,2)}`;
  const rainProb = `Rainfall: ${Math.round(day.percipitation_probability ?? 0)}%`;

  const arr = [cloud, uv, wind, humid, aod, rainProb];
  heroMetaEls.forEach((el,i)=> el.textContent = arr[i] || '');
}

function drawForecastCards(days){
  forecastWrap.innerHTML = '';
  days.slice(0,5).forEach((d, idx)=>{
    const art = document.createElement('article');
    art.className = 'daycard daycard--mist';
    art.innerHTML = `
      <h3 class="daycard__title">Day ${idx+1}</h3>
      <img src="${pickIcon({
        temperature:d.temperature,
        precipitation_prob:d.percipitation_probability??0,
        cloudcover:d.cloudcover??0
      })}" alt="" width="88" height="88"/>
      <div class="daycard__temp">${Math.round(d.temperature)}°C</div>
      <div class="daycard__desc">${(d.cloudcover??0) >= 80 ? 'cloudy' : (d.percipitation_probability??0) >= 50 ? 'rain' : 'clear'}</div>
    `;
    forecastWrap.appendChild(art);
  });
}

// ======================  ПОШУК / ПОКАЗ ДОДАТКА  ======================
async function handleSearch(){
  const q = cityInput.value.trim();
  if (!q) return;

  State.city = q;


  if (!State.comfortModel){
    State.comfortModel = await loadComfortModel();
  }

  
  try{
    const data = await getForecast(q);
   
    State.forecast = Array.isArray(data) ? data : (data?.days || []);
  }catch(err){
    console.error(err);
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

 
  analysisBtn.classList.add('is-hidden');
  recoRoot.classList.add('is-hidden');
  $('#recoBox')?.setAttribute('hidden','');

 
  capsulesFills.forEach(f => f.style.setProperty('--fill','0%'));
  circleValEl.textContent = '0%';
}

// ======================  ПОДІЇ  ======================
cityInput.setAttribute('autocomplete','off');
searchBtn.addEventListener('click', (e)=>{ e.preventDefault(); handleSearch(); });
cityInput.addEventListener('keydown', (e)=>{ if (e.key === 'Enter'){ e.preventDefault(); handleSearch(); }});


analysisBtn.addEventListener('click', async (e)=>{
  e.preventDefault();
  
  let day = State.forecast[0];
  if (State.selectedDate && State.forecast.length){
 
    const iso = State.selectedDate.toISOString().slice(0,10);
    day = State.forecast.find(d => String(d.date).slice(0,10) === iso) || day;
  }


  recoRoot.classList.remove('is-hidden');
  await buildRecommendationsUI({
    temperature: day.temperature,
    humidity: day.humidity,
    windspeed: day.windspeed,
    uv_index: day.uv_index,
    aod: day.aod ?? 0,
    cloudcover: day.cloudcover ?? 0,
    percipitation_probability: day.percipitation_probability ?? 0
  });


});


(async function init(){

})();

