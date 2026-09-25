<p><img src="assets/header.svg" width="100%" alt="Hi 👋, I'm Alfred, 16. Student, VFX artist, SaaS animation, AI."></p>

## Overshoot

I make motion for software: launch films, demo videos and product animation that moves the way a good interface feels to use. Everything is keyframed by hand in After Effects, often on real interfaces rebuilt layer by layer. Booking from Q1 2027.

<p><a href="https://overshootfx.com"><img src="assets/overshoot-banner.svg" width="100%" alt="The Overshoot wordmark next to an icon of an animation curve that overshoots its target and settles."></a></p>

[Overshootfx.com](https://overshootfx.com)

## Stack

<p><b>Using</b><br><img src="assets/stack.svg" width="462" alt="After Effects, Premiere Pro, Audition, Blender, Python, Vercel, FastAPI, HTML, CSS, JavaScript"></p>

<p><b>Learning</b><br><img src="assets/learning.svg" width="462" alt="C++, TypeScript, Next.js"></p>

## Selected projects

<p><img src="assets/stats.svg" width="100%" alt="Commit and language stats across my repositories, updated daily."></p>

### Protocol

After training for a while I wanted to progress faster. Recent sports science had most of the answers: how many hard sets grow a muscle, how close to failure they need to go, when a deload pays off. None of it was written for someone standing at a squat rack.

Protocol turns that research into a plan you can follow without reading any of it. Open it before the gym and today's session is already decided: the movements, the exact weight and reps for every set, and how close to failure to take them. Using it feels like having a friendly coach. Behind that sits a statistical model of you as a lifter that updates after every set and bends the plan around the exercises you prefer.

<details>
<summary>What it's like to use</summary>

- You pick the weekdays you train. Miss one and the session waits for you.
- Tap the session title to train something else, and the rest of the week rearranges around it.
- When a lift stalls, the plan changes the stimulus.
- Deloads come from accumulated fatigue, so a hard month earns one and two easy weeks don't.
- If you misjudge how many reps you had left, it learns your bias and corrects for it.
- One goal sets both training and food, and calorie targets follow your bodyweight trend.
- The Focus screen predicts how alert you'll be through the day from your sleep and caffeine, and checks itself now and then with a 3-minute reaction test. It places deep work, study, meetings and the workout where each fits best.
- It works offline in the gym and syncs later.

</details>

<details>
<summary>How it's built</summary>

- The app stores one thing: an append-only log of sets, check-ins, weigh-ins and answers. The athlete model is rebuilt from that log and memoized against its version, and the plan, loads, volume and calories are derived on every read, so a stale plan can't exist.
- Estimated one-rep maxes run through Holt's level-and-trend filter, a Kalman filter with fixed gains. A bad session moves the estimate by a fraction of the surprise, and a real change still registers.
- Reps-in-reserve bias is measured from your own sets. A set taken to failure is compared with an earlier set at the same load in the same session, corrected for the reps lost to fatigue in between, and every later target accounts for the difference.
- Seven parameters are learned per lifter: strength, fatigue, RIR calibration, dose-response, recovery, adherence and exercise affinity. Each is shrunk toward a population prior with weight n/(n+k), which keeps week one sensible and makes month three personal.
- Rep targets model set-to-set fatigue, so three sets of 8 at one weight are prescribed as 8, 8, 7. Fatigue debt builds per muscle and for the whole body and decides when a deload comes. A volume controller adds a set, holds, backs off or stops for each muscle, using the local OLS slope of progress against volume as its marginal return.
- Nutrition starts from Katch–McArdle when body composition is known and Mifflin–St Jeor otherwise. Bodyweight is smoothed with an EWMA and trended from the two halves of a 28-day window. After 10 days, calories steer toward a target rate (+0.35% of bodyweight a week to build, −0.7% to lean out) inside a 0.15% deadband, capped at 150 kcal a week and rounded to 10 kcal.
- The Focus model combines sleep pressure with a 14-day sleep-debt term, a circadian rhythm fitted as 24- and 12-hour harmonics in closed form, and a one-compartment caffeine model with Emax masking. A ridge regression over 11 features fits it to your focus ratings, with the reaction tests calibrating the rating scale. The regression is VIF-guarded, bootstrapped by whole days and solved with a hand-written Cholesky decomposition.
- The planner simulates the day in 96 fifteen-minute slots after a 56-day warm-up, averages a 9-run ensemble, and re-simulates after each of up to 8 placements. Randomized micro-trials test open questions on you, such as whether a walk beats a phone break, with arms assigned by an FNV-1a hash of the date and block.
- `src/core` is pure TypeScript with no React or database code, and Vitest covers the engine, model, nutrition, focus, sync and migrations. The app runs on Next.js 16 and React 19, offline-first in IndexedDB through Dexie, and syncs to Upstash Redis behind a jose-signed http-only cookie.
- Updates can't strand data. Facts carry stable IDs, so sync merges as a set union, and new schema versions only add optional tables.

</details>

### Microcontrollers and hardware hacking

I like hardware I can open up and make do something it wasn't sold to do. Most of it is ESP32 boards. I wire bare screens, touch panels and camera modules from their pinouts and datasheets, flash my own firmware onto off-the-shelf boards and gadgets, salvage and solder parts, and probe UART, I2C and SPI lines with a multimeter or logic analyzer to see what a board is actually doing.

Cheap boards rarely match their listings. One was sold as an ESP32-C5 with a 2.8-inch screen, 16 MB of flash and 8 MB of PSRAM. Reading the chip with esptool turned up an older ESP32 with 4 MB of flash and no PSRAM, wired to a 3.5-inch ILI9488 panel, so I mapped the rest by measurement and wrote the drivers to match.

<details>
<summary>How I mapped the board</summary>

- The listing promised a RISC-V C5 with Wi-Fi 6. esptool's chip and flash IDs showed an ESP32-D0WD-V3: dual-core Xtensa, 2.4 GHz Wi-Fi 4, 4 MB of flash and no PSRAM.
- A sweep through display drivers found a 320×480 ILI9488 on HSPI (MISO 12, MOSI 13, SCK 14, CS 15, DC 2) that needs its colors inverted.
- The backlight pin came from bisecting candidate GPIOs while measuring screen contrast. GPIO 27 changed it by 73.9 gray levels, and every other pin by 0.3 to 1.3.
- Probing the wiring found an XPT2046 resistive touch controller sharing the display's SPI bus (CS 33, IRQ 36). The SD slot sits on VSPI (18, 19, 23, CS 5).
- I wrote the XPT2046 driver directly over SPI at 2 MHz inside bus transactions: pressure from Z1 and Z2 (0xB1, 0xC1), X on 0xD1, Y on 0x91 and a final 0x90 to power down. The first conversion is thrown away, pressure is z1 + 4095 − z2 against a threshold tuned from 350 to 140, and every reading is a median of three.
- A three-point calibration works out axis swap and flips, extrapolates to the screen edges, and saves to NVS with a copy in `/config.json` on the SD card.

</details>

<details>
<summary>Firmware and wiring</summary>

- Firmware is C++ on PlatformIO with the Arduino framework, GFX Library for Arduino and ArduinoJson. At about 1.3 MB it outgrew the default 1.25 MB app partition, so it runs on the huge_app layout.
- The touch interface uses 44 px targets, and a soft-AP page handles Wi-Fi setup.
- On the ESP32-CAM, the firmware checks for PSRAM and reads the sensor's product ID to tell an OV2640 (0x26) from an OV3660 (0x36). It captures VGA JPEG at quality 12 into two PSRAM frame buffers with XCLK at 20 MHz, falls back to QVGA, and validates the JPEG markers on every frame.
- The camera kept browning out. I left the brownout detector on and fixed the cause with a stronger 5 V supply and a 470 µF capacitor.
- An Arduino Uno doubles as a USB-serial bridge for flashing, with its reset tied to GND, an empty sketch and every pin left as an input. Uploads run at 115200 baud because its 16U2 bridge drops out at 460800.
- A 10k/20k divider steps 5 V logic down to about 3.2 V for the ESP32.

</details>

### Local LLMs

I wanted to use language models from my own apps and devices without sending data to a provider or paying per request. The models run on my own machine, behind a small API that's safe to put on the internet.

<details>
<summary>What it's like to use</summary>

To an app it looks like any hosted API: an HTTPS address, a token for each device, and requests that queue while the model is busy. A lost device is locked out by revoking its token, which takes effect on the next request.

</details>

<details>
<summary>How it's built</summary>

- Ollama serves the models on 127.0.0.1. A FastAPI gateway sits in front, and Tailscale Funnel is the only way in, with no router ports open.
- ASGI middleware authenticates each request before the body is buffered. It checks Content-Length up front, then counts the streamed bytes and cuts the request off with a 413 once it passes the cap.
- Tokens carry 32 bytes of entropy from `secrets.token_urlsafe`. Only their SHA-256 hashes are stored, and the plaintext is shown once.
- Verification runs `secrets.compare_digest` against every stored hash without stopping at a match, so timing can't reveal which token matched. The token file is re-read on each call, so revoking a token needs no restart, and every write is atomic.
- Rate limits are sliding-window deques per token and globally, per hour. A rejected request doesn't use up capacity.
- Uploads must pass a file-signature check before they reach the model, and one asyncio lock serializes inference. Logs keep metadata and a hash of each upload, never the content.
- The model client uses httpx with a timeout and one retry on connect or read errors, and returns 504 on a timeout and 503 when the model is down.
- pytest covers issuing, verifying and revoking tokens, checks that plaintext never reaches disk, and tests the limiter: the window slides, rejected requests don't count, and buckets stay separate.

</details>

### Archvfinds

Finds get shared as links, but every buying agent needs its own link format, so a link that works for one shopper breaks for the next. The sites that collected finds didn't help either. Most were cluttered, slow or hard to trust.

Archvfinds is the catalog I wanted to use: fashion finds from archive labels and Instagram brands on a fast static site. Pick your buying agent once, and every product link on the site opens in that agent.

<p><a href="https://archvfinds.com"><img src="assets/archvfinds-home.svg" width="100%" alt="The Archvfinds homepage, with the headline “Find the fit.” over dark product photos."></a></p>

[Archvfinds.com](https://archvfinds.com)

<details>
<summary>What it's like to use</summary>

- The agents page compares every supported agent, and a 30-second quiz suggests one if you're unsure.
- You can browse by brand, item type or outfit, or search the catalog. A filter shows only finds with QC photos.
- Prices show in your currency, and there's no account to make.
- A Discord bot posts a curated find on Monday, a cop-or-drop poll on Thursday and a QC pick on Saturday.

</details>

<details>
<summary>How it's built</summary>

- The site is a static Next.js 15 export on Vercel, built from JSON, so no server runs when a page loads. Ordered matchers derive each product's brand and item type from its name at build time, and the brand and category hubs are generated from those.
- One link builder covers every agent, each with its own mix of path segments, query parameters and single or double URL encoding, plus a fallback for links it can't convert.
- Sorting by popularity decays repeat brands and interleaves categories, so one label can't take over a page.
- Analytics are first-party. The tracker keeps a per-tab session ID in sessionStorage, sets no cookies, writes nothing to localStorage, and only runs on the production hostname.
- A separate panel app on Neon Postgres counts visitors as `sha256(salt|day|ip|ua)` cut to 32 hex characters, with a salt that rotates at midnight UTC. The raw IP is never stored.
- Its collect endpoint checks an origin allowlist, accepts at most 20 events and 16 KB per request, and writes them in one multi-row insert. An insert-if-absent CTE on `visitor_seen` keeps a visitor from being counted twice.
- A cron job at 03:10 UTC rebuilds the daily rollups with an idempotent delete-then-insert and logs each run. Raw events are purged after 30 days and `visitor_seen` after 3.
- The discord.js bot checks every 30 seconds for a due slot at 19:00 Swedish time. Each slot is keyed by date and kind, so a restart can't double-post, and state is written atomically through a temp file and a rename.
- Posts come from a hand-approved pool validated against the live catalog. A Fisher–Yates queue never opens with the product it just posted and holds back a find from the same brand as the previous post.
- Poll votes are stored as `sha256(messageId:userId)`, so one person hashes differently on every poll. Changing a vote moves the count, and voter hashes are deleted after 30 days while the totals stay.
- Discord doesn't replay events a bot missed, so the bot snapshots members to disk and diffs them at startup to catch anyone who left while it was offline. Failed sends to the panel wait in a disk queue and retry.

</details>
