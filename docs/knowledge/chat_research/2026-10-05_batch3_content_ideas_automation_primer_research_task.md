# Batch 3 notes: content ideas, automation primer, research task

**Source:** ChatGPT chats from batch 3 (Idea Generation / Viral Business Research / Understanding Automation Agents / Automated Business Research Prompt), saved 2026-10-05 before the chats were removed. The science news items are ChatGPT's (2026), not verified.

## Content idea engine
- **Pattern** (the gym-app guy's "I forced the fly to do push-ups forever"): an interesting substrate + an absurd constraint + a visually obvious result.
- **Formula:** THING × GOAL × CONSTRAINT × TIMESCALE × TWIST. For example: virtual fly × get jacked × can't stop × 1,000 simulated years × progressive overload.
- **Rabbit holes to mine:**
  - digital organisms and simulated cells or yeast
  - "given infinite time…" simulations
  - AI playing games (Pokémon Red)
  - AI agent societies (change one rule and watch what emerges)
  - gameplay as training data ("I trained an AI on every decision I made for 30 days")
  - insect robot swarms
- **Mine:** artificial life, simulations, digital twins, embodied AI, evolution, agent societies, world models, small open-source research. Look for the "wait… I can actually PLAY with this?" reaction. Avoid generic "AI news" slop.

## Tie it to a business, or it's empty attention
- **Structure:** weird experiment → entertaining content → visible proof of the product → obvious CTA. The joke and the product should be the same mechanism.
- **Archetypes:**
  1. The product is the experiment.
  2. A benchmark is the content, which builds proprietary data.
  3. A ridiculous test built around the pain the product solves.
  4. Turn the business into a game (an AI Sales League where agents compete on replies, meetings and £).
  5. Generate a proprietary world or dataset.
- **Filter:** the content should demonstrate the product, improve it, generate proprietary data, create a case study, attract the exact customer, or build an asset competitors can't copy. If it only gets impressions, it's low value.
- **Pablo's lane:** "I make your business earn more / easier / more automated". In order: 1 make you more money, 2 save time, 3 improve operations.
- **Formats:** "I fixed / automated / found hidden money in this business", "I made AIs compete to improve this business", "I rebuilt this process in 24 h", "this business leaks money here", "I removed this stupid manual task". Always before → intervention → measurable result.
  - Examples: "I gave 5 AI agents the same 1,000 dead leads", "I rebuilt this company's follow-up and found £18k in their CRM", "I built an employee that answers every lead in under 30 seconds".
- **Umbrella line:** **"I build systems that make boring businesses more money with less work."** The positioning is revenue systems, not "AI automation".

## How automation actually works (primer)
- "24/7" doesn't mean an AI thinking all the time. It means a program that's always available and wakes up on **triggers, schedules, messages or events**.
- **Levels:**
  1. script
  2. workflow (deterministic steps)
  3. persistent automation
  4. AI workflow (AI handles the fuzzy steps)
  5. agentic (AI picks actions dynamically)
  - Aim for about **80% deterministic + 20% agentic.**
- **Running 24/7:** code → Docker → VPS (Hetzner, DigitalOcean, Railway, Render, Fly.io).
- **Triggers:** cron schedules, webhooks (events), queues + workers (Redis/RabbitMQ/SQS/Postgres/Celery/BullMQ) for big volumes.
- **State:** SQLite → Postgres tables (companies, contacts, leads, messages, tasks, events, agent_runs, errors), so it remembers what's done, bounced or replied.
- **AI as a function:** always ask for structured JSON output.
- **Agent loop:** while the goal isn't met → get state → LLM picks a tool → run it → save → repeat.
- **Guardrails:** the agent proposes; rules, policy and quality checks decide (e.g. max 100 emails/day, no repeat within 30 days, approval above €10 or for anything public, confidence over 0.85).
- **Reliability:** retries with backoff and a failed-jobs queue. Log every step, plus a dashboard (jobs, failures, LLM cost, outputs).
- **Ways to build:** n8n/Make/Zapier for prototypes, code-first (Python/TS + Postgres + Docker + queues) for serious work, or a hybrid.
- **Learning order:** Python → APIs/HTTP → JSON → webhooks → SQLite/Postgres → cron → Docker → VPS → queues/workers → LLM structured outputs → tool calling → agent loops → retries/idempotency → logging/monitoring.
- **Everything is:** trigger → state → decision → tools → action → state → repeat.

## RESEARCH TASK (not started)
> Find businesses capable of €20k–€100k+/month where a solo founder or very small team can eventually operate the company in ≤20 founder hours/week, because repetitive acquisition, fulfillment, administration, support and follow-up are heavily automated, while retaining human involvement wherever it materially increases conversion, pricing, quality, trust or retention.

**Prefer:** high-ticket + B2B + pain/money + standardizable + recurring + the machine does the routine work + humans only at high-value moments. This brings tech-enabled services and the revenue-recovery/growth-system family back to the front, instead of filtering them out because onboarding or some sales are human.
