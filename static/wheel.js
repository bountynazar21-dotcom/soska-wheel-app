const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const res = document.getElementById("result");
const pointerRotator = document.getElementById("pointer-rotator");
const fireworks = document.getElementById("fireworks");
const fireworksText = document.getElementById("fireworks-text");

let spinning = false;
let currentRotation = 0;

const sectors = [
  "Смартфон",
  "Ноутбук",
  "Наушники",
  "Велосипед",
  "Часы",
  "Книга",
  "Кофе",
  "Торт"
];

const SECTOR_ANGLE = 360 / sectors.length;

// Стрілка вже стоїть зверху і дивиться вниз на сектор
const POINTER_OFFSET = 0;

async function spinRequest(payload) {
  try {
    const r = await fetch("/spin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    return await r.json();
  } catch (e) {
    console.error(e);
    return {
      prize: "Помилка. Спробуй ще раз пізніше.",
      sector_index: 0,
      repeat: false,
      message: ""
    };
  }
}

function showFireworks(text) {
  if (!fireworks || !fireworksText) return;

  fireworksText.textContent = `🎉 ${text} 🎉`;
  fireworks.classList.add("show");

  setTimeout(() => {
    fireworks.classList.remove("show");
  }, 2000);
}

function normalizeAngle(angle) {
  return ((angle % 360) + 360) % 360;
}

btn.addEventListener("click", async () => {
  if (spinning) return;

  spinning = true;
  btn.disabled = true;
  res.textContent = "Крутимо...";

  let username = "unknown";
  let user_id = null;

  if (tg?.initDataUnsafe?.user) {
    const u = tg.initDataUnsafe.user;

    username =
      u.username ||
      `${u.first_name || ""} ${u.last_name || ""}`.trim() ||
      "user";

    user_id = u.id;
  }

  const data = await spinRequest({ username, user_id });
  const { prize, sector_index, repeat, message } = data;

  let sectorIndex = 0;

  if (typeof sector_index === "number" && sector_index >= 0) {
    sectorIndex = sector_index % sectors.length;
  } else {
    const idx = sectors.indexOf(prize);
    sectorIndex = idx !== -1 ? idx : 0;
    console.warn("Prize not matched, using fallback sector:", prize);
  }

  const targetAngle =
    sectorIndex * SECTOR_ANGLE + SECTOR_ANGLE / 2 + POINTER_OFFSET;

  const extraSpins = 5;
  const baseRotation = normalizeAngle(currentRotation);

  let delta = normalizeAngle(targetAngle) - baseRotation;
  if (delta < 0) delta += 360;

  const finalDeg = Math.round(currentRotation + extraSpins * 360 + delta);
  currentRotation = finalDeg;

  pointerRotator.style.transition = "none";
  pointerRotator.style.transform =
    `rotate(${Math.round(baseRotation)}deg) translateZ(0)`;

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      pointerRotator.style.transition =
        "transform 4.2s cubic-bezier(0.16, 1, 0.3, 1)";
      pointerRotator.style.transform =
        `rotate(${finalDeg}deg) translateZ(0)`;
    });
  });

  const onEnd = (e) => {
    if (e.target !== pointerRotator) return;

    pointerRotator.removeEventListener("transitionend", onEnd);

    res.textContent = repeat
      ? `${message || "Ви вже крутили колесо."} Ваш приз: ${prize}`
      : `Вітаємо! Ви виграли: ${prize}`;

    showFireworks(prize);

    spinning = false;
    btn.disabled = false;
  };

  pointerRotator.addEventListener("transitionend", onEnd);
});