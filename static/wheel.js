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

/**
 * Той самий порядок, що й у PRIZES_WEIGHTS у config.py:
 * 0 – верхній сектор, далі за годинниковою.
 */
const sectors = [
  "Відкривачок x10",
  "Ланцюжок + кліп-холдер x6",
  "Стікери + ручка x20",
  "Стрічки + пахучки x30",
  "Павучки x45",
  "Стрічки x55",
  "Стікери x70",
  "Аромакомпозиції x5"
];

const SECTOR_ANGLE = 360 / sectors.length;
// якщо поінтер трохи не по центру сектора — можна підкрутити
const ANGLE_OFFSET = 0;

/** запит до бекенда */
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
    return { prize: "Помилка. Спробуй ще раз пізніше." };
  }
}

function showFireworks(text) {
  if (!fireworks || !fireworksText) return;
  fireworksText.textContent = `🎉 ${text} 🎉`;
  fireworks.classList.add("show");
  setTimeout(() => fireworks.classList.remove("show"), 2000);
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

  const payload = { username, user_id };

  // 1) тягнемо результат із бекенда
  const data = await spinRequest(payload);
  const { prize, sector_index, repeat, message } = data;

  // 2) визначаємо індекс сектора
  let sectorIndex = null;

  if (typeof sector_index === "number" && sector_index >= 0) {
    sectorIndex = sector_index % sectors.length;
  } else {
    // fallback: шукаємо по тексту
    const idx = sectors.indexOf(prize);
    if (idx !== -1) {
      sectorIndex = idx;
    } else {
      sectorIndex = Math.floor(Math.random() * sectors.length);
      console.warn("Prize not matched, using random sector:", prize);
    }
  }

  // центр сектора, куди має дивитись поінтер
  const sectorCenterAngle = sectorIndex * SECTOR_ANGLE + ANGLE_OFFSET;

  // кілька повних обертів + сектор
  const extraSpins = 3 + Math.floor(Math.random() * 3); // 3..5
  const finalDeg = extraSpins * 360 + sectorCenterAngle;

  // скидаємо старий transition
  pointerRotator.style.transition = "none";

  requestAnimationFrame(() => {
    pointerRotator.style.transition =
      "transform 4s cubic-bezier(.33,1,.68,1)";
    pointerRotator.style.transform = `rotate(${finalDeg}deg)`;
  });

  const onEnd = (e) => {
    if (e.target !== pointerRotator) return;
    pointerRotator.removeEventListener("transitionend", onEnd);

    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    showFireworks(prize);

    spinning = false;
    btn.disabled = false;
  };

  pointerRotator.addEventListener("transitionend", onEnd);
});

