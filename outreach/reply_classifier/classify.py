"""Reply classification. Keyword-based by default (no API key required).

classify_reply() returns the coarse sentiment used by experiment tracking.
categorize_reply() is what the send engine acts on: it decides whether a
reply suppresses the sender, stops the sequence, or needs a human. It also
returns an `intent` (how much / send info / call me / GDPR question /
wrong person / already follow up ...) that the alert and the `replies`
list use to suggest the playbook reply. The engine stores the whole
verdict in replies.classification, so the intent is kept without any
engine change.

Always classify the *new* text only: our own email sits quoted underneath
most replies and contains "Reply 'no'", which would otherwise read as an
opt-out on every reply. Signatures and disclaimers are cut off too: they
contain words like "spam", "ICO" and "GDPR" in perfectly friendly replies.

Routing rules that matter (tests/integration/test_reply_classifier.py):
- A legal threat or accusation (spam, ICO, harassment, "breach of GDPR",
  "delete my data") is a complaint: suppressed, all sending paused, a
  human reads it.
- A GDPR *question* ("where did you get my email?", "is this GDPR OK?")
  is NOT a complaint and is never suppressed: category "unknown", intent
  "gdpr_question", a human answers it (SALES_PLAYBOOK section 1).
- Mixed signals ("not interested in paying per lead, but ...") are never
  auto-suppressed: "unknown", a human decides.
- A bare "no" is an opt-out (our footer asks for exactly that); a bare
  "yes" / "go on then" / "aye" is positive.
- When in doubt the answer is "unknown": every human reply is read by a
  person anyway, and a wrong "not interested" would suppress the address
  for good.
"""

import re

