<p><img src="assets/header.svg" width="100%" alt="Hi 👋, I'm Alfred. Student, VFX artist, SaaS animation, AI."></p>

<p><b>Stack</b><br><img src="assets/stack.svg" width="462" alt="After Effects, Premiere Pro, Audition, Blender, Python, Vercel, FastAPI, HTML, CSS, JavaScript"></p>

<p><b>Learning</b><br><img src="assets/learning.svg" width="462" alt="C++, TypeScript, Next.js"></p>

## Overshoot

I make motion for software: launch films, demo videos and product animation that moves the way a good interface feels to use. Everything is keyframed by hand in After Effects, often on real interfaces rebuilt layer by layer. Booking from Q1 2027.

<p><a href="https://overshootfx.com"><img src="assets/overshoot-banner.svg" width="100%" alt="The Overshoot wordmark next to an icon of an animation curve that overshoots its target and settles."></a></p>

[overshootfx.com](https://overshootfx.com)

## Selected projects

<p><img src="assets/stats.svg" width="100%" alt="Commit and language stats across my repositories, updated daily."></p>

### Protocol

Protocol is a coach for building muscle. Open it before the gym and today's session is already decided: the movements, the exact weight and reps for every set, and how close to failure to take them. It learns from every set you log.

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

- The only stored data is an append-only log of sets, check-ins, weigh-ins and answers. The plan, loads, volume and calories are recomputed on every read, so a stale plan can't exist.
- The athlete model has seven learned parameters: strength, fatigue, RIR calibration, dose-response, recovery, adherence and exercise affinity. Each starts at a population prior and moves toward your own data as the log grows, which keeps week one sane and month three personal.
- The focus engine fits a ridge regression over 11 features, VIF-guarded and bootstrapped. Randomized micro-trials work through four unsettled questions, such as whether a walk beats a phone break, and a greedy planner re-simulates the day before each placement.
- `src/core` is pure TypeScript with no React or database code. Vitest covers the engine, model, nutrition, sync and migrations.
- It runs on Next.js 16 and React 19. Data lives offline-first in IndexedDB through Dexie and syncs to Upstash Redis behind a jose-signed http-only cookie.
- Updates can't strand data. The schema only adds, backups restore from any version, sync merges as a union, and a migration leaves data alone when there's no honest equivalent.

</details>

### Local LLMs and microcontrollers

I run open models on my own hardware and put them behind small, locked-down APIs. I also write firmware for ESP32 and Arduino boards that drive displays, touch input and cameras.

<details>
<summary>What it's like to use</summary>

Nothing goes to a model provider, and there's no per-request bill. To an app, the setup looks like any hosted API: an HTTPS address, a key for each device, and requests that queue while the model is busy. Once flashed, the boards run on their own.

</details>

<details>
<summary>How it's built</summary>

- Ollama serves the models on localhost only.
- A FastAPI gateway in front checks hashed bearer tokens, per-token and global rate limits, upload size and file signatures. An async lock lets one request run at a time.
- Tailscale Funnel is the only way in, and no router ports are open.
- Firmware is C++ with PlatformIO, for ESP32, ESP32-CAM and Arduino Uno boards across 3.3 V and 5 V logic.
- SPI displays and resistive touch share one bus, with SD cards on a second.
- An Uno doubles as a USB-serial bridge for flashing.

</details>

### archvfinds

A catalog of fashion finds from archive labels and Instagram brands. Shoppers pick their buying agent once, and every product link on the site opens in that agent.

<p><a href="https://archvfinds.com"><img src="assets/archvfinds-home.svg" width="100%" alt="The archvfinds homepage, with its navigation bar and the headline “Find the fit.” over dark product photos."></a></p>

[archvfinds.com](https://archvfinds.com)

<details>
<summary>What it's like to use</summary>

- The agents page compares every supported agent, and a 30-second quiz suggests one if you're unsure.
- You can browse by brand, item type or outfit, or search the catalog. A filter shows only finds with QC photos.
- Prices show in your currency, and there's no account to make.
- A Discord bot posts a curated find on Monday, a cop-or-drop poll on Thursday and a QC pick on Saturday.

</details>

<details>
<summary>How it's built</summary>

- The site is a static Next.js 15 export on Vercel, built from JSON, so no server runs when a page loads.
- Brand and item-type hubs are generated from product names at build time.
- One link builder handles every agent, each with its own URL encoding.
- Analytics are first-party, in a separate panel app on Neon Postgres. Visitors are counted with a hash whose salt rotates daily. Nothing is stored on their device, and the raw IP never reaches the database. Events are rolled up nightly and deleted after 30 days.
- The discord.js bot only posts products from an allowlist reviewed image by image. Polls keep vote counts and a voter hash scoped to each poll, so votes can't be linked across polls.

</details>
