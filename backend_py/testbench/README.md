# Тестовий стенд: емулятор пристрою + наскрізна перевірка

Що тут є
- `device_simulator.py` — емулятор Inspector-comforT (Pico W), поводиться як прошивка з `device/app_a`.
- `e2e_check.py` — автоматична перевірка ланцюга **пристрій → MQTT → backend → MongoDB → REST** (~50 перевірок).
- `run_backend_inmemory.py` — запуск backend **без MongoDB** (дані в памʼяті).
- `docker-compose.dev.yml` — MongoDB + Mosquitto + backend в Docker (не запускався в моєму середовищі).

## Швидкий старт (4 термінали, з кореня backend_py)
```bash
pip install -r requirements.txt -r testbench/requirements.txt
# 0) MQTT-брокер: docker run -p 1883:1883 eclipse-mosquitto:2 mosquitto -c /mosquitto-no-auth.conf
#    або `mosquitto -p 1883`, або публічний broker.hivemq.com (тоді --broker і MQTT_URL відповідно)

# 1) backend (без Mongo)          # або з реальною: python -m app  (потрібен .env)
PORT=3001 MQTT_URL=mqtt://localhost:1883 python testbench/run_backend_inmemory.py

# 2) емулятор: 3 кімнати з різною поведінкою
python testbench/device_simulator.py --broker localhost:1883

# 3) автоматична перевірка
python testbench/e2e_check.py --api http://localhost:3001 --broker localhost:1883
```
Усе одним махом у Docker: `docker compose -f testbench/docker-compose.dev.yml up --build`.

## Перевірка frontend вручну
```bash
cd frontend/client && npm install
VITE_API_BASE_URL=http://localhost:3001 npm run dev
```
1. Зареєструйтесь → створіть локацію → «додати кімнату», вставте id з консолі емулятора
   (`com-…-fort`; вони стабільні між запусками). Кімнату можна додати лише після першої телеметрії.
2. Очікувано: `school-day` — CO₂ «пилкою» (росте на уроках, падає на перервах, температура ~20–21 °C),
   `comfortable` — високий відсоток комфорту, `stuffy` — CO₂ росте, температура >25 °C, відсоток падає.
3. Для швидкої динаміки: `--speed 30 --interval-ms 3000` (1 с реального часу ≈ 30 с моделі; урок видно за ~1,5 хв).
4. Налаштування кімнати: вкажіть **Wi-Fi `Komiki` / `Parol222`** (як у прошивці) — тоді пристрій застосує нові
   units/interval (видно в консолі емулятора). З іншим Wi-Fi прошивка налаштування відхиляє — емулятор теж
   (`--accept-any-wifi`, щоб вимкнути).
5. `e2e_check.py --keep` лишає створену локацію та виводить логін/пароль, щоб подивитись її у frontend.

## Команди емулятора (вводяться в його терміналі)
`status` · `scenario stuffy 0` (сценарій, номер пристрою) · `offline on|off` (втрата Wi-Fi: вимірювання
копляться й відправляються пачкою) · `bad` (некоректні payload — backend має ігнорувати) · `burst 20` · `quit`.
Сценарії: `school-day`, `comfortable`, `stuffy`, `cold-dark`, `noisy`.
Опції: `--devices N`, `--ids a,b`, `--ts-format iso|epoch`, `--offline-prob 0.2`, `--firmware-cycle`
(підключатись/відключатись щоцикл, як прошивка), `--seed`.

## Наскільки це схоже на справжній пристрій
Повторено з прошивки: формат id, топіки, структура payload, ISO-час, сирі 16-бітні значення АЦП для
gas/sound/light (я виводжу їх обертанням формул backend, щоб на екрані були реальні ppm/дБ/лк), цілі T/H від DHT11,
буфер вимірювань, retained status + last will, перевірка й застосування settings. Не емулюється: Wi-Fi/NTP на
рівні мережі (NTP-хост лише перевіряється на валідність імені), OTA, кнопка/світлодіод, access point.

## Що виявив стенд (є і в оригінальному коді)
1. **Формат часу.** Прошивка шле `timestamp` як ISO-рядок, а `MQTT.md` і Node-backend очікують epoch-секунди
   (у Node `Number("2025-…Z")` = NaN → некоректна дата). У Python-версії backend тепер приймає обидва формати.
2. **Налаштування з UI.** Форма шле лише заповнені поля, backend підставляє порожні `wifi.ssid`/`mqtt.server`,
   а прошивка перевіряє підключення до Wi-Fi — тож зміна, наприклад, лише units **відхиляється** пристроєм.
   Варто, щоб backend брав поточні значення (напр. зберігав їх у БД) або UI вимагав Wi-Fi.
3. **Прошивка зараз не підписується на settings** (блок у `states/ota.py` закоментований) — реальний пристрій
   налаштувань з backend не отримає, поки це не розкоментують. Емулятор підписується, як задумано.
4. **Одиниці температури.** Прошивка лише підписує `units` (standard/metric/imperial), значення завжди °C;
   формули комфорту на backend теж припускають °C.
5. **Помилки на фронтенді.** `request()` читає `error.message`, а backend віддає `error.error.message` —
   користувач завжди бачить «API Error».
6. Рекомендації Gemini потрібен `GOOGLE_API_KEY`; без нього поради порожні (e2e покаже ⚠️).