_POSITIVE_PHRASES = [
    "interested", "intrested", "interseted", "intersted", "sounds good", "sounds alright", "sounds ok",
    "let's talk", "lets talk", "book a call", "send over", "send me", "send us", "send some", "send it",
    "yes please", "would like to know more", "schedule", "give me a call", "give us a call", "call me",
    "ring me", "ring us", "give me a bell", "give us a bell", "bell me", "drop me a line", "give me a shout",
    "give us a shout", "tell me more", "more info", "more information", "how does it work", "how does this work",
    "how would it work", "how would this work", "what's involved", "whats involved", "happy to chat", "happy to talk",
    "go on then", "what's the catch", "whats the catch", "how much", "what does it cost", "what would it cost",
    "what do you charge", "what's the damage", "whats the damage", "price", "prices", "pricing", "fee", "fees",
    "a call", "a chat", "a quick call", "best number", "my number", "my mobile", "catch me on", "get me on",
    "let's do it", "lets do it", "count me in", "worth a go", "worth a try", "why not", "fire away",
    "what do you need", "keen", "up for", "open to", "love to", "be good to", "would be good",
]
_NEGATIVE_PHRASES = [
    "not interested", "not intrested", "not interseted", "not intersted", "no interest", "unsubscribe",
    "remove me", "no thanks", "no thank you", "no thnks", "no ta", "stop emailing", "not looking",
    "already have a provider", "already have a", "already have someone", "already got a", "already use", "already got someone", "got someone", "have someone",
    "not for us", "not for me", "not at this time", "we're fine", "we are fine", "were fine",
    "you're alright", "youre alright", "your alright", "we're alright", "were alright", "we are alright",
    "we're ok", "we're good", "all good thanks", "we're sorted", "were sorted", "sorted thanks", "sorted thank you",
    "don't need", "dont need", "do not need", "no need", "not required", "not needed", "not something we",
    "don't want", "dont want", "do not want", "not keen", "not really", "no thanks mate", "jog on", "do one",
    "sod off", "piss off", "bugger off", "get lost", "nah", "not relevant", "not applicable", "not what we do",
    "no longer trading", "ceased trading", "retired", "closed down", "shut down", "pass on this", "pass thanks",
    "going to pass on this", "we'll pass on this", "i'll pass on this", "i'll pass thanks", "we'll pass thanks", "pass on this one", "leave it", "leave it thanks", "not bothered", "not fussed",
]
_UNSUBSCRIBE_PHRASES = [
    "unsubscribe", "unsuscribe", "unsubcribe", "unsubscibe", "remove me", "remove us", "remove my", "remove our",
    "take me off", "take us off", "take my", "delete me", "delete us", "stop emailing", "stop sending",
    "stop contacting", "do not contact", "don't contact", "dont contact", "do not email", "don't email", "dont email",
    "don't send", "dont send", "do not send", "no more emails", "no further emails", "no further contact",
    "opt out", "opt-out", "opt me out", "cease contact", "stop these", "stop this", "lose my", "lose our",
]
# Explicit accusations, threats and legal requests only. Bare words like
# "spam", "ICO", "GDPR" or "data protection" appear in ordinary footers
# ("scanned for spam", "ICO registration Z123", "in line with GDPR") and must
# not trigger a complaint. A *question* about GDPR is handled separately.
_COMPLAINT_PATTERNS = [
    r"this is spam", r"\bspamm(ing|er|ed)\b", r"\bspam (email|mail|message|me|us)s?\b", r"\bis spam\b", r"\bas spam\b",
    r"\breport(ed|ing)? (you|this|it|your)\b", r"\breport (you|this|it) to\b",
    r"complain(t|ing|ed)? (to|with) the ico", r"(report|refer|complain)\w* (it |this |you |them )?to (the )?(ico|information commissioner)",
    r"\bthe ico\b", r"\bharass", r"unsolicited (email|mail|marketing|message|contact|approach)",
    r"breach of (gdpr|pecr|the regulations|data protection|the data protection)", r"\b(gdpr|pecr|data protection) (breach|violation|offence)",
    r"\billegal\b", r"\bunlawful\b", r"\bsolicitor", r"\blegal action\b", r"\bsue (you|your|velarqo)\b", r"\bsuing\b",
    r"\bblock(ed|ing)? (you|your|this)\b", r"\bblacklist", r"\bin breach\b",
    r"subject access request", r"\bdelete (all )?(my|our) (data|details|information|records|personal)\b",
    r"\b(erase|remove) (all )?(my|our) (data|details|information|records|personal)\b",
    r"\bno (right|permission|consent) to (email|contact|hold|process|have)\b", r"\bdid not (consent|agree|sign up)\b",
    r"\bnever (consented|agreed|signed up|opted in|gave you)\b", r"\bwithout (my|our) (consent|permission)\b",
    r"\bdisgrace", r"\bdisgusting\b", r"\bfed up (of|with) (these|your|getting)\b", r"\bhow many times\b",
    r"\bstop (spamming|harassing|pestering)\b", r"\bpester",
]
# A polite question about where the address came from, or whether this is
# allowed. The playbook answers it honestly, by hand, and suppresses only if
# asked to. Never a complaint on its own, never "not interested".
_GDPR_WHERE_FROM_PATTERNS = [
    r"(how|where) (did|do|have) you (get|got|obtain|find|source|have)\w* (my|our|this|these|the|hold of)",
    r"where (did|do|does) (you|this|it) (get|come)", r"where (did|have) you (got|get)", r"where('s| is| did) this (from|come)",
    r"\bwho gave you\b", r"\bhow (do|did) you have\b", r"\bhow (did|do) you know\b", r"\bhow have you got\b",
    r"\bscrap(ed|ing)\b", r"\bget hold of\b", r"\bbought (a |my )?(list|data|details)\b", r"\bpurchased (a )?(list|data)\b",
]
# Bare keywords count only when the reply actually asks something ("?"), so
# a "Data Protection: see our notice" line in a friendly reply is not one.
_GDPR_KEYWORD_PATTERNS = [
    r"\bgdpr\b", r"\bpecr\b", r"\bdata protection\b", r"\bprivacy (policy|notice)\b", r"\blawful basis\b",
    r"\blegitimate interest", r"\bconsent\b", r"\bopt(ed)?[ -]?in\b", r"\bmailing list\b", r"\bdata (source|came from)\b",
    r"\bpermission\b", r"\ballowed to\b", r"\blegal\b", r"\bcompliant\b",
]
# Unambiguous automation: nobody typed this to us.
_OUT_OF_OFFICE_PHRASES = [
    "out of office", "out of the office", "out the office", "automatic reply", "auto-reply", "autoreply", "auto reply",
    "automated reply", "automated response", "automated message", "automated email", "this is an automated",
    "annual leave", "on holiday", "on leave", "on vacation", "maternity leave", "paternity leave", "sick leave",
    "away from the office", "away from my desk", "currently away", "currently out", "i am away", "i'm away",
    "away until", "out until", "back in the office", "i'll be back", "i will be back", "return to the office",
    "on my return", "limited access to email", "limited access to my email", "will respond on my return",
    "will reply on my return", "i will be out", "i am out of the office", "i'm out of the office", "office is closed",
    "office is now closed", "closed for", "christmas shutdown", "not monitored", "unmonitored", "do not reply to this",
    "please do not reply", "ticket number", "ticket #", "ticket id", "case number", "case reference", "has been logged",
    "your request has been received", "your enquiry has been received",
]
# Helpdesk-style acknowledgements. Automated unless the text also carries a
# human signal (a question, a phone number, a yes/no), because people write
# "thanks for getting in touch, give me a call" too.
_AUTO_ACK_PHRASES = [
    "we have received your email", "we have received your message", "we have received your enquiry",
    "received your email and", "received your enquiry and", "received your message and", "has been received",
    "reference number", "thank you for contacting", "thanks for contacting", "thank you for your enquiry",
    "thanks for your enquiry", "thank you for your email", "thank you for getting in touch", "thanks for getting in touch",
    "will be in touch shortly", "will respond within", "aim to respond", "aim to reply", "will get back to you within",
    "will get back to you as soon", "will reply as soon as", "someone will be in touch", "a member of (our|the) team",
    "one of the team will", "one of our team will", "bank holiday",
]
# "Dave no longer works here": a person must re-route it, even when sent automatically.
_LEFT_PATTERNS = [
    r"\b(no longer|doesn't|does not|don't|dont) (work|works) (here|for|at|with)\b", r"\bhas left (the|our|this) (company|business|firm)\b",
    r"\bleft the (company|business|firm)\b", r"\bno longer (with|at|employed)\b", r"\bis no longer (here|with us)\b",
]
_BOUNCE_SENDERS = ("mailer-daemon@", "postmaster@", "mail-daemon@", "maildaemon@")
_AUTOMATED_SENDERS = _BOUNCE_SENDERS + ("bounce", "noreply@", "no-reply@", "no_reply@", "donotreply@", "do-not-reply@", "microsoftexchange")
_BOUNCE_SUBJECTS = (
    "undeliverable", "undelivered", "delivery status notification", "mail delivery failed", "mail delivery failure",
    "returned mail", "delivery has failed", "failure notice", "undelivered mail", "delivery failure", "delivery notification",
    "message not delivered", "could not be delivered", "couldn't be delivered", "wasn't delivered", "was not delivered",
    "non-delivery", "nondeliverable", "message blocked", "unable to deliver", "delivery problem",
    "returned to sender", "mail system error", "address not found", "recipient address rejected", "permanent error",
)
# "Delivery Status Notification (Delay)" is a warning, not a failure.
_NOT_A_BOUNCE = ("delay", "delayed", "warning", "will retry", "still trying", "temporarily deferred")
# A failure notice from a mail system that did not say so in the subject.
_BOUNCE_BODY = re.compile(
    r"(wasn't delivered|was not delivered|could not be delivered|couldn't be delivered|delivery (has )?failed|"
    r"delivery to the following recipient failed|address(es)? (couldn't|could not) be found|does not exist|"
    r"no such user|user unknown|unknown user|recipient (address )?rejected|mailbox (unavailable|not found|does not exist)|"
    r"\b55[0-9][ -]5\.\d\.\d|\b550\b|permanent(ly)? (fail|error)|unable to deliver|not delivered to)",
    re.IGNORECASE,
)
# Where a reply's own words end and the signature/disclaimer starts.
_SIGNATURE_START = re.compile(
    r"^\s*(--\s*$|__+\s*$|kind regards|best regards|warm regards|regards\b|rgds\b|many thanks|thanks,?\s*$|thank you,?\s*$|"
    r"cheers,?\s*$|ta,?\s*$|all the best|best wishes|yours (sincerely|faithfully)|"
    r"registered (in|office|company|address|number)|company (registration|reg|number|no)|"
    r"this (e-?mail|message|communication) (and any|is confidential|may|is intended|contains)|"
    r"disclaimer|confidentiality|vat (no|number|reg)|sent from (my|outlook|mail))",
    re.IGNORECASE,
)
# A one-word "no" / "stop" is exactly what our footer asks people to send.
_BARE_OPT_OUT = re.compile(r"^\W*(no+|nope|stop|unsubscribe|remove|nah mate|no thanks|no ta|no thank you|no thanks mate)\W*$")
# A one-word yes is a yes.
_BARE_YES = re.compile(
    r"^\W*(yes|yes please|yeah|yep|yup|aye|ok|okay|sure|go on|go on then|sounds good|why not|please do|fine|"
    r"yes sure|yeah sure|yeah ok|ok then|alright|alright then|sound|yes mate|yeah mate|yes pls|y|ye|yea)\W*$"
)
_PHONE = re.compile(r"(\+44\s?\d|\b0[1-9])[\d\s]{8,12}\d")

