# Velarqo back office: autónomo, tax, invoicing, getting paid (Spain)

Side: **Velarqo**. No gestor: Claude prepares everything (forms, figures,
invoices, calendar); the owner files and signs with certificado digital /
Cl@ve, because only the taxpayer (or a registered representative) can.
Claude is not a registered tax adviser: the owner is liable for what's
filed. Worth a one-off paid check only if something unusual comes up.

Researched 2026-09-30. Sources at the bottom. Re-check anything marked
*(verify)* before relying on it.

---

## 0. The shape of it

- You: **autónomo** in **estimación directa simplificada** (IRPF), régimen
  general de IVA. Switch to an SL around **€40-60k net profit/year**.
- You sell to **UK businesses** → **no Spanish VAT** on your invoices
  ("no sujeta", art. 69 LIVA). No IRPF retention either (only Spanish
  clients withhold).
- You buy from **US** (Smartlead, Anthropic) and **EU** (Google Ireland)
  → **reverse charge**: you self-assess Spanish VAT and deduct it in the
  same return, net €0. Needs registration in the **ROI** (EU VAT number).
- Every quarter: **303** (VAT), **130** (IRPF advance, 20%), **349** (if
  you bought EU services). Every year: **390** (VAT summary) and **Renta
  (100)**.

---

## 1. One-time setup (before launch day, target ~20 Oct 2026)

Why before launch: the cold emails are the start of the activity, and the
footer needs your legal name + NIF + address anyway.

### 1.1 Digital identity (do first; everything needs it)
- **Certificado digital (FNMT)** or **Cl@ve Móvil**. FNMT certificate:
  request online, verify identity (office or video), download.

### 1.2 Hacienda: Modelo 036 (the 037 no longer exists since Feb 2025)
Sede AEAT → Censos → Modelo 036 (alta). Key choices:

| Field | Value |
|---|---|
| Tipo | Alta, persona física |
| Fecha de inicio | the day you file (or launch day), not later than the first cold email |
| Actividad | **Empresarial**, IAE **epígrafe 844** (servicios de publicidad, relaciones públicas y similares). CNAE **7311** (for Seguridad Social) |
| Lugar de actividad | your home address (declare the home office: % of m² used, needed to deduct home costs) |
| IVA | Régimen general; you'll mark operations "no sujetas" per invoice |
| **ROI / NIF-IVA** | **Yes, request inscripción en el ROI** (you buy services from EU companies like Google Ireland). Gives you an **ES + NIF** VAT number valid in VIES |
| IRPF | Estimación directa **simplificada**; pagos fraccionados **Modelo 130** |

### 1.3 Seguridad Social: RETA via Import@ss (same day as the 036)
- Alta en RETA, CNAE 7311, same start date.
- Request **tarifa plana**: **~€88.64/month for 12 months** (€80 + MEI).
  *Must be requested at alta.* Extendable 12 more months only if your
  income is below the SMI.
- Choose a **mutua colaboradora** (e.g. any major one; they're equivalent
  for this).
- Direct debit of the cuota: a Spanish-branch IBAN is safest *(verify
  whether TGSS accepts a Revolut Business LT IBAN; if not, use your
  personal Spanish account for this one debit and treat it as a business
  expense)*.
- After the tarifa plana year, the cuota depends on your net income:
  roughly **€300-€600/month** at the income levels we're targeting. You
  can change your declared income bracket up to 6 times a year;
  Seguridad Social regularises once your Renta is filed.

### 1.4 Money setup
- **Revolut Business** in the business name (you). Use it for **every**
  business expense and every client payment. Nothing personal through it,
  nothing business through personal accounts.
- In Revolut create a pocket **"Hacienda"**: move **30% of every payment
  received** into it on arrival (covers 130 advances + year-end IRPF +
  higher cuota later). Adjust once we see real numbers.
- **In every vendor's billing settings** (Google Workspace, Smartlead,
  Anthropic, domain registrar): business name + address + **NIF-IVA
  (ES…)**, so they invoice you **without VAT** (reverse charge). If a
  vendor charges you Spanish VAT anyway, that VAT isn't deductible: fix
  the billing profile.

