# Module 01: Multi-Tenancy, Authentication & Role-Based Access Control (RBAC)

## 1. Overview & Architecture
This module establishes the foundational multi-tenant and security framework for the Hotel Management System (PMS) in Odoo 18. It supports hotel chains operating multiple properties, independent boutique hotels, and regional branches within a single unified database instance.

## 2. Multi-Property / Multi-Tenancy Hierarchy
Odoo's multi-company architecture is leveraged to isolate and govern property data:
* **Hotel Chain / Holding (Parent Company):** Consolidated financial reporting, global guest profiles, unified brand standards.
* **Individual Hotel Properties (`res.company`):**
  * Dedicated room inventories (`hotel.room`), folios (`hotel.folio`), and front desk operations.
  * Localized tax configurations, chart of accounts, and cashier tills.
  * Multi-currency support per property with central conversion.

### Record Rules Enforcement
Each operational model implements an Odoo Record Rule:
```xml
<record id="hotel_room_comp_rule" model="ir.rule">
    <field name="name">Hotel Room Multi-Company</field>
    <field name="model_id" ref="model_hotel_room"/>
    <field name="global" eval="True"/>
    <field name="domain_force">['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]</field>
</record>
```

## 3. Role-Based Access Control (RBAC) Matrix

| Security Role | Group ID | Scope & Permissions | Key Operations |
|---|---|---|---|
| **Front Desk Receptionist** | `group_hotel_user` | Read/Write on Reservations, Guests, Rooms, Folios | Walk-in bookings, Check-In/Check-Out, Keycard issuance, Folio charge posting |
| **Housekeeping Attendant** | `group_hotel_housekeeping` | Read Rooms; Read/Write assigned Cleaning Tasks | View assigned cleaning list, toggle Clean status, report lost & found |
| **Housekeeping Supervisor** | `group_hotel_housekeeping_supervisor` | Full on Housekeeping & Minibar | Assign attendants, inspect cleaned rooms, approve room readiness, verify minibar charges |
| **Laundry & Valet Staff** | `group_hotel_laundry` | Read/Write Laundry Orders & Catalog | Tag garments, record wash/dry clean status, deliver to guest room, post charges to folio |
| **Maintenance Technician** | `group_hotel_maintenance` | Read/Write Maintenance Tickets & Out-of-Order locks | Log facility defects, lock rooms out-of-order, complete repairs, release rooms |
| **Night Auditor** | `group_hotel_night_auditor` | Read/Write Folios, Payments, and Night Audit engine | Reconcile daily arrivals/departures, run night audit, post daily room and tax charges, rollover business date |
| **Hotel General Manager** | `group_hotel_manager` | Administrator / Full Access | Set room rates, define policies, manage users, view executive KPI analytics & financial ledgers |

## 4. Audit Logging & Traceability
All critical transactional objects inherit from `mail.thread` and `mail.activity.mixin` to provide an indelible audit trail:
- Room status changes (who marked a room clean, inspected, or out of order).
- Financial ledger entries and manual charge overrides.
- Security deposit refunds and cancellations.