CATEGORIES = ("bounce", "out_of_office", "unsubscribe", "complaint", "not_interested", "positive", "unknown")

# Intents a human cares about when answering. Labels are what the alert and
# the `replies` list show; SALES_PLAYBOOK section 1 says what to send.
INTENTS = {
    "call_me": "wants a call",
    "how_much": "asks how much",
    "send_info": "wants info",
    "yes": "said yes",
    "interested": "interested",
    "already_follow_up": "says they already follow up",
    "gdpr_question": "GDPR / where-did-you-get-my-email question",
    "wrong_person": "wrong person / forwarded / left",
    "later": "not now, maybe later",
    "mixed": "mixed signals, read it",
    "question": "asks something",
    "legal": "legal threat or accusation",
}

_INTENT_PATTERNS = {
    "call_me": [
        r"\b(call|ring|phone|bell|buzz) (me|us|him|her|the office|anytime|any time|tomorrow|today|monday|tuesday|wednesday|thursday|friday)\b",
        r"\bgiv(e)? (me|us) a (call|ring|bell|buzz|shout)\b", r"\b(bell|ring) me\b", r"\bdrop me a (line|call)\b",
        r"\b(office|mobile|work|landline) (number|no\.?|num)\b", r"\ba (bell|ring|buzz)\b",
        r"\b(best|my) (number|mobile|phone|no\.?|num)\b", r"\bcatch me on\b", r"\bget me on\b", r"\bon this number\b",
        r"\b(book|arrange|set up|sort) a (call|chat|meeting)\b", r"\bcalendly\b", r"\bwhen (suits|are you free|can you)\b",
        r"\b(a|quick|short) (call|chat) (would|works|is fine|suits)\b", r"\bhappy to (chat|talk|have a call)\b",
        r"\bfree (for a (call|chat)|to (talk|chat))\b", r"\b(call|ring|phone) (the )?(office|shop|yard)\b",
    ],
    "how_much": [
        r"\bhow much\b", r"\bwhat('s| is| does| would) (it|this|that) (cost|charge)", r"\bwhat do you charge\b",
        r"\bwhat('s| is) the (damage|cost|price|fee|charge)", r"\b(cost|costs|price|prices|pricing|fee|fees|charge|charges|rates?)\b",
        r"\bper (lead|survey|booking|appointment|job)\b", r"\bupfront\b", r"\bup front\b", r"\bcommission\b",
        r"\bpay(ment)? (terms|structure)\b", r"\bhow (do|does|would) (you|it|this|the) (get paid|charge|bill|pricing)\b",
    ],
    "send_info": [
        r"\bsend (me|us|over|some|more|through|across|it|them|what|the|your|a|an)\b", r"\bmore (info|information|details)\b",
        r"\b(some|any|the|further) (info|information|details)\b", r"\bin writing\b", r"\bby email\b", r"\bemail (me|us) (some|the|more|over)\b",
        r"\bbrochure\b", r"\bliterature\b", r"\bwhat (you|you've|youve) (do|offer|got)\b", r"\bbit more (detail|info)\b",
        r"\bhow (does|would|will) (it|this|that) work\b", r"\bexplain\b", r"\btell me more\b", r"\bwhat('s| is) involved\b",
        r"\bmore about\b", r"\bdetails\b",
    ],
    "already_follow_up": [
        r"\b(we|i) (already|do|always) (follow|chase|do (our|the|this)|handle|manage)",
        r"\b(our|my) own (follow|chasing|system|crm|team|admin|process)", r"\bfollow (them |these |those |quotes )?up (ourselves|in[- ]house|already|myself)\b",
        r"\bchase (them|these|those|quotes|our own)\b", r"\bin[- ]house\b", r"\bgot (that|this|it) covered\b", r"\balready do (that|this|it)\b",
        r"\balready (chase|chasing|following|doing)\b", r"\bdo (that|this|it) ourselves\b", r"\bcovered thanks\b",
        r"\b(crm|system|software|team) (does|handles|chases|takes care of) (that|this|it|them|those)\b",
        r"\bdeal with (that|this|those|our own|it) ourselves\b",
    ],
    "wrong_person": [
        r"\b(wrong|not the right|not the best|not the correct) (person|contact|department|company|firm|email|address)\b",
        r"\b(forward|forwarded|pass|passed|sent|send) (this|it|your email|your message|that|the email|the message|on) (on |over |along )?to\b",
        r"\b(forwarded|passed) (this|it|your email)\b", r"\bi'?ve (forwarded|passed|sent) (this|it|your)\b",
        r"\b(speak|talk) (to|with) (dave|steve|the owner|the boss|the director|our|my|him|her)\b",
        r"\b(contact|try|email) (the owner|the boss|the director|our|my|him|her)\b",
        r"\b(is|are) the (one|person|man|guy|best|right person) (to|for|who)\b", r"\bdeals? with (that|this|those|the quotes|sales|marketing)\b",
        r"\b(i|we) (just|only) (do|handle|look after) (the|our) (accounts|books|admin|invoices|payroll)\b",
        r"\b(not|aren't|are not|we're not|we are not) (a|an) (window|roofing|installer|fitting|installation)\b",
        r"\bwe (don't|do not|dont) (do|fit|install|sell) (windows|doors|roofs|roofing|conservatories)\b",
        r"\bwe('re| are) (plumbers|electricians|builders|an accountancy|a (law|accountancy|recruitment) firm|not in that (trade|line))\b",
        r"\byou('ve| have) got the wrong\b", r"\bwrong (company|firm|business|number|email)\b", r"\btry (sales|info|enquiries|the office)@",
        r"\b(his|her|their) (email|address|number) is\b", r"\bbest (person|contact) (is|would be)\b",
        r"\bhe'?s (the|your) (man|guy|one)\b", r"\bshe'?s (the|your) (one|woman|person)\b",
    ] + _LEFT_PATTERNS,
    "later": [
        r"\b(maybe|perhaps|possibly|try) (next|in the|again in|later|after)\b", r"\bnot (right )?now\b", r"\bnot at the (moment|minute)\b",
        r"\b(next|new) year\b", r"\bin the (spring|summer|autumn|winter|new year)\b", r"\bafter (christmas|xmas|easter|the summer)\b",
        r"\b(too|really|very|rushed off|snowed under|up to my eyes) busy\b", r"\bflat out\b", r"\bsnowed under\b",
        r"\b(come|get) back to (me|us) (in|after|next)\b", r"\b(circle|check|come) back\b", r"\btouch base\b", r"\bbad time\b",
        r"\bnot (a|the) (good|right|best) time\b", r"\bbooked (up|solid|out)\b", r"\bin a few (weeks|months)\b", r"\bmonths? time\b",
        r"\bquiet(er)? (period|time|patch)\b", r"\bwhen things (calm|quieten|settle)\b",
    ],
}

