# Current source notes — checked 2026-10-01

## Companies House

- Public Data API supports company search and company profiles.
- Advanced company search supports filters including company status, type, location and SIC codes, with up to 5,000 results per request according to the current reference.
- Officers and persons-with-significant-control endpoints are available.
- Use Companies House as legal-entity evidence, not as proof that a person still runs day-to-day sales.

Sources:
- https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/search/advanced-company-search
- https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference
- https://www.gov.uk/guidance/searching-the-companies-house-register

## FENSA

FENSA maintains a live installer search and states that approved installers are assessed for replacement-window/door Building Regulations compliance. Current listings may expose installer name, registration number, address, phone and email. Treat it as a strong trade/installation signal, not automatic outbound permission.

Sources:
- https://www.fensa.org.uk/find-installers
- https://fensahelp.zendesk.com/hc/en-gb/articles/360059449814-Find-and-Check-a-FENSA-Approved-Installer

## ICO — B2B direct marketing

- Corporate subscribers and individual subscribers are treated differently for PECR electronic-mail rules.
- The electronic-mail consent rule does not apply to corporate subscribers, but UK GDPR still applies to personal data such as a named work contact.
- Sender identity and valid opt-out are required.
- Sole traders and certain partnerships are treated like individuals for electronic-mail marketing.
- Publicly available personal data remains subject to UK GDPR.
- Objections/suppression must be respected.

Sources:
- https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/business-to-business-marketing/
- https://ico.org.uk/for-organisations/advice-for-small-organisations/direct-marketing-and-data-protection/marketing-and-data-protection-in-detail/
- https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/a-guide-to-lawful-basis/legitimate-interests/

## Gmail sender requirements

Current Gmail guidance requires sender authentication and recommends stronger alignment. Bulk senders (>5,000/day to personal Gmail) require SPF, DKIM and DMARC and one-click unsubscribe for marketing/subscribed mail; Google tightened enforcement in November 2025. Low-volume outbound should still use proper authentication and reputation monitoring.

Sources:
- https://support.google.com/mail/answer/81126?hl=en
- https://support.google.com/mail/answer/14229414?hl=en

## Email verification

Hunter currently exposes an Email Verifier API. Treat provider-specific statuses as adapter input and map to canonical statuses in your own database.

Source:
- https://help.hunter.io/en/articles/12633706-how-to-verify-emails-via-api-with-code-examples
