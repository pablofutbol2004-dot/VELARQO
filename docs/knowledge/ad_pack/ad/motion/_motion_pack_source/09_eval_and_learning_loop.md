# 09 — Evaluation and Learning Loop

## Objective
Make the system improve over time without blindly copying high-performing videos.

---

# 1. Log every generation

Store:
- format ID/version
- mutation operators
- content topic
- duration
- asset types
- render QC scores
- human rating
- platform performance when available

---

# 2. Separate craft performance from topic performance

A reel can perform because of:
- topic
- hook
- distribution
- visual format
- timing
- audience fit

Do not automatically conclude that a visual format is strong from one viral result.

Compare formats across multiple topics and instances.

---

# 3. Component-level metrics

Track:
- hook retention
- average watch percentage
- completion rate
- rewatches
- saves/shares
- clicks/DMs when relevant

Map results back to:
- hook grammar
- format family
- scene count
- density curve
- visual style
- signature mechanic

---

# 4. Human review labels

Useful labels:
- polished
- clear
- fresh
- overdesigned
- generic
- confusing
- too fast
- too slow
- AI-looking
- excellent transition
- weak typography

These can become training/evaluation data.

---

# 5. Format promotion lifecycle

`experimental -> candidate -> production -> proven -> deprecated`

A new format becomes production-ready only after:
- several successful renders
- low QC failure rate
- consistent human approval
- manageable render cost

---

# 6. Mutation learning

Track which mutation combinations remain coherent.

Example:
- F02 + scrapbook material = good
- F02 + aggressive 3D camera + tiny labels = bad

Over time, build a compatibility matrix between:
- format families
- material languages
- motion families
- content types

This is more useful than generic prompt tuning.