# Urgency for alerts: these are answered within the hour.
URGENT_CATEGORIES = ("positive", "unknown", "complaint")


def classify_reply(reply_text: str) -> str:
    text = (reply_text or "").lower()

    if any(phrase in text for phrase in _NEGATIVE_PHRASES):
        return "negative"
    if any(phrase in text for phrase in _POSITIVE_PHRASES):
        return "positive"
    return "maybe"


_QUOTE_MARKER = re.compile(
    r"^(on .+wrote:?|-{2,}\s*original message\s*-{2,}|-{2,}\s*forwarded message\s*-{2,}|from:\s.+|sent from my .*|"
    r"sent from outlook.*|get outlook for .*|_{5,})$",
    re.IGNORECASE,
)


def strip_quoted(body: str) -> str:
    """The reply's own new text: drop quoted lines and everything after an
    'On ... wrote:' / 'From:' / '-----Original Message-----' marker."""
    lines = (body or "").splitlines()
    kept = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if _QUOTE_MARKER.match(stripped):
            break
        # Gmail wraps "On <date>, <name> <email>" / "wrote:" over two lines on narrow clients.
        if re.match(r"^on .{8,}$", stripped, re.IGNORECASE) and i + 1 < len(lines) and lines[i + 1].strip().lower().endswith("wrote:"):
            break
        if stripped.startswith(">"):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def own_words(new_text: str) -> str:
    """The message before the signature/disclaimer (always keeps line one)."""
    lines = new_text.splitlines()
    for i, line in enumerate(lines):
        if i > 0 and _SIGNATURE_START.match(line):
            return "\n".join(lines[:i]).strip()
    return new_text


