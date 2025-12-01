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

// ПРИЗИ — порядок і назви мають збігатися з config.PRIZES_WEIGHTS
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

// поточний кут поінтера (накручуваний)
let currentRotation = 0;

/**
 * Запит до бекенда
 */
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

/**
 * Показати салют із текстом призу
 */
function showFireworks(text) {
  if (!fireworks || !fireworksText) return;
  fireworksText.textContent = text;
  fireworks.classList.add("show");
  setTimeout(() => fireworks.classList.remove("show"), 2000);
}

/**
 * Обробка кліку по кнопці
 */
btn.addEventListener("click", async () => {
  if (spinning) return;
  if (!pointerRotator) return;

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

  // 1) результат з бекенда
  const { prize, repeat, message } = await spinRequest(payload);

  // 2) визначаємо сектор
  let sectorIndex = sectors.indexOf(prize);
  if (sectorIndex === -1) {
    sectorIndex = Math.floor(Math.random() * sectors.length);
  }

  const sectorCenter = sectorIndex * sectorAngle + sectorAngle / 2;

  // 3) скільки вже "стоїть" поінтер по куту
  const normalizedCurrent = ((currentRotation % 360) + 360) % 360;

  // на який кут треба стати, щоб поінтер дивився на центр сектора
  const deltaToSector = ((sectorCenter - normalizedCurrent) + 360) % 360;

  // рандомні додаткові повні обороти (4–6)
  const extraSpins = 4 + Math.floor(Math.random() * 3); // 4,5,6

  const deltaRotation = extraSpins * 360 + deltaToSector;
  const targetRotation = currentRotation + deltaRotation;

  // скидаємо попередню анімацію
  pointerRotator.style.transition = "none";
  pointerRotator.style.transform = `rotate(${currentRotation}deg)`;

  // запускаємо плавну крутку
  requestAnimationFrame(() => {
    pointerRotator.style.transition =
      "transform 4s cubic-bezier(.33, 1, .68, 1)";
    pointerRotator.style.transform = `rotate(${targetRotation}deg)`;
  });

  const onEnd = () => {
    currentRotation = targetRotation; // запамʼятали новий кут

    if (repeat) {
      res.textContent = `${message} Ваш приз: ${prize}`;
    } else {
      res.textContent = `Вітаємо! Ви виграли: ${prize}`;
    }

    showFireworks(`🎉 ${prize} 🎉`);

    spinning = false;
    btn.disabled = false;
    pointerRotator.removeEventListener("transitionend", onEnd);
  };

  pointerRotator.addEventListener("transitionend", onEnd);
});
