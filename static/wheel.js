const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const wheel = document.getElementById("wheel");
const res = document.getElementById("result");

let spinning = false;

async function spinRequest(payload) {
  try {
    const r = await fetch("/spin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return await r.json();
  } catch (e) {
    console.error(e);
    return { prize: "Помилка. Спробуй ще раз пізніше." };
  }
}

btn.addEventListener("click", async () => {
  if (spinning) return;
  spinning = true;
  btn.disabled = true;
  res.textContent = "Крутимо...";

  // Дані користувача з Telegram WebApp
  let username = "unknown";
  let user_id = null;

  if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    username =
      tg.initDataUnsafe.user.username ||
      `${tg.initDataUnsafe.user.first_name || ""} ${
        tg.initDataUnsafe.user.last_name || ""
      }`.trim() ||
      "user";
    user_id = tg.initDataUnsafe.user.id;
  }

  // Номер чеку — для MVP можна через prompt
  const check = prompt("Введи номер чеку (або залиш порожнім):") || "demo";

  // Анімація колеса
  const extraSpins = 5; // кількість повних обертів
  const randomDeg = Math.floor(Math.random() * 360);
  const finalDeg = 360 * extraSpins + randomDeg;

  wheel.style.transition = "transform 4s cubic-bezier(.33,1,.68,1)";
  wheel.style.transform = `rotate(${finalDeg}deg)`;

  // Паралельно шлемо запит на бекенд
  const payload = { username, user_id, check };
  const promise = spinRequest(payload);

  // Чекаємо поки докрутиться
  setTimeout(async () => {
    const { prize, repeat, message } = await promise;

    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    spinning = false;
    btn.disabled = false;
  }, 4200);
});