def _has(text: str, phrases) -> bool:
    return any(re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", text) for p in phrases)


def _any(text: str, patterns) -> bool:
    return any(re.search(p, text) for p in patterns)


def _without(text: str, phrases) -> str:
    for p in phrases:
        text = re.sub(rf"(?<![a-z]){re.escape(p)}(?![a-z])", " ", text)
    return text


def _gdpr_question(text: str) -> bool:
    if _any(text, _GDPR_WHERE_FROM_PATTERNS):
        return True
    return "?" in text and _any(text, _GDPR_KEYWORD_PATTERNS)


def _looks_like_bounce(sender: str, subj: str, new_text: str) -> bool:
    if any(s in sender for s in _AUTOMATED_SENDERS) and _BOUNCE_BODY.search(new_text):
        return True
    return sender.startswith(_BOUNCE_SENDERS) or any(s in subj for s in _BOUNCE_SUBJECTS)


def _intent(text: str, category: str, positive: bool, negative: bool) -> str | None:
    """Best single intent for the alert, in the order a human would act on it."""
    if category == "positive":
        if _any(text, _INTENT_PATTERNS["call_me"]) or _PHONE.search(text):
            return "call_me"
        if _any(text, _INTENT_PATTERNS["how_much"]):
            return "how_much"
        if _any(text, _INTENT_PATTERNS["send_info"]):
            return "send_info"
        if _BARE_YES.match(text):
            return "yes"
        return "interested"
    if category == "unknown":
        if _gdpr_question(text):
            return "gdpr_question"
        for intent in ("wrong_person", "already_follow_up", "later"):
            if _any(text, _INTENT_PATTERNS[intent]):
                return intent
        if negative and positive:
            return "mixed"
        if "?" in text:
            return "question"
        return None
    if category == "complaint":
        return "legal"
    if category == "not_interested" and _any(text, _INTENT_PATTERNS["later"]):
        return "later"
    return None


def categorize_reply(from_email: str, subject: str, body: str, auto_submitted: bool = False) -> dict:
    """-> {"category", "intent", "label", "sentiment", "suppress", "stops_sequence", "needs_human"}

    Order: bounce, complaint, opt-out, "X has left", auto-reply (header or
    unambiguous wording), GDPR question, wrong person, helpdesk auto-ack
    without any human signal, mixed signals, not interested, positive,
    unknown. Opt-outs and complaints are checked before out-of-office, so
    "I'm away, but please remove us" is an opt-out. `auto_submitted` comes
    from the Auto-Submitted / X-Autoreply / Precedence headers."""
    sender = (from_email or "").lower()
    subj = (subject or "").lower()
    new_text = own_words(strip_quoted(body).lower())
    first_line = new_text.splitlines()[0].strip() if new_text else ""
    subj_and_text = f"{subj} {new_text}"

    bounce_like = _looks_like_bounce(sender, subj, new_text)
    negative = _has(new_text, _NEGATIVE_PHRASES)
    # "not interested" must not count as "interested": judge the positive
    # words on what is left once the negative phrases are taken out.
    residual = _without(new_text, _NEGATIVE_PHRASES)
    positive = _has(residual, _POSITIVE_PHRASES) or bool(_PHONE.search(new_text)) or any(
        _any(residual, _INTENT_PATTERNS[k]) for k in ("call_me", "how_much", "send_info"))
    bare_yes = bool(_BARE_YES.match(new_text) or _BARE_YES.match(first_line))
    human_signal = positive or negative or bare_yes or "?" in new_text or bool(_PHONE.search(new_text))
    strong_auto = auto_submitted or _has(subj_and_text, _OUT_OF_OFFICE_PHRASES)
    auto_ack = _has(subj_and_text, _AUTO_ACK_PHRASES)

    if bounce_like and not any(w in subj for w in _NOT_A_BOUNCE):
        category = "bounce"
    elif bounce_like:
        category = "out_of_office"            # a delay warning: an automatic notice, not a person
    elif _any(new_text, _COMPLAINT_PATTERNS):
        category = "complaint"
    elif _BARE_OPT_OUT.match(new_text) or _BARE_OPT_OUT.match(first_line) or _has(new_text, _UNSUBSCRIBE_PHRASES):
        category = "unsubscribe"
    elif _any(new_text, _LEFT_PATTERNS):
        category = "unknown"                  # the contact has gone: a human re-routes, the sequence stops
    elif strong_auto:
        category = "out_of_office"
    elif _gdpr_question(new_text):
        category = "unknown"                  # a question, answered by hand; never suppressed automatically
    elif _any(new_text, _INTENT_PATTERNS["wrong_person"]) and not positive:
        category = "unknown"                  # someone else is the contact
    elif auto_ack and not human_signal:
        category = "out_of_office"
    elif negative and (positive or bare_yes):
        category = "unknown"                  # "not interested in X but would do Y": never auto-suppressed
    elif negative:
        category = "not_interested"
    elif positive or bare_yes:
        category = "positive"
    else:
        category = "unknown"

    intent = _intent(new_text, category, positive, negative)
    return {
        "category": category,
        "intent": intent,
        "label": label(category, intent),
        "sentiment": {"positive": "positive", "unknown": "maybe"}.get(
            category, None if category in ("bounce", "out_of_office") else "negative"
        ),
        # bounce suppresses the address; people who said no are never emailed again
        "suppress": category in ("bounce", "unsubscribe", "complaint", "not_interested"),
        # an auto-reply is not a person answering, so the sequence carries on
        "stops_sequence": category not in ("out_of_office",),
        # a person reads every human reply (volume is tiny), so a wrong
        # automatic opt-out of an interested firm is caught the same day
        "needs_human": category not in ("bounce", "out_of_office"),
    }


def label(category: str, intent: str | None = None) -> str:
    """Short human label: 'POSITIVE: asks how much', 'READ IT: GDPR ... question'."""
    base = {
        "positive": "POSITIVE", "unknown": "READ IT", "complaint": "COMPLAINT (sending paused)",
        "not_interested": "not interested", "unsubscribe": "opt-out", "out_of_office": "auto-reply", "bounce": "bounce",
    }.get(category, category or "?")
    text = INTENTS.get(intent) if intent else None
    return f"{base}: {text}" if text and intent not in ("interested", "legal") else base
