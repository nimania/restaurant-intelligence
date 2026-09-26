"use strict";
// City benchmarks live in data/cities/<id>.json, listed in data/cities/index.json.
// See README.md ("Cities") for the file format and how to add a city.
let CITIES = {},
  cityOrder = [],
  city = null,
  zones = [];
const concepts = [
  {
    id: "burger",
    name: "برگر و فست‌فود",
    target: 60,
    setup: 1485000000,
    check: 1228000,
    payroll: 170630000,
    fixed: 70000000,
    cm: 0.61,
    margin: 0.08,
    labor: 0.3,
    mult: 1,
    low: 0.72,
    white: "qsr",
    emoji: "🍔",
  },
  {
    id: "pizza",
    name: "پیتزا",
    target: 70,
    setup: 1979000000,
    check: 1528350,
    payroll: 202340000,
    fixed: 75000000,
    cm: 0.62,
    margin: 0.08,
    labor: 0.3,
    mult: 0.95,
    low: 0.72,
    white: "qsr",
    emoji: "🍕",
  },
  {
    id: "cafe",
    name: "کافه",
    target: 80,
    setup: 2938000000,
    check: 409184,
    payroll: 206740000,
    fixed: 73000000,
    cm: 0.68,
    margin: 0.07,
    labor: 0.3,
    mult: 1.15,
    low: 0.678,
    white: "cafe",
    emoji: "☕",
  },
  {
    id: "iranian",
    name: "ایرانی و کباب",
    target: 120,
    setup: 3548000000,
    check: 1012060,
    payroll: 416970000,
    fixed: 95000000,
    cm: 0.61,
    margin: 0.05,
    labor: 0.34,
    mult: 0.8,
    low: 0.692,
    white: "traditional",
    emoji: "🍢",
  },
  {
    id: "delivery",
    name: "ارسال‌محور / بیرون‌بر",
    target: 40,
    setup: 996700000,
    check: 1293770,
    payroll: 170630000,
    fixed: 71000000,
    cm: 0.49,
    margin: 0.08,
    labor: 0.3,
    mult: 1.25,
    low: 0.818,
    white: "qsr",
    emoji: "🛵",
  },
];
const values = {
  budget: [1500000000, 2500000000, 4000000000, 6000000000, 9000000000],
  size: [30, 50, 75, 120, 180, 60],
  concept: ["any", "burger", "pizza", "cafe", "iranian", "delivery"],
  operation: ["dinein", "takeaway", "delivery", "any"],
  risk: ["low", "medium", "high"],
};
const labels = {
  budget: {
    1500000000: "تا ۱.۵ میلیارد",
    2500000000: "۱.۵ تا ۲.۵ میلیارد",
    4000000000: "۲.۵ تا ۴ میلیارد",
    6000000000: "۴ تا ۶ میلیارد",
    9000000000: "بیشتر از ۶ میلیارد",
  },
  size: {
    30: "زیر ۴۰ متر",
    50: "۴۰ تا ۶۰ متر",
    60: "اندازه متعادل",
    75: "۶۰ تا ۹۰ متر",
    120: "۹۰ تا ۱۵۰ متر",
    180: "بیشتر از ۱۵۰ متر",
  },
  concept: {
    any: "فرقی نمی‌کند",
    burger: "برگر و فست‌فود",
    pizza: "پیتزا",
    cafe: "کافه",
    iranian: "ایرانی و کباب",
    delivery: "ارسال‌محور",
  },
  operation: {
    dinein: "سالن‌محور",
    takeaway: "بیرون‌بر",
    delivery: "ارسال اینترنتی",
    any: "فرقی نمی‌کند",
  },
  risk: { low: "کم", medium: "متوسط", high: "زیاد" },
};
const PROPERTY_REQUIREMENTS = {
  common: [
    {
      id: "permission",
      label: "امکان فعالیت غذایی و موافقت مالک",
      positive: /رستوران|کافه|فست.?فود|اغذیه|کباب|مجوز|کاربری تجاری/,
      negative: /صرفاً اداری|بدون پخت|ممنوعیت پخت/,
      question:
        "آیا اجازه فعالیت غذایی، نصب تابلو و تغییرات لازم در قرارداد نوشته می‌شود؟",
      critical: true,
    },
    {
      id: "ventilation",
      label: "مسیر مستقل هود، اگزاست و هوای جبرانی",
      positive: /هود|اگزاست|دودکش|تهویه|کانال/,
      negative: /بدون دودکش|امکان هود ندارد|ممنوعیت اگزاست/,
      question:
        "مسیر خروج کانال تا بام یا نمای مجاز کجاست و مالک کتبی موافق است؟",
      critical: true,
    },
    {
      id: "utilities",
      label: "آب، برق و گاز متناسب با تجهیزات",
      positive: /آب و برق و گاز|انشعاب گاز|برق سه.?فاز|سه.?فاز|کنتور مستقل/,
      negative: /بدون گاز|فاقد گاز|برق ضعیف|کنتور مشترک/,
      question: "آمپر برق، نوع انشعاب، فشار آب و گاز مستقل دقیقاً چقدر است؟",
      critical: true,
    },
    {
      id: "sanitation",
      label: "فاضلاب، شست‌وشو و سرویس بهداشتی",
      positive: /سرویس بهداشتی|فاضلاب|کفشور|سینک|آب گرم/,
      negative: /بدون سرویس|سرویس مشترک|فاقد سرویس/,
      question: "کفشور، فاضلاب، محل سینک و سرویس اختصاصی قابل‌تأیید است؟",
      critical: true,
    },
    {
      id: "access",
      label: "دسترسی مشتری، پیک و بارگیری",
      positive: /پارکینگ|جای پارک|بر اصلی|دو دهنه|دسترسی|کمربندی|حیاط/,
      negative: /کوچه باریک|بدون پارک|دسترسی سخت/,
      question:
        "در ساعت شلوغ، توقف کوتاه مشتری و پیک و تخلیه بار عملاً ممکن است؟",
      critical: false,
    },
    {
      id: "level",
      label: "همکف، ورودی و حمل تجهیزات",
      positive: /همکف|هم سطح|درب بزرگ|ورودی مستقل/,
      negative: /زیرزمین|بالای همکف|طبقه دوم|راه پله|پله زیاد/,
      question:
        "عرض در، تعداد پله و مسیر ورود تجهیزات سنگین اندازه‌گیری شده است؟",
      critical: false,
    },
  ],
  burger: [
    {
      id: "burger-line",
      label: "خط گرم مناسب گریل و سرخ‌کن",
      positive: /گریل|سرخ.?کن|آشپزخانه|خط پخت/,
      negative: /پخت ممنوع/,
      question:
        "طول خط گرم، فاصله ایمن و ظرفیت هود برای گریل و سرخ‌کن کافی است؟",
      critical: true,
    },
  ],
  pizza: [
    {
      id: "pizza-line",
      label: "فضای فر، خمیر و تخمیر",
      positive: /فر پیتزا|خمیرگیر|آشپزخانه|پیتزا/,
      negative: /پخت ممنوع/,
      question:
        "محل فر، خمیرگیر، میز بازکردن خمیر و نگهداری خمیر قابل جانمایی است؟",
      critical: true,
    },
  ],
  cafe: [
    {
      id: "coffee-bar",
      label: "آب، تخلیه و برق بار قهوه",
      positive: /کافه|کافی.?شاپ|کانتر|آب و برق|سینک/,
      negative: /بدون آب|فاقد فاضلاب/,
      question: "نقطه آب تصفیه‌شده، تخلیه و مدار برق مجزای اسپرسوساز کجاست؟",
      critical: true,
    },
  ],
  iranian: [
    {
      id: "heavy-cookline",
      label: "خط پخت سنگین و دود کباب",
      positive: /کباب.?پز|چلوپز|آشپزخانه صنعتی|رستوران/,
      negative: /پخت ممنوع|بدون دودکش/,
      question:
        "دبی هود و مسیر دود برای کباب‌پز و دیگ‌ها توسط متخصص تأیید می‌شود؟",
      critical: true,
    },
  ],
  delivery: [
    {
      id: "dispatch",
      label: "ایستگاه بسته‌بندی و تحویل پیک",
      positive: /بیرون.?بر|دلیوری|پیک|بسته.?بندی|دسترسی/,
      negative: /توقف ممنوع|دسترسی سخت/,
      question: "پیک بدون تداخل با خط تولید و مشتری حضوری کجا منتظر می‌ماند؟",
      critical: false,
    },
  ],
};
const stepKey = {
  1: "budget",
  2: "size",
  3: "concept",
  4: "operation",
  5: "risk",
};
const clamp = (n, min = 0, max = 100) => Math.max(min, Math.min(max, n));
const fmt = (n) =>
  new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 1 }).format(n);
