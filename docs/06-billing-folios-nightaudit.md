# Module 06: Billing, Guest Folios & Daily Night Audit

## 1. Overview
Governs hotel financial integrity, multi-service charge aggregation, split billing, payment processing, customer invoice generation, and the daily Night Audit rollover.

## 2. Guest Master Folio Architecture (`hotel.folio`)
- **Master Folio:** Created upon check-in; aggregates all charges incurred across the property.
- **Charge Categories (`hotel.folio.line`):**
  - Room Accommodation Nights (`room`)
  - Laundry & Valet Services (`laundry`)
  - Minibar Refreshments (`minibar`)
  - Restaurant & F&B Outlets (`restaurant_pos`)
  - Valet Parking & Airport Shuttle (`valet`, `transport`)
  - Municipal Tourism Taxes & VAT (`tax`)
  - Promotional & Manager Discretionary Rebates (`discount`)
- **Payments & Deposits (`hotel.folio.payment`):**
  - Front Desk Cash Till (`cash`)
  - Electronic Card Terminals (`credit_card`)
  - Wire / Bank Transfers (`bank_transfer`)
  - Corporate Direct Billing / City Ledger (`direct_bill`)
  - Mobile Money (`mobile_money` e.g., CBE Birr, Telebirr, M-Pesa)
- **Odoo Financial Integration (`action_create_invoice`):**
  - Generates standard Odoo `account.move` Customer Invoice linked directly to the chart of accounts and general ledger.

## 3. Daily Night Audit Process (`hotel.night.audit`)
Executed nightly by the Night Auditor or automated via daily cron (`ir.cron`):
1. **Discrepancy & Exception Audit:**
   - Detects all arrivals for today that failed to check in (flags as **Potential No-Shows**).
   - Detects all expected departures that failed to check out (flags as **Overstay Discrepancies**).
2. **Automated Room & Tax Posting:**
   - Posts nightly room rate and applicable taxes for every in-house guest (`state == 'checkin'`).
3. **Daily Revenue Snapshot Balancing:**
   - Aggregates daily room revenue, laundry revenue, minibar revenue, and total cash/card collections.
4. **Business Date Rollover:**
   - Advances system operational date to the subsequent business calendar day.
