---
name: Velarqo
description: A UK tradesperson's desk diary on a white page, set in dark ink with one brick red.
colors:
  paper: "#ffffff"
  ink: "#16181b"
  ink-soft: "#41464e"
  rule: "#dcdfe4"
  rule-strong: "#a9afb8"
  tint: "#f3f4f6"
  bubble: "#e9ebef"
  brick-red: "#b3261e"
  brick-red-dark: "#8c1c16"
  red-wash: "#fbeceb"
typography:
  display:
    fontFamily: "Atkinson Hyperlegible Next, Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(2.3rem, 1.3rem + 3.9vw, 4.1rem)"
    fontWeight: 800
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Atkinson Hyperlegible Next, Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.8rem, 1.2rem + 2.2vw, 2.8rem)"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Atkinson Hyperlegible Next, Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif"
    fontSize: "1.22em"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(18px, 1rem + 0.25vw, 20px)"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Atkinson Hyperlegible Next, Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.45
    fontFeature: "tnum"
rounded:
  sm: "4px"
  md: "6px"
  bubble: "14px"
spacing:
  gutter: "clamp(18px, 4vw, 40px)"
  section: "clamp(60px, 9vw, 112px)"
  diary-line: "34px"
  wrap: "1140px"
components:
  button-primary:
    backgroundColor: "{colors.brick-red}"
    textColor: "{colors.paper}"
    rounded: "{rounded.md}"
    padding: "14px 28px"
    height: "58px"
  button-primary-hover:
    backgroundColor: "{colors.brick-red-dark}"
    textColor: "{colors.paper}"
  header-link:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    height: "44px"
  diary-card:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
  booking-block:
    backgroundColor: "{colors.brick-red}"
    textColor: "{colors.paper}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
  sms-bubble:
    backgroundColor: "{colors.bubble}"
    textColor: "{colors.ink}"
    rounded: "{rounded.bubble}"
    padding: "9px 13px"
  tint-band:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.ink}"
---

# Design System: Velarqo

## Overview

**Creative North Star: "The Desk Diary"**

The site is the installer's own week-to-view diary. A white page, near-black ink, hairline cool-grey rules and one brick red that is the logo's colour. Quotes that went quiet are shown becoming survey bookings written into next week. The register is plain, large and legible for a 40-60 year old owner reading on a phone between jobs. Evidence is shown (the exact texts, the exact steps) rather than claimed.

Density is open and ruled, not carded. Sections are separated by hairlines and generous vertical space; lists are rows between rules rather than boxes. Depth is nearly absent: the diary card and the one button are the only lifted objects. Everything is set in one family, Atkinson Hyperlegible Next, with weight (800 against 400) carrying hierarchy.

It rejects the agency landing page (gradient hero, stock handshake, stats band) and the old dark quotation-form look.

**Key Characteristics:**
- White page, ink text, hairline rules; red is rare and meaningful.
- One typeface, two working weights, large body (18-20px).
- Week-to-view diary grid with a 34px ruling for note rows and empty days.
- Grey SMS bubbles; the booking is a red set-type block, not script.
- One button on the whole site.

## Colors

A near-monochrome cool grey and ink palette with a single brick red.

