<p align="center">
  <img src="static/description/logo.png" alt="Axum Grand Hotel Logo" width="180" />
</p>

# Axum Grand Hotel PMS — Enterprise Hotel Management System (Odoo 18)

**Axum Grand Hotel PMS** is a full-featured Odoo 18 hospitality and property management addon (`hotel_pms`) tailored for **Axum Grand Hotel** (Addis Ababa, Ethiopia; Currency: **ETB**).

Developed and maintained by **Tsegay Hagos**.

---

## Property & Author Details

- **Hotel Name:** Axum Grand Hotel
- **Location:** Addis Ababa, Ethiopia
- **Currency:** Ethiopian Birr (`ETB` / `Br`)
- **Phone:** `+251914387813`
- **Email:** `tsegayhagos1942@gmail.com`
- **Author / Maintainer:** Tsegay Hagos
- **License:** LGPL-3
- **Platform:** Odoo 18 (`18.0.1.0.0`)

---

## Core Operational Modules (7 Pillars)

| # | Module | Key Capabilities | Documentation |
|---|--------|------------------|---------------|
| 01 | **Auth, Multi-Tenancy & RBAC** | Multi-property isolation, Hotel Users, Security Groups (Manager, Front Desk, Housekeeping, Laundry, Maintenance, Night Auditor) | [01-auth-multitenancy-rbac.md](docs/01-auth-multitenancy-rbac.md) |
| 02 | **Property, Rooms & Rates** | Buildings, floors, room types, amenities, physical room inventory, dynamic rate plans & meal plans | [02-property-rooms-rates.md](docs/02-property-rooms-rates.md) |
| 03 | **Guest CRM & Front Desk** | Reservations, quick Check-In / Check-Out wizards, guest 360 profile, VIP tiers & room board | [03-guest-crm-frontdesk.md](docs/03-guest-crm-frontdesk.md) |
| 04 | **Laundry & Valet Service** | Valet orders, laundry service catalog, express surcharges & one-click guest folio charge posting | [04-laundry-valet-service.md](docs/04-laundry-valet-service.md) |
| 05 | **Housekeeping & Maintenance** | Attendant task board, room status workflows (`Clean` / `Dirty` / `Inspected`), minibar logs & maintenance tickets | [05-housekeeping-maintenance.md](docs/05-housekeeping-maintenance.md) |
| 06 | **Billing, Folios & Night Audit** | Guest folios, folio lines, payment posting, QWeb folio PDF statements & end-of-day Night Audit wizard | [06-billing-folios-nightaudit.md](docs/06-billing-folios-nightaudit.md) |
| 07 | **Reporting & Analytics** | Live KPI Executive Dashboard (Occupancy %, ADR, RevPAR, Total Daily Revenue) & daily financial summaries | [07-reporting-analytics.md](docs/07-reporting-analytics.md) |

---

## Addon Structure

```text
hotel_pms/
├── __init__.py
├── __manifest__.py
├── data/                # Sequences, cron jobs & default KPI dashboard record
├── docs/                # Module documentation (01 - 07)
├── models/              # ORM models for Front Desk, Rooms, Laundry, HK, Billing & KPIs
├── report/              # QWeb PDF Folio Statement report
├── security/            # RBAC groups, record rules & model ACLs
├── static/description/  # Axum Grand Hotel app icon & brand logo
├── views/               # Backend UI views & 7-module navigation menus
└── wizard/              # Check-In, Check-Out & Night Audit wizards
```

---

## Installation (Odoo 18)

1. Place `hotel_pms` inside a directory listed in your Odoo `addons_path`.
2. Restart Odoo and update the module list, or install/upgrade via CLI:
   ```bash
   python odoo-bin -c odoo.conf -d <your_db> -i hotel_pms
   ```
3. Configure your company profile (**Axum Grand Hotel**, **Addis Ababa**, **ETB** currency, `+251914387813`, `tsegayhagos1942@gmail.com`) under **Settings -> Companies**.
