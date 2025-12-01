const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const pointerRotator = document.getElementById("pointer-rotator");
const res = document.getElementById("result");
const fireworks = document.getElementById("fireworks");
const fireworksText = document.getElementById("fireworks-text");

// Порядок секторів = порядок на картинці, за годинниковою, від ВЕРХУ
const sectors = [
  "Аромакомпозиції x5",
  "Відкривачок x10",
  "Ланцюжок + кліп-холдер x6",
  "Стікери + ручка x20",
  "Павучки x45",
  "Стрічки x55",
  "Стікери x70",
  "Стрічки + пахучки x30",
];

const sectorAngle = 360 / sectors.length;

let spinning = false;
let idle = true;
let idleAngle = 0;
let idleTimer = null;

function startIdleSpin() {
  idle = true;
  if (idleTimer) return;

  idleTimer = setInterval(() => {
    if (!idle || !pointerRotator) return;
    idleAngle = (idleAngle + 0.5) % 360;
    pointerRotator.style.transition = "none";
    pointerRotator.style.transform = `rotate(${idleAngle}deg)`;
  }, 40);
}

function stopIdleSpin() {
  idle = false;
  if (idleTimer) {
    clearInterval(idleTimer);
    idleTimer = null;
  }
}

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

  stopIdleSpin();

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

  let sectorIndex = sectors.findIndex((name) => name === prize);
  if (sectorIndex === -1) {
    sectorIndex = Math.floor(Math.random() * sectors.length);
  }

  const targetAngle = sectorIndex * sectorAngle + sectorAngle / 2;
  const extraSpins = 5;
  const finalRotation = 360 * extraSpins + targetAngle;

  if (!pointerRotator) {
    console.error("pointer-rotator not found");
    res.textContent = prize;
    spinning = false;
    btn.disabled = false;
    startIdleSpin();
    return;
  }

  // фіксуємо поточний idle-кут
  pointerRotator.style.transition = "none";
  pointerRotator.style.transform = `rotate(${idleAngle}deg)`;

  requestAnimationFrame(() => {
    pointerRotator.style.transition = "transform 4s cubic-bezier(.33,1,.68,1)";
    pointerRotator.style.transform = `rotate(${finalRotation}deg)`;
  });

  const onFinish = () => {
    idleAngle = finalRotation % 360;

    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    showFireworks(`🎉 ${prize} 🎉`);

    spinning = false;
    btn.disabled = false;

    pointerRotator.removeEventListener("transitionend", onFinish);
    startIdleSpin();
  };

  pointerRotator.addEventListener("transitionend", onFinish, { once: true });
});

// запускаємо ідл-обертання поінтера
startIdleSpin();
