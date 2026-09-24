<h1 align="center">Hi 👋, I'm Alfred</h1>
<h3 align="center">Student · VFX artist · SaaS animation · AI</h3>

## Overshoot

I make motion for software: launch films, demo videos and product animation that moves the way a good interface feels to use. Everything is keyframed by hand in After Effects, often on real interfaces rebuilt layer by layer. Booking from Q1 2027.

<p><img src="assets/overshoot.svg" width="100%" alt="A scale curve in a graph editor that springs past 100 percent to 112, dips below and settles, next to the same interface element drawn at four frames of the move."></p>

<p><picture><source media="(prefers-color-scheme: dark)" srcset="assets/button-overshoot-dark.svg"><a href="https://overshootfx.com"><img src="assets/button-overshoot-light.svg" height="98" alt="overshootfx.com"></a></picture></p>

## Selected projects

<p><img src="assets/stats.svg" width="100%" alt="Across all my repositories, 14 May to 24 Sep 2026: 335 commits, 61k lines of code, 590+ tests, 6 repositories. Commits per week peak at 47. Languages: TypeScript 69%, JavaScript 12%, Python 8%, HTML 6%, CSS 2%, C++ 2%, other 1%."></p>

### Protocol

A strength-training coach built on a statistical model of the athlete. It reads an append-only training log and works out today's session: which movements, what load and how many reps in each set.

<p><img src="assets/protocol.svg" width="100%" alt="How Protocol works: a training log of sets, check-ins and weigh-ins feeds an athlete model of seven parameters, each pulled from a population prior toward the athlete's data. The model derives today's sets with exact loads and reps, and the logged result feeds the next derivation."></p>

- Seven parameters fitted to each athlete's own data and shrunk toward population priors until the data can carry them
- Exact load and reps for every set, corrected for how the athlete reports reps in reserve
- Deloads fire on modelled fatigue debt, not on the calendar
- The plan is recomputed from the log on every read, so it can never go stale
- A focus engine fits circadian and caffeine models and runs randomised micro-trials where the evidence is contested

### Local LLMs and microcontrollers

Self-hosted vision models behind a hardened gateway, and firmware for ESP32 and Arduino boards.

<p><img src="assets/local-ai.svg" width="100%" alt="A client reaches a FastAPI gateway only through Tailscale Funnel. The gateway checks a hashed bearer token, rate limits, JPEG magic bytes and a 512 KB cap, then takes a GPU lock before calling Ollama on localhost. Below: an ESP32 sharing one SPI bus between an ILI9488 display and an XPT2046 touch controller, and an Arduino Uno held in reset as a USB-serial bridge to flash an ESP32-CAM."></p>

- Vision models served by Ollama, kept fully in VRAM, bound to localhost only
- FastAPI gateway: SHA-256-hashed bearer tokens, per-token + global rate limits
- One async GPU lock serialises inference; JPEG magic-byte + 512 KB body checks
- Tailscale Funnel is the only way in; nothing listens on 0.0.0.0
- ESP32 / ESP32-CAM / Arduino firmware in C++ with PlatformIO
- SPI display + resistive touch sharing one bus, camera modules, flashing through a USB-serial bridge, 3.3 V / 5 V logic levels

### archvfinds

A catalog of fashion finds. Shoppers browse brands, categories, outfits and QC photos, choose their buying agent once, and every product link opens in that agent.

<p><img src="assets/archvfinds.svg" width="100%" alt="How archvfinds works: brand hubs, category hubs, outfits and QC photos feed the site. The shopper's chosen agent turns each item ID into a ready agent link. A Discord bot and a first-party analytics panel sit alongside the site."></p>

- Next.js site with brand, category and outfit pages, catalog search and a currency switcher
- One product ID becomes a working link for whichever supported agent the shopper picked
- A Discord bot posts a curated find, a poll and a QC pick every week, each linking back to the site
- First-party analytics count visitors with a salted hash that rotates daily; IP addresses are never stored

<p><picture><source media="(prefers-color-scheme: dark)" srcset="assets/button-archvfinds-dark.svg"><a href="https://archvfinds.com"><img src="assets/button-archvfinds-light.svg" height="98" alt="archvfinds.com"></a></picture></p>

## Stack

<p><img src="https://skillicons.dev/icons?i=ae%2Cpr%2Cau%2Cblender%2Cpy%2Cvercel%2Cfastapi%2Chtml%2Ccss%2Cjs&theme=dark" alt="After Effects, Premiere Pro, Audition, Blender, Python, Vercel, FastAPI, HTML, CSS, JavaScript"></p>

### Currently learning

<p><img src="https://skillicons.dev/icons?i=cpp%2Cts%2Cnextjs&theme=dark" alt="C++, TypeScript, Next.js"></p>
