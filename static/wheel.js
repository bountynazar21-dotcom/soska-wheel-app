const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const wheel = document.getElementById("wheel");
const wheelContainer = document.querySelector(".wheel-container");
const res = document.getElementById("result");
const centerText = document.getElementById("wheel-center-text");
const fireworks = document.getElementById("fireworks");
const fireworksText = document.getElementById("fireworks-text");

// 👉 СПИСОК СЕКТОРІВ / ПРИЗІВ
// ВАЖЛИВО: назви label повинні збігатися з тим, що бекенд повертає в `prize`
const sectors = [
  { label: "Рідина Punch" },
  { label: "Знижка 31%" },
  { label: "Pod система" },
  { label: "Мерч Soska Bar" },
  { label: "Дві рідини" },
  { label: "Картридж" },
  { label: "Нічого 😅" },
  { label: "Сюрприз" }
];

const sectorAngle = 360 / sectors.length;
// Стрілка зверху, а 0° для rotate — це “направо”, тому використовуємо офсет
const POINTER_OFFSET = 90;

let spinning = false;

/**
 * Додаємо підписи секторів по колу
 */
function renderSectorLabels() {
  if (!wheelContainer) return;

  sectors.forEach((sector, i) => {
    const label = document.createElement("div");
    label.className = "sector-label";
    label.textContent = sector.label;

    // центр сектору відносно 0°
    const angle = i * sectorAngle + sectorAngle / 2;

    // крутимо навколо центру кола, зсув до краю, потім повертаємо текст назад
    label.style.transform = `
      rotate(${angle - POINTER_OFFSET}deg)
      translate(0, -42%)
      rotate(${-(angle - POINTER_OFFSET)}deg)
    `;

    wheelContainer.appendChild(label);
  });
}

renderSectorLabels();

/**
 * Запит до бекенда
 */
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

/**
 * Показ салюту з текстом
 */
function showFireworks(text) {
  if (!fireworks || !fireworksText) return;
  fireworksText.textContent = text;
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
  if (centerText) centerText.textContent = "Крутимо...";

  // Дані юзера з Telegram WebApp
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

  const check = prompt("Введи номер чеку (або залиш порожнім):") || "demo";
  const payload = { username, user_id, check };

  // 1️⃣ Спочатку дізнаємось, який приз видав бекенд
  const { prize, repeat, message } = await spinRequest(payload);

  // 2️⃣ Знаходимо сектор із таким призом
  let sectorIndex = sectors.findIndex((s) => s.label === prize);
  if (sectorIndex === -1) {
    // Якщо бекенд повернув назву, якої немає у sectors — рулетка рандомна
    sectorIndex = Math.floor(Math.random() * sectors.length);
  }

  const sectorCenterAngle =
    sectorIndex * sectorAngle + sectorAngle / 2; // центр сектору в градусах

  // Кут, щоб стрілка зверху зупинилась на центрі цього сектору
  // Формула: хочемо, щоб (sectorCenterAngle + rotation) ≡ POINTER_OFFSET (mod 360)
  // => rotation ≡ POINTER_OFFSET - sectorCenterAngle (mod 360)
  const baseRot = (POINTER_OFFSET - sectorCenterAngle + 360) % 360;
  const extraSpins = 5; // повні оберти для краси
  const finalDeg = 360 * extraSpins + baseRot;

  // Скидаємо попередню анімацію
  wheel.style.transition = "none";
  wheel.style.transform = `rotate(0deg)`;

  // Даємо браузеру кадр, потім крутимо
  requestAnimationFrame(() => {
    wheel.style.transition = "transform 4s cubic-bezier(.33,1,.68,1)";
    wheel.style.transform = `rotate(${finalDeg}deg)`;
  });

  // 3️⃣ Коли анімація закінчилась — показуємо приз, салют, розлочуємо кнопку
  const onEnd = () => {
    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    if (centerText) {
      centerText.textContent = prize;
    }

    showFireworks(`🎉 ${prize} 🎉`);

    spinning = false;
    btn.disabled = false;
    wheel.removeEventListener("transitionend", onEnd);
  };

  wheel.addEventListener("transitionend", onEnd);
});
