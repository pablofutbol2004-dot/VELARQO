# Attribution schema

Every billable result must be reconstructable from records.

## Contact keys
- client_id
- source_record_id
- campaign_contact_id
- campaign_id

## Source
- original_enquiry_date
- original_quote_date
- quote_value
- original_product
- original_status
- source_system
- source_provenance_class
- eligibility_status

## Messaging
- first_send_at
- channel
- message_variant
- delivered_at / delivery_status
- reply_at
- reply_class
- opt_out_at

## Booking
- qualified_at
- booking_created_at
- appointment_id
- appointment_at
- appointment_status: booked / cancelled / no_show / attended
- qualification_fields

## Downstream client outcome
- new_quote_at
- new_quote_value
- sale_status
- sale_at
- revenue_won
- lost_reason

## Billing
- result_id
- billable_boolean
- billable_reason
- credit_reason
- invoice_id
- billed_amount

## Attribution rules v0
1. no billing from manual spreadsheet memory;
2. pre-existing active opportunities excluded;
3. one homeowner opportunity cannot generate duplicate fees merely through rescheduling;
4. every dispute resolvable from timestamped source/reply/booking logs;
5. downstream sale revenue is reported separately unless commercial model explicitly bills on it.