---

## 2. Invoicing (from the first client)

### 2.1 Tool
- **AEAT's free VeriFactu invoicing app** (Sede AEAT → IVA → Sistemas
  Informáticos de Facturación y Verifactu). Free, generates the QR and
  sends the record to Hacienda, compliant from day one. Fine for low
  volumes; move to a paid tool if it gets painful.
- VeriFactu becomes mandatory for autónomos on **1 July 2027** (Real
  Decreto-ley 15/2025). Using the AEAT app now means nothing to migrate.
- **Don't** make Stripe invoices or our own scripts the legal invoice:
  they'd be a non-certified billing system under VeriFactu. Stripe is only
  for *taking payment*.

### 2.2 What every invoice must show (RD 1619/2012, art. 6)
- Series + consecutive number (e.g. `2026-001`), issue date, and service
  date/period if different.
- **You**: full name, NIF, address. (Trading name "Velarqo" can appear too.)
- **Client**: legal name, **UK company number / UK VAT number**, address.
- Description (e.g. "Old-quote reactivation: 14 booked surveys, October
  2026").
- Base amount, currency (GBP is allowed), **VAT: 0**, total.
- The legal note:
  **"Operación no sujeta a IVA por reglas de localización (art. 69.Uno.1º
  Ley 37/1992). Reverse charge: the customer accounts for any UK VAT."**
- No IRPF retention line (foreign client).
- Payment details: Revolut **GBP sort code + account number**, due date.

### 2.3 Currency
- Invoice UK clients **in GBP** (they pay domestically, you receive GBP).
- For your books and tax returns, convert each invoice to EUR at the ECB
  rate on the invoice date. Claude keeps this ledger.

---

## 3. Getting paid

| Method | How | Cost | Use for |
|---|---|---|---|
| **UK bank transfer (primary)** | Client pays your Revolut Business **GBP local details** (sort code + account number): a normal UK Faster Payment for them | Free to receive | Everything by default |
| **Stripe card payment link** | Payment link on the invoice email | Card fees (UK cards on an EEA Stripe account are charged international rates, ~2.5-3.3% *(verify)*) | Clients who want to pay by card |
| **Bacs Direct Debit** | ❌ Not available: Stripe only offers Bacs to UK Stripe accounts | | Revisit if you open a UK Ltd |

Terms: invoice **monthly in arrears** for per-survey fees, **7-day** payment
terms, late fee clause in the contract. Setup fees (if any) upfront.

GBP → EUR: keep income in GBP and convert in batches on weekdays within
your plan's allowance (weekend/over-allowance FX costs more).

---

## 4. Expenses you can deduct

Always get a **full invoice (factura completa) with your NIF**, not a
receipt. Store the PDF.

| Expense | Deductible | VAT treatment |
|---|---|---|
| Smartlead, Anthropic (US) | 100% | Reverse charge: 303 boxes 12/13 + 28/29 |
| Google Workspace (Google Ireland) | 100% | Reverse charge + **349** |
| Domains, hosting | 100% | Depends on vendor country (as above) |
| Cuota de autónomos | 100% (IRPF) | n/a |
| Laptop / hardware | Amortised over its useful life | Spanish VAT deductible if 100% business |
| Mobile + internet | Reasonable business % | Same % of VAT |
| Home office supplies (electricity, water, internet at home) | **30% × % of home used** (declared in 036) | Not VAT-deductible for home supplies *(verify)* |
| Training, books, courses | 100% if related | as invoiced |
| Plus automatically | **5% of net income** as "gastos de difícil justificación", max **€2,000/year** | |

---

## 5. Tax calendar

