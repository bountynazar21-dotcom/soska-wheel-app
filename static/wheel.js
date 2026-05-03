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

// pointer.svg дивиться вниз.
// Якщо буде маленький зсув — пробуй 175 або 185.
const ANGLE_OFFSET = 180;

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
      sector_index: 0
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

  const data = await spinRequest(payload);
  const { prize, sector_index, repeat, message } = data;

  let sectorIndex = null;

  if (typeof sector_index === "number" && sector_index >= 0) {
    sectorIndex = sector_index % sectors.length;
  } else {
    const idx = sectors.indexOf(prize);

    if (idx !== -1) {
      sectorIndex = idx;
    } else {
      sectorIndex = 0;
      console.warn("Prize not matched, using sector 0:", prize);
    }
  }

  const sectorCenterAngle =
    sectorIndex * SECTOR_ANGLE + SECTOR_ANGLE / 2 + ANGLE_OFFSET;

  const extraSpins = 4 + Math.floor(Math.random() * 2);

  const baseRotation = ((currentRotation % 360) + 360) % 360;
  let delta = sectorCenterAngle - baseRotation;

  if (delta < 0) {
    delta += 360;
  }

  const finalDeg = currentRotation + extraSpins * 360 + delta;
  currentRotation = finalDeg;

  pointerRotator.style.transition = "none";
  pointerRotator.style.transform = `rotate(${baseRotation}deg)`;

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      pointerRotator.style.transition =
        "transform 4s cubic-bezier(.33,1,.68,1)";
      pointerRotator.style.transform = `rotate(${Math.round(finalDeg)}deg)`;
    });
  });

  const onEnd = (e) => {
    if (e.target !== pointerRotator) return;

    pointerRotator.removeEventListener("transitionend", onEnd);

    if (repeat) {
      res.textContent = `${message || ""} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    showFireworks(prize);

    spinning = false;
    btn.disabled = false;
  };

  pointerRotator.addEventListener("transitionend", onEnd);
});
