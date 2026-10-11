# Grokbot task: do installers' quote forms offer a marketing opt-out?

Paste this whole brief to Grokbot. The general rules in `grokbot_tasks.md`
apply (public pages only, never log in, never solve CAPTCHAs, leave a cell
empty rather than guess).

**Most important rule for this task: NEVER submit, fill in or type into any
form.** Only look at it.

## Why we need this

UK law lets a business text or email someone who asked it for a quote only
if, **at the moment it took their details**, it gave them a simple way to
say "don't send me marketing" (an opt-out box, an opt-in box, or a clear
sentence). We need to know how many installers actually do that.

## Input

`D:\velarqo\data\agent_tasks\optout_sample.csv`. Columns: `id, trade,
company, website`. About 120 UK window/door, roofing and kitchen firms.
Do them in order. If you run out of time, stop after any row and save what
you have.

## For each row

1. Open the website. Find **every** place a homeowner can ask for a quote:
   a "Get a quote" / "Free quote" / "Contact" / "Book a survey" page, a
   pop-up, a form at the bottom of the home page, a quote calculator.
   Scroll to the bottom of each form, including the small print under the
   Submit button. Forms can load a few seconds late: wait for them.
2. Look at the form only. Record:
   - Is there a form? (`yes` / `no_form_phone_email_only` / `site_down`)
   - The form's page URL.
   - **Every checkbox and its exact label text**, word for word.
   - **Any sentence near the form about marketing, offers, newsletters,
     contacting you in future, or opting out**, word for word.
   - Is there a link to a privacy policy next to the form? (`yes` / `no`)
3. Open the privacy policy (footer or form link). Search the page for
   "marketing", "opt out", "unsubscribe", "newsletter", "offers". Copy
   **one** sentence that says whether they send marketing and how to stop
   it, word for word. If none, leave empty.
4. Note other ways to enquire shown on the site: WhatsApp button,
   Checkatrade/MyBuilder widget, live chat, phone number.
5. Classify `marketing_choice` with exactly one of:
   - `opt_out_box`: a box to tick to say NO to marketing
   - `opt_in_box`: a box to tick to say YES to marketing (box not pre-ticked)
   - `prechecked_box`: a marketing box that is already ticked
   - `form_text_opt_out`: a sentence at the form saying they may market
     to you and how to opt out, no box
   - `privacy_policy_only`: nothing at the form about marketing; only the
     privacy policy mentions it
   - `consent_to_enquiry_only`: only "I agree to the privacy policy" or
     "I consent to being contacted about my enquiry", nothing about
     marketing
   - `none`: nothing at all
   - `no_form`: no form exists

## Output

Save `D:\velarqo\data\agent_tasks\optout_sample_result.csv` with columns:

`id,trade,company,website,form_found,form_url,checkbox_labels,marketing_text_at_form,privacy_link_at_form,privacy_policy_marketing_sentence,other_enquiry_routes,marketing_choice,note`

Put quotes around any cell that contains commas. Separate several checkbox
labels with ` | `.

When done, also write three lines at the bottom of your chat reply: how many
rows you checked, the count for each `marketing_choice` value, and anything
surprising.
