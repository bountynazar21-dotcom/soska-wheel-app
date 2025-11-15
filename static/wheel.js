const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

const btn = document.getElementById("spinBtn");
const wheelContainer = document.querySelector(".wheel-container");
const res = document.getElementById("result");
const fireworks = document.getElementById("fireworks");
const fireworksText = document.getElementById("fireworks-text");

// 👉 СПИСОК ПРИЗІВ (має збігатися з PRIZES у бекенді)
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
const POINTER_OFFSET = 90; // 90° бо стрілка зверху
let spinning = false;

/**
 * Малюємо назви призів по колу
 */
function renderSectorLabels() {
  if (!wheelContainer) return;

  const radius = 105; // як далеко від центру текст (підберемо під дизайн)

  sectors.forEach((sector, index) => {
    const label = document.createElement("div");
    label.className = "sector-label";
    label.textContent = sector.label;

    const angle = index * sectorAngle + sectorAngle / 2;

    label.style.transform = `
      rotate(${angle}deg)
      translate(0, -${radius}px)
      rotate(${-angle}deg)
    `;

    wheelContainer.appendChild(label);
  });
}

renderSectorLabels();

/**
 * Запит на бекенд
 */
async function spinRequest(payload) {
  try {
    const r = await fetch("/spin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return await r.json();
  } catch (err) {
    console.error(err);
    return { prize: "Помилка" };
  }
}

/**
 * Салют
 */
function showFireworks(text) {
  if (!fireworks || !fireworksText) return;
  fireworksText.textContent = text;
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
    username = u.username || `${u.first_name || ""} ${u.last_name || ""}`.trim();
    user_id = u.id;
  }

  const payload = { username, user_id };

  // Дізнаємось результат
  const { prize, repeat, message } = await spinRequest(payload);

  // Знаходимо сектор
  let sectorIndex = sectors.findIndex((s) => s.label === prize);
  if (sectorIndex === -1) sectorIndex = Math.floor(Math.random() * sectors.length);

  const targetAngle = sectorIndex * sectorAngle + sectorAngle / 2;

  // Кут щоб стрілка показала приз (стрілка в 90°)
  const rotation = 360 * 5 + (POINTER_OFFSET - targetAngle);

  // Скидаємо попередній стан
  wheelContainer.style.transition = "none";
  wheelContainer.style.transform = "rotate(0deg)";

  requestAnimationFrame(() => {
    wheelContainer.style.transition = "transform 4.2s cubic-bezier(.33,1,.68,1)";
    wheelContainer.style.transform = `rotate(${rotation}deg)`;
  });

  const onFinish = () => {
    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `🎉 Ви виграли: ${prize}`;
    }

    showFireworks(prize);

    spinning = false;
    btn.disabled = false;

    wheelContainer.removeEventListener("transitionend", onFinish);
  };

  wheelContainer.addEventListener("transitionend", onFinish);
});
