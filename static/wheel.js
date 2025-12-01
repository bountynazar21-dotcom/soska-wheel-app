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
 * Порядок секторів ПО КОЛУ, починаючи з ВЕРХУ (12:00)
 * і далі за годинниковою стрілкою.
 * ТЕКСТИ МАЮТЬ СПІВПАДАТИ з PRIZES_WEIGHTS у config.py
 */
const sectors = [
  { label: "Аромакомпозиції x5" },
  { label: "Відкривачок x10" },
  { label: "Ланцюжок + кліп-холдер x6" },
  { label: "Стікери + ручка x20" },
  { label: "Павучки x45" },
  { label: "Стрічки + пахучки x30" },
  { label: "Стрічки x55" },
  { label: "Стікери x70" }
];

// кут одного сектора
const SECTOR_ANGLE = 360 / sectors.length;

// якщо поінтер трохи “зʼїхав” між секторами – можна змінити це значення
const ANGLE_OFFSET = 0;

/** Запит до бекенда */
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

  // Дані юзера з Telegram WebApp (опціонально)
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

  // 1) Отримуємо приз з бекенда
  const { prize, repeat, message } = await spinRequest(payload);

  // 2) Знаходимо сектор з таким призом
  let sectorIndex = sectors.findIndex((s) => s.label === prize);

  if (sectorIndex === -1) {
    console.warn("Prize not matched to sectors, using random sector:", prize);
    sectorIndex = Math.floor(Math.random() * sectors.length);
  }

  // Центр сектора, куди має дивитися поінтер
  const sectorCenterAngle = sectorIndex * SECTOR_ANGLE + ANGLE_OFFSET;

  // Додаємо кілька повних обертів
  const extraSpins = 3 + Math.floor(Math.random() * 3); // 3..5 обертів
  const finalDeg = extraSpins * 360 + sectorCenterAngle;

  // Скидаємо старий transition, щоб не було ривків
  pointerRotator.style.transition = "none";

  requestAnimationFrame(() => {
    pointerRotator.style.transition =
      "transform 4s cubic-bezier(.33,1,.68,1)";
    pointerRotator.style.transform = `rotate(${finalDeg}deg)`;
  });

  const onEnd = (e) => {
    if (e.target !== pointerRotator) return;
    pointerRotator.removeEventListener("transitionend", onEnd);

    // Текст під кнопкою
    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    // Салют з тим самим призом
    showFireworks(prize);

    spinning = false;
    btn.disabled = false;
  };

  pointerRotator.addEventListener("transitionend", onEnd);
});

