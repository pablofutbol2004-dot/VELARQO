# Canary runbook

The canary exists to discover implementation danger before scale, not to estimate conversion rate.

## Before send
- gate checker says READY;
- cohort frozen;
- suppression rechecked immediately before send;
- test messages sent to controlled addresses/numbers;
- reply routing and calendar route tested;
- emergency stop available.

## Canary size
Choose a deliberately small number relative to the pilot. The exact count depends on channel and risk. It should be large enough to exercise routing but small enough to inspect manually.

## Inspect every canary contact
Check:
- correct identity/product/context;
- delivery/bounce;
- reply capture;
- opt-out suppression;
- sentiment/complaint;
- duplicate sends;
- booking path;
- client response behavior;
- manual handling effort.

## Expansion rule
Expand only if the implementation is healthy. A booking is not evidence that the system is safe.
