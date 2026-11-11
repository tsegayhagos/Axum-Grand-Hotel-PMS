# Module 05: Housekeeping Management & Engineering Maintenance

## 1. Overview
Coordinates room cleanliness, hygiene standards, daily room attendant sheets, minibar replenishments, and engineering work orders.

## 2. Housekeeping Task Automation (`hotel.housekeeping.task`)
- **Cleaning Task Classifications:**
  - `departure_clean`: Deep turnover cleaning triggered automatically upon guest check-out.
  - `daily_clean`: Routine stayover cleaning for in-house guests.
  - `turndown`: Evening bed preparation, fresh towels, confectionery placement.
  - `deep_clean`: Scheduled periodic intensive maintenance wash.
  - `touch_up`: Pre-arrival inspection refresh.
- **Sanitation Checklist:**
  - Bed dressed with fresh linens.
  - Bathroom scrubbed, disinfected, and sealed.
  - Toiletries, towels, and slippers replenished.
  - Carpets vacuumed / hard floors sanitized.
  - Trash removed and bins relined.
- **Minibar Tracking & Auto-Billing:**
  - Attendant records consumed items during cleaning.
  - Supervisor clicks **"Post Minibar Charges"** to push charges directly to the in-house guest's folio line.

## 3. Engineering & Maintenance (`hotel.maintenance.request`)
- **Category Classifications:** HVAC / Air Conditioning, Plumbing, Electrical, RFID Door Locks, Wi-Fi/Smart TV, Furniture.
- **Urgency / Priority:** Normal, High, Emergency.
- **Out of Order (OOO) Automatic Room Locking:**
  - Enabling `block_room` automatically flags `hotel.room` as `maintenance`.
  - Blocks front desk receptionists from assigning the room to incoming guests.
  - Upon technician resolution (`action_mark_resolved`), the lock is released and room status is reverted to `clean` for final inspection.
