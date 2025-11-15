const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const wheel = document.getElementById("wheel");
const res = document.getElementById("result");
const fireworks = document.getElementById("fireworks");
const fireworksText = document.getElementById("fireworks-text");

// ПОРЯДОК ПРИЗІВ = ПОРЯДОК СЕКТОРІВ НА КАРТИНЦІ (зверху і далі за годинниковою)
const sectors = [
  { label: "Рідина Punch" },  // верхній сектор під стрілкою
  { label: "Знижка 31%" },
  { label: "Pod система" },
  { label: "Мерч Soska Bar" },
  { label: "Дві рідини" },
  { label: "Картридж" },
  { label: "Нічого 😅" },
  { label: "Сюрприз" }
];

const sectorAngle = 360 / sectors.length;
const POINTER_OFFSET = 90;  // стрілка зверху
let spinning = false;

function showFireworks(text) {
  if (!fireworks || !fireworksText) return;
  fireworksText.textContent = text;
  fireworks.classList.add("show");
  setTimeout(() => fireworks.classList.remove("show"), 2000);
}

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
  const { prize, repeat, message } = await spinRequest(payload);

  // шукаємо сектор з таким самим текстом, як повернув бекенд
  let sectorIndex = sectors.findIndex((s) => s.label === prize);
  if (sectorIndex === -1) {
    // якщо бекенд віддав щось інше – просто рандомний сектор
    sectorIndex = Math.floor(Math.random() * sectors.length);
  }

  const targetAngle = sectorIndex * sectorAngle + sectorAngle / 2;
  const rotation = 360 * 5 + (POINTER_OFFSET - targetAngle);

  // скидаємо кут
  wheel.style.transition = "none";
  wheel.style.transform = "rotate(0deg)";

  requestAnimationFrame(() => {
    wheel.style.transition = "transform 4s cubic-bezier(.33,1,.68,1)";
    wheel.style.transform = `rotate(${rotation}deg)`;
  });

  const onFinish = () => {
    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    showFireworks(`🎉 ${prize} 🎉`);

    spinning = false;
    btn.disabled = false;
    wheel.removeEventListener("transitionend", onFinish);
  };

  wheel.addEventListener("transitionend", onFinish, { once: true });
});
