# 02 — Identity and deduplication

## Match hierarchy

Strongest → weakest:

1. exact Companies House number
2. exact normalized canonical domain
3. exact legal name + postcode
4. exact phone + strong name similarity
5. fuzzy name/address only → manual review

## Normalize

- lowercase domains; remove protocol, `www`, trailing slash
- lowercase emails
- E.164-normalize phones where possible
- strip legal suffixes only for comparison, never from canonical legal name
- normalize whitespace/punctuation

## Never merge solely because

- names are similar
- two businesses share a registered office/accountant
- a group has several trading names
- one director appears at multiple companies

Create `merge_reason` and `merge_confidence` for every merge.