| When | What | Content |
|---|---|---|
| **1-20 Jan / Apr / Jul / Oct** (Q4 until **30 Jan**) | **303** | VAT: invoices to UK in **box 120** (no sujetas); reverse charge on purchases in boxes 12/13 and 28/29 (usually nets to €0). Result is usually €0 or a small refund |
| same dates | **130** | IRPF advance: **20% × (cumulative income − cumulative expenses) − earlier 130 payments** |
| same dates | **349** | Only if you bought EU services (Google Ireland) that quarter |
| **by 30 Jan** | **390** | Annual VAT summary |
| **April-30 June** | **Renta (100)** | Final IRPF; the 130 advances are subtracted |
| Monthly | Cuota RETA | Direct debit |

Your first filings if you register in October 2026: **Q4 2026 → 303, 130,
349 by 30 January 2027**, plus **390** by 30 January.

---

## 6. What Claude does every quarter

1. Keep the ledger: every invoice issued (GBP + EUR), every expense (with
   vendor country and VAT treatment), every payment.
2. Around day 1 of the filing month: prepare 303, 130, 349 figures box
   by box, and the amount to pay.
3. Owner files in the Sede with certificado/Cl@ve (about 15 minutes).
4. Remind: move money to the Hacienda pocket, and adjust the RETA income
   bracket if income changes a lot.

## 7. Open decisions / to verify

- Registration date: before launch (recommended) vs at first client.
- TGSS direct debit from a Revolut Business IBAN *(verify)*.
- Stripe fees for UK cards on a Spanish account *(verify on Stripe's pricing page)*.
- Home office: whether to declare it in the 036 (small saving, some paperwork).
- When profit passes ~€40-60k/year: SL (then corporate tax 15% for the first years, 25% after).

---

## Sources

- 037 abolished, alta via 036 + RETA within 60 days: [Declarando](https://declarando.es/modelo-036), [Conversoria](https://www.conversoriaecnae.es/blog/modelo-037-eliminado-nueva-forma-de-alta-para-autonomos-2026)
- Tarifa plana 2026 (€80, €88.64 with MEI, 12 months): [Billeo](https://www.billeo.es/blog/tarifa-plana-autonomos-2026), [Quipu](https://getquipu.com/blog/tarifa-plana-autonomos/)
- Cuotas 2026 by income: [Billin](https://www.billin.net/blog/cuotas-autonomos-2023-2031/)
- ROI / reverse charge for EU services (Google Ireland): [Quipu](https://getquipu.com/blog/que-es-el-registro-de-operadores-intracomunitarios-y-alta-en-roi/), [Xolo](https://blog.xolo.io/es/roi-numero-iva-intracomunitario-autonomos)
- Services to non-EU business clients not subject to Spanish VAT (art. 69 LIVA), 303 not 349: [Billeo](https://www.billeo.es/blog/iva-facturas-clientes-extranjeros-autonomo-espana)
- 303 box 120 (no sujetas por reglas de localización): [SuperContable](https://www.supercontable.com/informacion/IVA_Impuesto_valor_a%C3%B1adido/Casilla_120_modelo_303.Operaciones_no_sujetas_por_.html)
- Gastos de difícil justificación 5%, max €2,000 (2026): [Quipu](https://getquipu.com/blog/gastos-de-dificil-justificacion/)
- IAE 844 / CNAE 7311: [Billeo](https://www.billeo.es/cnae/7311)
- AEAT free VeriFactu app: [Billin](https://www.billin.net/blog/?p=28831), [Alegra](https://blog.alegra.com/es/verifactu-aeat-gratuito/)
- VeriFactu dates (1 Jan 2027 companies, 1 Jul 2027 autónomos, RDL 15/2025): [Infoautónomos](https://www.infoautonomos.com/blog/verifactu-cuando-es-obligatorio-a-quien-afecta/)
- Revolut Business EEA: GBP sort code + account number: [Revolut help](https://help.revolut.com/en-ES/business/help/receiving-payments/transfers-info/where-can-i-find-my-account-details/)
- Stripe Bacs only for UK accounts: [Stripe docs](https://docs.stripe.com/payments/bacs-debit)
- Autónomo vs SL break-even €40-60k: [Billeo](https://www.billeo.es/blog/autonomo-o-sl-a-partir-de-cuanto-ganas-te-conviene-una-empresa-con-numeros)