### Primary
- **Brick Red** (#b3261e): reserved for diary day names, the diary-head underline, the booked-survey block, the one button and text selection.
- **Dark Brick** (#8c1c16): the button's hover fill and the soft shadow tint beneath it.

### Neutral
- **Paper White** (#ffffff): page and card ground.
- **Desk Ink** (#16181b): body and heading text, focus ring, header link.
- **Soft Ink** (#41464e): secondary text, intros, labels, captions.
- **Hairline** (#dcdfe4): section rules and row dividers.
- **Strong Hairline** (#a9afb8): list-item rules, diary and mail borders, reply-bubble border.
- **Tint** (#f3f4f6): the single tinted band, the video placeholder, portrait placeholder, contents box.
- **Bubble Grey** (#e9ebef): sent SMS bubble ground.
- Red wash (#fbeceb) is declared but unused in the build; do not rely on it.

### Named Rules
**The Brick Rarity Rule.** Red appears only on diary day names, the diary-head rule, the booked-survey block, the one button and selection. Anywhere else, use ink.
**The One Tint Rule.** Exactly one tinted full-width band per page (the "What I need" section). All other sections sit on white, divided by hairlines.

## Typography

**Display, Headline, Body, Label Font:** Atkinson Hyperlegible Next (variable 200-800, latin, self-hosted woff2; fallback Atkinson Hyperlegible, Segoe UI, system-ui, sans-serif)

**Character:** Open-letterform legibility face, heavy where it leads and plain where it reads. No second family.

### Hierarchy
- **Display** (800, clamp 2.3rem to 4.1rem, 1.04, -0.025em): hero h1 only, max 16ch.
- **Headline** (800, clamp 1.8rem to 2.8rem, 1.12, -0.015em): section h2, max 22ch. Close h2 runs larger (up to 3.3rem); doc page h1 up to 3.4rem.
- **Title** (800, 1.2-1.3em, 1.12): step, question, trade-link and need headings.
- **Body** (400, 18-20px, 1.6): running text, 58-60ch measure; intros in Soft Ink at 1.05em.
- **Label** (700, 13-17px): diary times, thread labels, nav (17px), captions (15px).

### Named Rules
**The Tabular Time Rule.** Tabular figures apply only to times, the diary head, thread labels and day names. Not to body copy.
**The Weight Is Hierarchy Rule.** Contrast comes from 800 versus 400 and size, never from a second face, italics or uppercase.

## Layout

A 1140px centred wrap with fluid gutters (18-40px) and fluid section padding (60-112px). The hero is a two-column grid at 920px and up (about 1.08fr text, 0.92fr diary); other splits switch at 900px (0.85fr / 1.15fr). Steps run three across at 900px, needs and questions two across at 760-900px. Below 760px the nav hides, the header keeps logo and an ink "Email Pablo" link, the hero and close buttons go full width, and the diary day column narrows to 52px. Long-form pages (FAQ, privacy, 404) hold a 46rem column. Lists are rows divided by hairlines, never cards.

The diary uses a 34px ruling: ruled lines appear only behind note rows and empty days.

## Elevation & Depth

Flat and ruled by default. Two lifted objects only: the diary card (`box-shadow: 0 1px 2px rgba(22,24,27,.08), 0 10px 18px -14px rgba(22,24,27,.3)`) and the button (`0 1px 2px rgba(22,24,27,.18), 0 6px 16px -8px rgba(140,28,22,.55)`, deepening on hover, flattening on press). Shadows are soft and ambient.

### Named Rules
**The Two Lifts Rule.** Only the diary card and the button carry shadows. Hairlines do the rest.

## Shapes

Mostly square-ish: 4px corners on the diary, mail card, video frame, portrait, contents box and booking block; 6px on the button. SMS bubbles are the only rounded form (14-18px with one 4-5px tail corner; sent bubbles tail bottom-left, replies bottom-right). Borders are 1px hairlines; the diary head carries a 2px red underline. Icons are inline stroked SVG (2.2 stroke, round caps), 22-26px.

## Components

### Buttons
- **Shape:** gently squared (6px).
- **Primary (the one `.btn`):** Brick Red fill, white 800-weight 19px text, 58px min height, padding 14px 28px, optional mail icon. Hover shifts to Dark Brick; 0.15s ease-out.
- **Header CTA:** the same markup restyled as an ink underlined text link (2px underline, 44px target), red on hover. No filled button in the header.
- **Focus:** 3px ink outline, 3px offset, on every focusable element.

### Diary card
Bordered (strong hairline) 4px card. Head: bold month left, soft-ink week right, 2px red underline. Day rows: 62px red day-name column (small day label over a 28px 800 date) beside a body separated by a hairline. Rows contain a small time label, SMS bubbles (sent grey left, reply white with border, right-aligned), ruled notes, or an empty ruled day. The booking block is a red set-type entry that writes itself in once via a clip-path reveal (1.1s, 0.7s delay), static under reduced motion.

### SMS and mail samples
Sent messages sit in Bubble Grey; replies in white with a strong hairline. Template placeholders are shown in square brackets, bold. The mail sample is a bordered 4px box with a bold subject over a hairline.

### Lists
Steps (large 44-56px numerals, strong hairline above), needs, questions and trade links are rows divided by strong hairlines. Trade links end in an arrow that nudges 4px on hover.

### Close
The final call to action is an empty diary day: a red day name beside a ruled body holding the heading, sentence and the one button. On phones it stacks.

### Video slot
16:9, 4px, Tint placeholder with a short line until a self-hosted mp4 exists; with a video it becomes ink-backed and borderless.

## Do's and Don'ts

### Do:
- **Do** use ink for everything and reserve Brick Red per the Brick Rarity Rule.
- **Do** keep one button style per page and one tinted band per page.
- **Do** build lists as hairline-ruled rows, headings at 800 weight, body at 18px or larger.
- **Do** apply the 34px diary ruling only to note rows and empty days.
- **Do** show real example text (messages, steps) in the grey bubble and diary vocabulary.
- **Do** keep touch targets 44px or taller and the 3px ink focus ring.

### Don't:
- **Don't** add gradients, stock photography, stat bands or a dark quotation-form look.
- **Don't** introduce a second typeface, script faces for the booking, or uppercase tracking labels.
- **Don't** wrap sections in shadowed cards; only the diary card and the button lift.
- **Don't** use red for decoration, borders, icons or secondary links.
- **Don't** apply tabular figures or ruled backgrounds outside their named places.