const money = (n) =>
  n == null
    ? "نامشخص"
    : n >= 1e9
      ? `${fmt(n / 1e9)} میلیارد تومان`
      : `${fmt(n / 1e6)} میلیون تومان`;
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
let maxRPB = 1;
let step = 1,
  answers = {},
  propertyData = { meta: null, properties: [] },
  equipmentData = { methodology: {}, items: {}, kits: {} },
  activePlannerKey = 0,
  propertyDetailCache = new Map();
function cityMaxRPB(c) {
  return Math.max(...c.zones.map((z) => z.reviews / z.active));
}
function requestedCity() {
  try {
    const q = new URLSearchParams(location.search).get("city");
    if (q && CITIES[q]) return q;
  } catch {}
  return CITIES.nowshahr ? "nowshahr" : cityOrder[0];
}
async function loadCities() {
  const index = await fetch("./data/cities/index.json", {
    cache: "no-store",
  }).then((r) => {
    if (!r.ok) throw new Error(`city index ${r.status}`);
    return r.json();
  });
  const loaded = await Promise.allSettled(
    index.cities.map((entry) =>
      fetch(`./data/cities/${entry.file}`, { cache: "no-store" }).then((r) => {
        if (!r.ok) throw new Error(`city ${entry.id} ${r.status}`);
        return r.json();
      }),
    ),
  );
  loaded.forEach((result, i) => {
    if (result.status === "fulfilled" && result.value.zones?.length) {
      CITIES[result.value.id] = result.value;
      cityOrder.push(result.value.id);
    } else console.warn("City data unavailable", index.cities[i], result.reason);
  });
  if (!cityOrder.length) throw new Error("no city data");
  useCity(requestedCity());
}
function useCity(id) {
  city = CITIES[id];
  zones = city.zones;
  maxRPB = cityMaxRPB(city);
}
async function loadCityProperties() {
  if (!city.properties_file) return { meta: null, properties: [] };
  const r = await fetch(`./${city.properties_file}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`property data ${r.status}`);
  return r.json();
}
async function loadPlannerData() {
  await loadCities();
  const [properties, equipment] = await Promise.allSettled([
    loadCityProperties(),
    fetch("./data/equipment-catalog.json", { cache: "no-store" }).then((r) => {
      if (!r.ok) throw new Error(`equipment data ${r.status}`);
      return r.json();
    }),
  ]);
  if (properties.status === "fulfilled") propertyData = properties.value;
  else {
    propertyData = { meta: null, properties: [] };
    console.warn("Property data unavailable", properties.reason);
  }
  if (equipment.status === "fulfilled") equipmentData = equipment.value;
  else console.warn("Equipment data unavailable", equipment.reason);
}
function riskThreshold(r) {
  return r === "low" ? 0.75 : r === "high" ? 0.55 : 0.65;
}
function evaluate(a, forCity = city) {
  if (!a.budget || !a.size || !a.concept || !a.operation || !a.risk) return [];
  const selected =
      a.concept === "any"
        ? concepts
        : concepts.filter((c) => c.id === a.concept),
    cityZones = forCity.zones,
    cityRPB = forCity === city ? maxRPB : cityMaxRPB(forCity);
  const maxRent = Math.max(
      ...cityZones.filter((z) => z.rent).map((z) => z.rent),
    ),
    rows = [];
  for (const c of selected)
    for (const z of cityZones) {
      const monthlyRent = (z.rent || 0) * a.size,
        deposit = (z.deposit || 0) * a.size,
        scale = 0.65 + 0.35 * clamp(a.size / c.target, 0.55, 1.45),
        capital = c.setup * scale + deposit + 3 * monthlyRent,
        fixed = c.payroll + c.fixed + monthlyRent,
        healthy = Math.max(
          fixed / Math.max(0.05, c.cm - c.margin),
          c.payroll / c.labor,
          monthlyRent / 0.06,
        ),
        tickets = healthy / c.check / 30,
        reviewIntensity = (100 * (z.reviews / z.active)) / cityRPB,
        zoneDemand = 0.75 * z.demand + 0.25 * reviewIntensity,
        opportunity = 0.8 * zoneDemand + 0.2 * z.w[c.white],
        supported = 40 * (0.5 + opportunity / 100) * c.mult,
        low = supported * c.low,
        coverage = supported / tickets,
        lowCoverage = low / tickets,
        affordability = z.rent === null ? 25 : 100 * (1 - z.rent / maxRent),
        market = 0.5 * z.demand + 0.25 * z.w[c.white] + 0.25 * affordability,
        budgetScore =
          capital > a.budget
            ? 0
            : clamp(55 + (45 * ((a.budget - capital) / a.budget)) / 0.35),
        sizeScore = clamp(100 - (100 * Math.abs(a.size - c.target)) / c.target),
        bonus =
          (a.operation === "delivery" && c.id === "delivery" ? 8 : 0) +
          (a.operation === "takeaway" &&
          ["burger", "pizza", "delivery"].includes(c.id)
            ? 5
            : 0) +
          (a.operation === "dinein" &&
          ["cafe", "iranian", "pizza"].includes(c.id)
            ? 5
            : 0),
        score = clamp(
          0.35 * market +
            0.25 * budgetScore +
            0.15 * sizeScore +
            0.15 * clamp(coverage * 100) +
            0.1 * z.confidence * 100 +
            bonus,
        ),
        eligible =
          capital <= a.budget &&
          z.confidence >= riskThreshold(a.risk) &&
          z.rent !== null;
      rows.push({
        city: forCity,
        concept: c,
        zone: z,
        monthlyRent,
        capital,
        tickets,
        coverage,
        lowCoverage,
        score,
        eligible,
      });
    }
  return rows.sort(
    (x, y) => (x.eligible ? 0 : 1) - (y.eligible ? 0 : 1) || y.score - x.score,
  );
}
function viableCompletions(partial, forCity = city) {
  const missing = Object.keys(values).filter((k) => partial[k] === undefined);
  let count = 0;
  function walk(i, obj) {
    if (count > 5) return;
    if (i === missing.length) {
      if (evaluate(obj, forCity).some((x) => x.eligible)) count++;
      return;
    }
    for (const v of values[missing[i]])
      walk(i + 1, { ...obj, [missing[i]]: v });
  }
  walk(0, { ...partial });
  return count;
}
function refreshOptionAvailability() {
  document.querySelectorAll("[data-key]").forEach((group) => {
    const key = group.dataset.key;
    group.querySelectorAll(".option").forEach((btn) => {
      const value = ["budget", "size"].includes(key)
          ? Number(btn.dataset.value)
          : btn.dataset.value,
        partial = { ...answers, [key]: value },
        count = viableCompletions(partial),
        elsewhere =
          count === 0
            ? cityOrder.filter(
                (id) =>
                  CITIES[id] !== city &&
                  viableCompletions(partial, CITIES[id]) > 0,
              )
            : [];
      btn.disabled = count === 0 && !elsewhere.length;
      btn.classList.toggle("limited", count > 0 && count <= 2);
      btn.classList.toggle("elsewhere", elsewhere.length > 0);
      let hint = btn.querySelector(".elsewhere-hint");
      if (elsewhere.length) {
        if (!hint) {
          hint = document.createElement("em");
          hint.className = "elsewhere-hint";
          btn.appendChild(hint);
        }
        hint.textContent = `در ${city.name} نه؛ در ${elsewhere
          .map((id) => CITIES[id].name)
          .join(" و ")} شدنی`;
      } else hint?.remove();
      btn.dataset.disabledReason = btn.disabled
        ? "با انتخاب‌های فعلی نتیجه قابل‌عرضه‌ای باقی نمی‌ماند"
        : "";
      if (btn.disabled && btn.classList.contains("active")) {
        btn.classList.remove("active");
        delete answers[key];
      }
    });
  });
}
function showStep() {
  document
    .querySelectorAll(".screen")
    .forEach((s) =>
      s.classList.toggle("active", Number(s.dataset.step) === step),
    );
  document.getElementById("progressBar").style.width =
    `${Math.min(step, 5) * 20}%`;
  document.getElementById("stepLabel").textContent =
    step <= 5 ? `مرحله ${step} از ۵` : "نتیجه";
  document.getElementById("prev").style.visibility =
    step === 1 ? "hidden" : "visible";
  document.getElementById("next").style.display =
    step === 6 ? "none" : "inline-block";
  document.getElementById("next").textContent =
    step === 5 ? "دیدن پیشنهادها" : "بعدی";
  if (step <= 5) refreshOptionAvailability();
  if (step === 5) renderSummary();
}
function renderSummary() {
  document.getElementById("answerSummary").innerHTML =
    `<b>انتخاب‌های تو:</b><br>سرمایه: ${labels.budget[answers.budget] || "—"} · فضا: ${labels.size[answers.size] || "—"} · مدل: ${labels.concept[answers.concept] || "—"} · سبک کار: ${labels.operation[answers.operation] || "—"} · ریسک: ${labels.risk[answers.risk] || "—"}`;
}
function zoneAdvice(z) {
  if (z.advice) return z.advice;
  if (z.id === "Z04")
    return "اول محور امام رضا–دریاسر–شمع‌جاران را بررسی کن؛ در مدل فعلی ترکیب تقاضا و فشار اجاره متعادل‌تر است.";
  if (z.id === "Z01")
    return "بازار جاافتاده‌تر است ولی اجاره بالاتر؛ فقط برای ملک با دید و دسترسی واقعاً خوب هزینه کن.";
  if (z.id === "Z02")
    return "در کریدور کریمی روی بر خیابان، دید مناسب و امکان توقف تمرکز کن.";
  if (z.id === "Z06")
    return "در کمربندی–امیررود–فرودگاه دسترسی خودرو، دلیوری و قیمت ملک مزیت دارد؛ تردد را حضوری چک کن.";
  if (z.id === "Z05")
    return "بازار کوچک‌تر است؛ ارزان بودن ملک به‌تنهایی کافی نیست و جریان مشتری همان نقطه مهم است.";
  return "پتانسیل دارد اما اطلاعات ملک این محدوده هنوز برای تصمیم قطعی کافی نیست.";
}
function conceptAdvice(c) {
  if (c.id === "delivery")
    return "ملک با دسترسی راحت پیک و اجاره منطقی؛ ویترین خیلی گران ضروری نیست.";
  if (c.id === "burger")
    return "ملک جمع‌وجور با ویترین واضح، دسترسی سریع و امکان بیرون‌بر.";
  if (c.id === "pizza")
    return "هود و اگزاست، برق/گاز و فضای آماده‌سازی خمیر را جدی‌تر از متراژ ببین.";
  if (c.id === "cafe")
    return "نور، دید و کیفیت فضای نشستن مهم است؛ ملک صرفاً ارزان کافی نیست.";
  return "آشپزخانه، هود، دسترسی خودرو و فضای نشستن اهمیت بیشتری دارد.";
}
function matchingProperties(row) {
  return propertyData.properties
    .filter((p) => p.zone_id === row.zone.id)
    .map((p) => {
      let fit = 0;
      if (p.area)
        fit += Math.max(0, 40 - Math.abs(p.area - row.concept.target) * 0.5);
      if (p.deposit + p.rent * 3 <= answers.budget * 0.4) fit += 25;
      if (/بر |دو دهنه|فست.?فود|امکانات کامل/.test(p.signal || "")) fit += 20;
      return { ...p, fit };
    })
    .sort((a, b) => b.fit - a.fit)
    .slice(0, 3);
}
function propertyHtml(row) {
  const props = matchingProperties(row);
  if (!props.length) return "";
  return `<div class="property-section"><h4>🏪 چند فایل ملک مرتبط برای شروع جست‌وجو</h4><div class="property-note">این فایل‌ها Lead هستند، نه توصیه قطعی. موجود بودن آگهی و قیمت را داخل دیوار دوباره کنترل کن؛ تا زمان تأیید تازه‌بودن وارد Benchmark جاری اجاره نمی‌شوند.</div><div class="property-list">${props.map((p) => `<a class="property-card" href="${p.url}" target="_blank" rel="noopener"><b>${p.title}</b><div class="price">رهن ${money(p.deposit)} · اجاره ${money(p.rent)} / ماه</div><small>${p.area ? `${fmt(p.area)} متر · ` : ""}${p.micro_area} · ${p.signal}</small></a>`).join("")}</div></div>`;
}
function sourceHtml() {
  const general = city.sources || [];
  return `<details><summary>🔗 منابع ملک و اجاره مورد استفاده</summary><div class="sources">${general.map((x) => `<a class="source" href="${esc(x.url)}" target="_blank" rel="noopener"><b>${esc(x.label)}</b><small>مشاهده منبع</small></a>`).join("")}</div><div class="sub">قیمت آگهی با اجاره قطعی قرارداد یکی نیست.</div></details>`;
}
function equipmentSizeBand() {
  return answers.size <= 60
    ? "small"
    : answers.size <= 120
      ? "medium"
      : "large";
}
function setupScale(concept) {
  return 0.65 + 0.35 * clamp(answers.size / concept.target, 0.55, 1.45);
}
function latinDigits(value) {
  return String(value || "")
    .replace(/[۰-۹]/g, (d) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(d)))
    .replace(/[٠-٩]/g, (d) => String("٠١٢٣٤٥٦٧٨٩".indexOf(d)));
}
function areaFromTitle(title) {
  const match = latinDigits(title).match(/(\d{2,4})\s*(?:متر|متری)/);
  return match ? Number(match[1]) : null;
}
function propertyFit(offer, row) {
  const rent = offer.price || 0,
    deposit = Number(offer.raw?.deposit_toman) || 0,
    commitment = deposit + 3 * rent,
    cap = answers.budget * 0.4,
    area = areaFromTitle(offer.title);
  let score =
    commitment <= cap ? 45 : clamp(45 - (45 * (commitment - cap)) / cap);
  if (area) score += clamp(30 - Math.abs(area - answers.size) * 0.55, 0, 30);
  else score += 10;
  const conceptTerms = {
    burger: /فست.?فود|رستوران|اغذیه|بر اصلی|دو دهنه/,
    pizza: /فست.?فود|رستوران|آشپزخانه|بر اصلی/,
    cafe: /کافه|تراس|حیاط|بر اصلی|دو دهنه/,
    iranian: /رستوران|آشپزخانه|حیاط|پارکینگ|بر اصلی/,
    delivery: /آشپزخانه|اغذیه|کمربندی|دسترسی|مغازه/,
  };
  if (conceptTerms[row.concept.id]?.test(offer.title)) score += 15;
  score += clamp((offer.raw?.image_count || 0) * 2, 0, 10);
  if (offer.placeholder) score -= 60;
  return { score: clamp(Math.round(score)), commitment, area };
}
function propertyFitLabel(score) {
  return score >= 75
    ? "تناسب بالا"
    : score >= 55
      ? "ارزش بررسی"
      : "تناسب محدود";
}
function propertyDetailText(details) {
  return [
    details.title,
    details.description,
    ...(details.amenities || []),
    ...(details.amenities_absent || []),
    ...(details.tags || []),
    ...(details.specs || []).flatMap((spec) => [spec.title, spec.value]),
  ]
    .filter(Boolean)
    .join(" · ");
}
function detailArea(details) {
  const row = (details.specs || []).find((spec) => /متراژ/.test(spec.title));
  const value = Number(latinDigits(row?.value).replace(/[^0-9.]/g, ""));
  return Number.isFinite(value) && value > 0
    ? value
    : areaFromTitle(details.title);
}
function assessPropertyReadiness(details, row) {
  const text = propertyDetailText(details),
    requirements = [
      ...PROPERTY_REQUIREMENTS.common,
      ...(PROPERTY_REQUIREMENTS[row.concept.id] || []),
    ],
    checks = requirements.map((requirement) => {
      const risk = requirement.negative?.test(text),
        confirmed = !risk && requirement.positive?.test(text);
      return {
        ...requirement,
        status: risk ? "risk" : confirmed ? "confirmed" : "unknown",
      };
    }),
    confirmed = checks.filter((item) => item.status === "confirmed").length,
    risks = checks.filter((item) => item.status === "risk").length,
    criticalUnknown = checks.filter(
      (item) => item.critical && item.status === "unknown",
    ).length,
    evidenceScore = clamp(
      Math.round((confirmed / checks.length) * 100 - risks * 15),
    );
  return { checks, confirmed, risks, criticalUnknown, evidenceScore };
}
function readinessLabel(assessment) {
  if (assessment.risks) return "دارای مانع یا هشدار صریح";
  if (assessment.evidenceScore >= 65 && assessment.criticalUnknown <= 1)
    return "آمادگی مستند نسبتاً خوب";
  if (assessment.evidenceScore >= 35) return "نیازمند راستی‌آزمایی حضوری";
  return "اطلاعات فنی آگهی ناکافی";
}
function requirementHtml(requirement) {
  const status = {
    confirmed: ["تأیید در متن آگهی", "confirmed"],
    risk: ["هشدار صریح", "risk"],
    unknown: ["نامشخص؛ باید پرسیده شود", "unknown"],
  }[requirement.status];
  return `<li class="requirement ${status[1]}"><div><b>${esc(requirement.label)}</b><small>${esc(requirement.question)}</small></div><span>${status[0]}</span></li>`;
}
function propertyAssessmentHtml(details, entry, row) {
  const assessment = assessPropertyReadiness(details, row),
    area = detailArea(details),
    rent = Number(details.monthly_rent_toman ?? details.price_toman) || 0,
    deposit = Number(details.deposit_toman) || 0,
    setupBudget = row.concept.setup * setupScale(row.concept),
    committed = deposit + 3 * rent + setupBudget,
    remaining = answers.budget - committed,
    expires = details.expires_at
      ? new Date(details.expires_at).toLocaleDateString("fa-IR")
      : "نامشخص",
    specs = (details.specs || [])
      .filter((spec) => !/ودیعه|اجاره/.test(spec.title))
      .slice(0, 6),
    seller =
      details.seller_type === "personal"
        ? "شخصی"
        : details.seller_type
          ? "کسب‌وکار / مشاور"
          : "نامشخص";
  return `<div class="readiness-head"><div><small>جمع‌بندی آمادگی فنی</small><b>${readinessLabel(assessment)}</b></div><strong>${fmt(assessment.evidenceScore)} از ۱۰۰ <small>پوشش شواهد آگهی</small></strong></div><div class="detail-facts"><div><small>متراژ ثبت‌شده</small><b>${area ? `${fmt(area)} متر` : "نامشخص"}</b></div><div><small>نوع آگهی‌دهنده</small><b>${seller}</b></div><div><small>اعتبار درج‌شده تا</small><b>${expires}</b></div><div><small>امکان چت</small><b>${details.chat_enabled ? "دارد" : "در داده فعلی ندارد"}</b></div></div>${specs.length ? `<div class="spec-strip">${specs.map((spec) => `<span>${esc(spec.title)}: <b>${esc(spec.value)}</b></span>`).join("")}</div>` : ""}<p class="property-description">${esc(details.description || "توضیحی در آگهی ثبت نشده است.")}</p><h6>شکاف فنی ملک با ${esc(row.concept.name)}</h6><ul class="requirement-list">${assessment.checks.map(requirementHtml).join("")}</ul><div class="capital-check ${remaining < 0 ? "over" : "safe"}"><b>آزمون سرمایه پس از انتخاب این ملک</b><span>ودیعه + ذخیره ۳ ماه اجاره + برآورد راه‌اندازی: ${money(committed)}</span><span>${remaining < 0 ? `کسری تقریبی ${money(Math.abs(remaining))}` : `مانده تقریبی ${money(remaining)}`}</span><small>این محاسبه قیمت‌گذاری پیمانکار نیست؛ هزینه رفع موارد نامشخص باید پس از بازدید جداگانه استعلام شود.</small></div><div class="property-actions"><a href="${esc(details.url || entry.offer.url)}" target="_blank" rel="noopener noreferrer">بازکردن آگهی در دیوار</a><span>${assessment.criticalUnknown ? `${fmt(assessment.criticalUnknown)} سؤال حیاتی هنوز بی‌پاسخ است` : "سؤال حیاتی بی‌پاسخ در متن پیدا نشد؛ بازدید همچنان لازم است"}</span></div>`;
}
async function loadPropertyAssessment(button, entry, row) {
  const target = document.getElementById(
    `property-detail-${entry.offer.id.replace(/[^a-zA-Z0-9_-]/g, "")}`,
  );
  if (!target || !window.RestaurantMarket) return;
  button.closest(".live-property")?.classList.add("expanded");
  button.disabled = true;
  button.textContent = "در حال خواندن جزئیات آگهی…";
  target.hidden = false;
  target.innerHTML =
    '<div class="coverage-note">مشخصات، توضیحات و امکانات ثبت‌شده در دیوار در حال بررسی است.</div>';
  try {
    let details = propertyDetailCache.get(entry.offer.id);
    if (!details) {
      details = await window.RestaurantMarket.getPropertyDetails(
        entry.offer.id,
      );
      propertyDetailCache.set(entry.offer.id, details);
    }
    target.innerHTML = propertyAssessmentHtml(details, entry, row);
    button.textContent = "به‌روزرسانی تحلیل فنی";
  } catch (error) {
    target.innerHTML = `<div class="live-error">جزئیات این آگهی فعلاً دریافت نشد: ${esc(error.message || error)}</div>`;
    button.textContent = "تلاش دوباره برای تحلیل";
  } finally {
    button.disabled = false;
  }
}
function renderLivePropertyCard(entry) {
  const { offer, fit } = entry,
    image = offer.image
      ? `<img src="${esc(offer.image)}" alt="" loading="lazy">`
      : "",
    rent = offer.price == null ? "اجاره نامشخص" : `اجاره ${money(offer.price)}`,
    deposit = offer.raw?.deposit_toman
      ? `رهن ${money(offer.raw.deposit_toman)}`
      : "رهن نامشخص";
  const detailId = `property-detail-${offer.id.replace(/[^a-zA-Z0-9_-]/g, "")}`;
  return `<article class="live-property">${image}<div class="live-property-body"><b>${esc(offer.title)}</b><span class="fit">${propertyFitLabel(fit.score)} · امتیاز اولیه ${fmt(fit.score)}</span><small>${deposit} · ${rent}${fit.area ? ` · ${fmt(fit.area)} متر` : ""}</small><small>${esc(offer.timeAgo || "زمان انتشار نامشخص")} · اطلاعات زنده دیوار</small><div class="property-card-actions"><a href="${esc(offer.url)}" target="_blank" rel="noopener noreferrer">دیدن آگهی</a><button data-property-token="${esc(offer.id)}">تحلیل فنی ملک</button></div></div><div class="property-detail" id="${detailId}" hidden></div></article>`;
}
async function renderLiveProperties(row, plannerKey) {
  const state = document.getElementById("livePropertyState"),
    grid = document.getElementById("livePropertyGrid");
  if (!state || !grid) return;
  if (!window.RestaurantMarket) {
    state.textContent = "اتصال بازار در دسترس نیست";
    return;
  }
  state.textContent = "در حال دریافت آگهی‌های زنده دیوار…";
  try {
    const result = await window.RestaurantMarket.searchProperties({
      city: city.divar_city,
      pages: 2,
      limit: 20,
    });
    if (plannerKey !== activePlannerKey) return;
    const ranked = result.items
      .filter((offer) => offer.url && !offer.placeholder)
      .map((offer) => ({ offer, fit: propertyFit(offer, row) }))
      .sort((a, b) => b.fit.score - a.fit.score)
      .slice(0, 6);
    state.textContent = `${fmt(result.candidates || result.items.length)} آگهی بررسی شد · ${new Date(result.collectedAt).toLocaleTimeString("fa-IR", { hour: "2-digit", minute: "2-digit" })}`;
    grid.innerHTML = ranked.length
      ? ranked.map(renderLivePropertyCard).join("")
      : '<div class="live-error">فعلاً آگهی قابل‌نمایشی پیدا نشد. چند دقیقه بعد دوباره امتحان کن.</div>';
    grid.querySelectorAll("[data-property-token]").forEach((button) => {
      const entry = ranked.find(
        (candidate) => candidate.offer.id === button.dataset.propertyToken,
      );
      if (entry)
        button.addEventListener("click", () =>
          loadPropertyAssessment(button, entry, row),
        );
    });
  } catch (error) {
    if (plannerKey !== activePlannerKey) return;
    state.textContent = "دریافت زنده ناموفق بود";
    grid.innerHTML = `<div class="live-error">اتصال به بازار زنده برقرار نشد. پیشنهادهای اصلی همچنان از مدل و داده ذخیره‌شده نمایش داده می‌شوند. ${esc(error.message || error)}</div>`;
  }
}
function offerWarning(offer, lane) {
  if (offer.placeholder) return offer.placeholderNote || "قیمت آگهی واقعی نیست";
  if (lane === "new" && /خانگی|اسباب.?بازی/.test(offer.title))
    return "این نتیجه احتمالاً خانگی است و با مشخصات حرفه‌ای پیشنهادی تطبیق کامل ندارد.";
  return "";
}
function offerHtml(offer, lane) {
  const warning = offerWarning(offer, lane),
    meta = [
      offer.city,
      offer.district,
      offer.seller,
      offer.rating ? `امتیاز ${fmt(offer.rating)}` : "",
    ]
      .filter(Boolean)
      .join(" · ");
  return `<a class="offer" href="${esc(offer.url)}" target="_blank" rel="noopener noreferrer"><b>${esc(offer.title)}</b><small>${offer.price == null ? "قیمت توافقی" : money(offer.price)}${meta ? ` · ${esc(meta)}` : ""}</small>${warning ? `<small class="warning">${esc(warning)}</small>` : ""}</a>`;
}
function offerColumn(title, lane, result) {
  if (result.error)
    return `<div class="offer-column"><h6>${title}</h6><div class="coverage-note">این منبع فعلاً پاسخ نداد؛ بعداً دوباره امتحان کن.</div></div>`;
  const items = (result.items || []).filter((x) => x.url).slice(0, 3);
  return `<div class="offer-column"><h6>${title}</h6>${items.length ? items.map((x) => offerHtml(x, lane)).join("") : '<div class="coverage-note">گزینه قابل‌اعتمادی در این بودجه پیدا نشد.</div>'}${lane === "new" ? '<div class="coverage-note">پوشش تجهیزات صنعتی در دیجی‌کالا کامل نیست؛ عنوان و مشخصات حرفه‌ای را دوباره کنترل کن.</div>' : result.marketMedian ? `<div class="coverage-note">میانه نمونه بازار: ${money(result.marketMedian)}</div>` : ""}</div>`;
}
async function loadEquipmentOffers(button, itemId, budget) {
  const item = equipmentData.items[itemId],
    target = document.getElementById(`offers-${itemId}`);
  if (!item || !target || !window.RestaurantMarket) return;
  button.disabled = true;
  button.textContent = "در حال جست‌وجوی دو بازار…";
  target.innerHTML =
    '<div class="coverage-note">آگهی‌های دست‌دوم دیوار و محصولات نوی دیجی‌کالا در حال بررسی‌اند.</div>';
  try {
    const result = await window.RestaurantMarket.searchEquipment(item, budget, city.used_market_cities);
    target.innerHTML = `<div class="offer-columns">${offerColumn("دست‌دوم · دیوار", "used", result.used)}${offerColumn("نو · دیجی‌کالا", "new", result.new)}</div><div class="coverage-note">قیمت‌ها پیشنهادی و لحظه‌ای‌اند. پیش از خرید، مدل دقیق، ظرفیت، سلامت فنی، هزینه حمل و نصب را تأیید کن.</div>`;
    button.textContent = "به‌روزرسانی پیشنهادها";
  } catch (error) {
    target.innerHTML = `<div class="live-error">جست‌وجوی بازار کامل نشد: ${esc(error.message || error)}</div>`;
    button.textContent = "تلاش دوباره";
  } finally {
    button.disabled = false;
  }
}
function equipmentCardHtml(entry, equipmentBudget) {
  const item = equipmentData.items[entry.id];
  if (!item) return "";
  const budget = Math.max(
      5000000,
      Math.round((equipmentBudget * entry.weight) / 5000000) * 5000000,
    ),
    band = equipmentSizeBand(),
    priority = entry.priority === "essential" ? "ضروری" : "تکمیل‌کننده";
  return `<article class="equipment-card"><div class="equipment-top"><span class="equipment-icon">${esc(item.icon)}</span><div><h5>${esc(item.name)}</h5><span class="policy">${priority} · ${esc(item.buy_label)}</span></div><div class="equipment-budget">سقف هدف ${money(budget)}</div></div><div class="equipment-spec"><b>مشخصات پایه:</b> ${esc(item.specs?.[band] || item.specs?.medium || "نیازمند بررسی")}</div><div class="equipment-check"><b>هنگام خرید:</b> ${esc(item.inspection)}</div><button class="market-btn" data-equipment-id="${esc(entry.id)}" data-equipment-budget="${budget}">دیدن گزینه‌های زنده نو و دست‌دوم</button><div class="offers" id="offers-${esc(entry.id)}"></div></article>`;
}
function renderLaunchIntelligence(row) {
  const root = document.getElementById("launchIntelligence"),
    kit = equipmentData.kits[row.concept.id];
  if (!root || !kit) {
    if (root) root.hidden = true;
    return;
  }
  const plannerKey = ++activePlannerKey,
    scale = setupScale(row.concept),
    setupBudget = row.concept.setup * scale,
    equipmentBudget = setupBudget * kit.equipment_share,
    fitoutBudget = setupBudget - equipmentBudget,
    monthlyRent = (row.zone.rent || 0) * answers.size,
    deposit = (row.zone.deposit || 0) * answers.size;
  root.hidden = false;
  root.innerHTML = `<div class="launch-head"><h3>نقشه راه‌اندازی: ملک + تجهیزات + سرمایه</h3><p>این سبد برای <b>${esc(row.concept.name)}</b> با فضای حدود <b>${fmt(answers.size)} متر</b> ساخته شده است. بودجه تجهیزات از همان برآورد سرمایه مدل جدا شده و دوباره روی جمع کل اضافه نشده است.</p></div><div class="budget-map"><div class="budget-cell"><small>ودیعه هدف در محدوده منتخب</small><b>${money(deposit)}</b></div><div class="budget-cell"><small>ذخیره سه ماه اجاره</small><b>${money(3 * monthlyRent)}</b></div><div class="budget-cell"><small>سبد هدف تجهیزات</small><b>${money(equipmentBudget)}</b></div><div class="budget-cell"><small>آماده‌سازی، مجوز و اقلام تکمیلی</small><b>${money(fitoutBudget)}</b></div></div><div class="live-block"><div class="live-title"><h4>🏪 ملک‌های زنده‌ای که الان ارزش بررسی دارند</h4><span class="live-state" id="livePropertyState">آماده اتصال به دیوار</span></div><div class="live-property-grid" id="livePropertyGrid"></div></div><div class="equipment-section"><h4>🧰 سبد پیشنهادی تجهیزات</h4><p class="equipment-intro">برای هر قلم، مشخصات پایه و سیاست خرید پیشنهاد شده است. دکمه هر کارت همان لحظه بازار نو و دست‌دوم را جست‌وجو می‌کند؛ نتیجه، سرنخ خرید است نه تأیید فنی.</p><div class="equipment-grid">${kit.items.map((entry) => equipmentCardHtml(entry, equipmentBudget)).join("")}</div></div><div class="source-strip">منابع زنده: آگهی‌های عمومی دیوار و کاتالوگ عمومی دیجی‌کالا از طریق MCPهای خواندنی و بدون ورود. قیمت آگهی معامله نهایی نیست؛ حذف آگهی هم الزاماً به معنی فروش نیست. خرید تجهیزات گاز، برق، برودت و فشار بدون بازدید متخصص توصیه نمی‌شود.</div>`;
  root
    .querySelectorAll("[data-equipment-id]")
    .forEach((button) =>
      button.addEventListener("click", () =>
        loadEquipmentOffers(
          button,
          button.dataset.equipmentId,
          Number(button.dataset.equipmentBudget),
        ),
      ),
    );
  renderLiveProperties(row, plannerKey);
}
function renderResults() {
  const top = evaluate(answers)
      .filter((x) => x.eligible)
      .slice(0, 5),
    overall = document.getElementById("overallReport"),
    list = document.getElementById("resultList");
  if (!top.length) {
    overall.innerHTML = "";
    document.getElementById("launchIntelligence").hidden = true;
    list.innerHTML = `<div class="result"><b>با این شرایط فعلاً در ${esc(city.name)} گزینه قابل‌عرضه‌ای نداریم.</b></div>`;
    renderCrossCity(null);
    return;
  }
  const first = top[0],
    second = top[1];
  overall.innerHTML = `<div class="overall"><h3>جمع‌بندی ساده</h3><p>با انتخاب‌های تو، فعلاً بهترین مسیر <b>${first.concept.name}</b> در محدوده <b>${first.zone.name}</b> است. ${second ? `گزینه دوم <b>${second.concept.name}</b> در <b>${second.zone.name}</b> است. ` : ""}بهتر است در دو محدوده اول چند ملک واقعی ذخیره کنی و بعد قیمت، امکانات فنی و تردد را مقایسه کنی. <a href="./properties.html?city=${city.id}">دیدن فایل‌های ملک ${city.name}</a></p></div>`;
  renderLaunchIntelligence(first);
  list.innerHTML = top
    .map((r, i) => {
      const status =
          r.score >= 80
            ? "مناسب برای بررسی جدی"
            : r.score >= 65
              ? "ارزش بررسی دارد"
              : "نیازمند احتیاط",
        cls = r.score >= 80 ? "good" : r.score >= 65 ? "ok" : "bad",
        why =
          r.coverage >= 1.5
            ? "تقاضای تقریبی منطقه فاصله خوبی با حداقل فروش لازم دارد."
            : r.coverage >= 1
              ? "تقاضای تقریبی فعلاً از حداقل فروش لازم بالاتر است، اما حاشیه اطمینان زیاد نیست."
              : "برای رسیدن به فروش سالم فشار بیشتری روی جذب مشتری داری.";
      return `<article class="result"><div class="result-top"><div class="rank">#${i + 1}</div><div><h3>${r.concept.emoji} ${r.concept.name}</h3><div class="sub">📍 ${r.zone.name}${r.zone.tag ? ` <span class="zone-tag">${esc(r.zone.tag)}</span>` : ""}</div></div><div class="status ${cls}">${status}</div></div><div class="cards"><div class="metric"><small>پول تقریبی لازم</small><b>${money(r.capital)}</b><div class="bar"><i style="width:${clamp(((answers.budget - r.capital) / answers.budget) * 100 + 55)}%"></i></div></div><div class="metric"><small>فروش روزانه لازم</small><b>حدود ${fmt(r.tickets)} سفارش</b></div><div class="metric"><small>تقاضای منطقه</small><b>${r.coverage >= 1.5 ? "قوی" : r.coverage >= 1 ? "قابل‌قبول" : "ضعیف"}</b></div></div><div class="advisor"><h4>🧭 راهنمای عملی این پیشنهاد</h4><div class="advisor-grid"><div class="advisor-box"><b>کجای شهر را اول بگردم؟</b><p>${zoneAdvice(r.zone)}</p></div><div class="advisor-box"><b>چه جور ملکی دنبالش باشم؟</b><p>${conceptAdvice(r.concept)}</p></div><div class="advisor-box"><b>چرا پیشنهاد شده؟</b><p>${why}</p></div><div class="advisor-box"><b>موقع بازدید ملک چه چیزهایی مهم است؟</b><p>هود و مسیر اگزاست، برق و گاز کافی، اجازه کتبی مالک برای فعالیت غذایی و امکان توقف مشتری یا پیک را بررسی کن.</p></div></div><div class="action"><b>قدم‌های بعدی</b><ol><li>۳ تا ۵ ملک در همین محدوده ذخیره کن.</li><li>رهن، اجاره، متراژ واقعی و امکانات فنی را مقایسه کن.</li><li>قبل از قرارداد در دو زمان شلوغ و یک زمان خلوت، ۳۰ دقیقه تردد واقعی اطراف ملک را ببین.</li></ol></div></div>${propertyHtml(r)}${sourceHtml()}</article>`;
    })
    .join("");
  renderCrossCity(first);
}
function crossCityReason(rows, a, forCity) {
  if (!rows.length) return "داده‌ای برای این انتخاب‌ها نیست.";
  const affordable = rows.some((r) => r.capital <= a.budget);
  if (!affordable) return "با این سرمایه در این شهر مسیری پیدا نشد.";
  if (forCity.zones.every((z) => z.confidence < riskThreshold(a.risk)))
    return "داده این شهر برای این سطح ریسک هنوز کافی نیست؛ با ریسک «متوسط» یا «زیاد» امتحان کن.";
  return "با این ترکیب انتخاب‌ها گزینه قابل‌عرضه‌ای نماند.";
}
function deltaText(value, base, unit) {
  if (!base) return "";
  const diff = value - base;
  if (Math.abs(diff) / base < 0.05) return '<span class="delta same">تقریباً برابر</span>';
  const txt = unit === "money" ? money(Math.abs(diff)) : `${fmt(Math.abs(diff))} سفارش`;
  return diff < 0
    ? `<span class="delta better">${txt} کمتر</span>`
    : `<span class="delta worse">${txt} بیشتر</span>`;
}
function renderCrossCity(base) {
  const root = document.getElementById("crossCity");
  if (!root) return;
  const others = cityOrder.filter((id) => id !== city.id);
  if (!others.length) {
    root.hidden = true;
    root.innerHTML = "";
    return;
  }
  const cards = others.map((id) => {
    const other = CITIES[id],
      rows = evaluate(answers, other),
      best = rows.find((r) => r.eligible);
    const head = `<div class="xc-head"><b>${esc(other.emoji || "📍")} ${esc(other.name)}</b><span class="quality q-${esc(other.quality)}">${esc(other.quality_label || "")}</span></div>`;
    if (!best)
      return `<article class="xc-card muted">${head}<p>${crossCityReason(rows, answers, other)}</p></article>`;
    return `<article class="xc-card">${head}<p class="xc-pick">${best.concept.emoji} <b>${esc(best.concept.name)}</b> در ${esc(best.zone.name)}${best.zone.tag ? ` <span class="zone-tag">${esc(best.zone.tag)}</span>` : ""}</p><dl class="xc-metrics"><div><dt>پول تقریبی لازم</dt><dd>${money(best.capital)}</dd>${base ? deltaText(best.capital, base.capital, "money") : ""}</div><div><dt>اجاره ماهانه برآوردی</dt><dd>${money(best.monthlyRent)}</dd>${base ? deltaText(best.monthlyRent, base.monthlyRent, "money") : ""}</div><div><dt>فروش روزانه لازم</dt><dd>حدود ${fmt(Math.round(best.tickets))} سفارش</dd>${base ? deltaText(best.tickets, base.tickets, "orders") : ""}</div></dl><button class="btn secondary xc-go" data-city-go="${esc(id)}">دیدن نتیجه کامل در ${esc(other.name)}</button></article>`;
  });
  const title = base
    ? "همین انتخاب‌ها در شهرهای دیگر"
    : `در ${esc(city.name)} نشد؛ در شهرهای دیگر چطور؟`,
    lead = base
      ? `مقایسه با گزینه اول تو در ${esc(city.name)} (${esc(base.concept.name)}، ${esc(base.zone.name)}).`
      : "با همین سرمایه، متراژ، مدل و سطح ریسک.";
  root.hidden = false;
  root.innerHTML = `<div class="xc-title"><h3>🗺️ ${title}</h3><p>${lead}</p></div><div class="xc-grid">${cards.join("")}</div><p class="xc-note">بازار هر شهر فرق دارد (مثلاً نوشهر فصلی و توریستی است و مشهد بازار زائر دارد). «تقاضای منطقه» هر شهر نسبت به محله‌های همان شهر سنجیده می‌شود، پس این‌جا فقط پول، اجاره و فروش لازم را کنار هم گذاشته‌ایم. هزینه راه‌اندازی، میانگین فاکتور و حقوق فعلاً برای همه شهرها یکسان فرض شده است.</p>`;
  root.querySelectorAll("[data-city-go]").forEach((btn) =>
    btn.addEventListener("click", () =>
      setCity(btn.dataset.cityGo, { keepAnswers: true }),
    ),
  );
}
document.querySelectorAll("[data-key]").forEach((group) => {
  const key = group.dataset.key;
  group.querySelectorAll(".option").forEach((btn) =>
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      group
        .querySelectorAll(".option")
        .forEach((x) => x.classList.remove("active"));
      btn.classList.add("active");
      answers[key] = ["budget", "size"].includes(key)
        ? Number(btn.dataset.value)
        : btn.dataset.value;
      refreshOptionAvailability();
      if (step === 5) renderSummary();
    }),
  );
});
document.getElementById("next").addEventListener("click", () => {
  const key = stepKey[step];
  if (!answers[key]) {
    alert("یکی از گزینه‌های فعال را انتخاب کن.");
    return;
  }
  if (step === 5) {
    renderResults();
    step = 6;
  } else step++;
  showStep();
});
document.getElementById("prev").addEventListener("click", () => {
  if (step > 1) {
    step--;
    showStep();
  }
});
function resetWizard() {
  answers = {};
  document
    .querySelectorAll(".option")
    .forEach((x) => x.classList.remove("active"));
  step = 1;
  showStep();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document.getElementById("restart").addEventListener("click", resetWizard);
const normalizeFa = (t) =>
  String(t || "")
    .replace(/ي/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/\u200c/g, " ")
    .trim()
    .toLowerCase();
function renderCityList(filter = "") {
  const list = document.getElementById("cityList");
  const q = normalizeFa(filter);
  const ids = cityOrder.filter(
    (id) =>
      !q ||
      normalizeFa(`${CITIES[id].name} ${CITIES[id].province || ""} ${id}`).includes(q),
  );
  list.innerHTML = ids.length
    ? ids
        .map((id) => {
          const c = CITIES[id];
          return `<li><button role="option" aria-selected="${c === city}" data-city="${esc(id)}" class="${c === city ? "active" : ""}"><span>${esc(c.emoji || "📍")} <b>${esc(c.name)}</b><small>${esc(c.province || "")}</small></span><span class="quality q-${esc(c.quality)}">${esc(c.quality_label || "")}</span></button></li>`;
        })
        .join("")
    : '<li class="empty">شهری با این نام هنوز اضافه نشده است.</li>';
  list.querySelectorAll("[data-city]").forEach((btn) =>
    btn.addEventListener("click", () => {
      closeCityPanel();
      setCity(btn.dataset.city);
    }),
  );
}
function openCityPanel() {
  const panel = document.getElementById("cityPanel"),
    search = document.getElementById("citySearch");
  panel.hidden = false;
  document.getElementById("cityButton").setAttribute("aria-expanded", "true");
  search.value = "";
  renderCityList();
  search.focus();
}
function closeCityPanel() {
  document.getElementById("cityPanel").hidden = true;
  document.getElementById("cityButton").setAttribute("aria-expanded", "false");
}
function applyCityText() {
  document.querySelectorAll("[data-city-name]").forEach((el) => {
    el.textContent = city.name;
  });
  document.getElementById("resultsNote").textContent = city.data_note || "";
  const notice = document.getElementById("cityNotice");
  notice.hidden = !city.notice;
  notice.textContent = city.notice || "";
  document.title = `رستوران‌نما — امکان‌سنجی رستوران در ${city.name}`;
  document.getElementById("cityButtonName").textContent =
    `${city.emoji || ""} ${city.name}`.trim();
  const quality = document.getElementById("cityQuality");
  quality.textContent = city.quality_label || "";
  quality.className = `quality q-${city.quality}`;
  document.getElementById("cityCount").textContent = `${fmt(cityOrder.length)} شهر`;
}
function markAnswers() {
  document.querySelectorAll("[data-key]").forEach((group) => {
    group.querySelectorAll(".option").forEach((btn) => {
      const v = ["budget", "size"].includes(group.dataset.key)
        ? Number(btn.dataset.value)
        : btn.dataset.value;
      btn.classList.toggle("active", answers[group.dataset.key] === v);
    });
  });
}
async function setCity(id, { keepAnswers = false } = {}) {
  if (!CITIES[id] || CITIES[id] === city) return;
  useCity(id);
  propertyDetailCache = new Map();
  activePlannerKey++;
  try {
    const url = new URL(location.href);
    url.searchParams.set("city", id);
    history.replaceState(null, "", url);
  } catch {}
  applyCityText();
  try {
    propertyData = await loadCityProperties();
  } catch (error) {
    propertyData = { meta: null, properties: [] };
    console.warn("Property data unavailable", error);
  }
  if (keepAnswers && stepKey && Object.values(stepKey).every((k) => answers[k] !== undefined)) {
    markAnswers();
    renderResults();
    step = 6;
    showStep();
    document.querySelector(".results-head")?.scrollIntoView({ behavior: "smooth" });
  } else resetWizard();
}
document.getElementById("cityButton").addEventListener("click", () => {
  if (document.getElementById("cityPanel").hidden) openCityPanel();
  else closeCityPanel();
});
document
  .getElementById("citySearch")
  .addEventListener("input", (e) => renderCityList(e.target.value));
document.addEventListener("click", (e) => {
  if (!e.target.closest(".city-picker")) closeCityPanel();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeCityPanel();
});
loadPlannerData()
  .then(applyCityText)
  .catch((error) => {
    console.error(error);
    document.getElementById("cityNotice").hidden = false;
    document.getElementById("cityNotice").textContent =
      "داده شهرها بارگذاری نشد. صفحه را دوباره باز کن.";
  })
  .finally(() => city && showStep());
