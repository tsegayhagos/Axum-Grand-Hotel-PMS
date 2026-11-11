# Module 02: Property, Room Inventory & Dynamic Rate Plans

## 1. Overview
This module governs the hotel's physical inventory, room categorization, architectural layout (buildings, wings, floors), and dynamic rate plans.

## 2. Inventory Structure & Models
- **Building / Wing (`hotel.building`):** Segregates distinct towers, beach villas, or annexes.
- **Floor (`hotel.floor`):** Floors with sequenced levels and room associations.
- **Room Amenities (`hotel.room.amenity`):** Features like Gigabit Wi-Fi, 4K Smart TV, Laptop Safe, Jacuzzi, Ocean View Balcony.
- **Room Type (`hotel.room.type`):**
  - Defines bed configuration (King, Queen, Twin Beds, Suites).
  - Maximum occupancy constraints (`max_adults`, `max_children`).
  - Base nightly pricing and extra occupant supplements.
  - Real-time inventory counters (Total, Available, Occupied, Dirty, Maintenance).
- **Physical Room (`hotel.room`):**
  - Room Number / Label.
  - Real-time Room State Machine:
    * `available`: Vacant and ready for assignment.
    * `reserved`: Guaranteed for guest arrival today.
    * `occupied`: Guest in-house.
    * `dirty`: Vacant, awaiting housekeeping clean.
    * `clean`: Cleaned by room attendant, pending supervisor inspection.
    * `inspected`: Verified by supervisor, approved for check-in.
    * `maintenance`: Locked for engineering repair.
    * `out_of_service`: Long-term renovation / decommissioning.

## 3. Rate Plans & Yield Pricing (`hotel.rate.plan`)
Supports diverse revenue management strategies:
1. **Best Available Rate (BAR):** Baseline flexible pricing with standard cancellation terms.
2. **Non-Refundable:** Lower rate with immediate full payment requirement and zero cancellation refund.
3. **Corporate Negotiated:** Contracted flat rates or discounts for corporate accounts.
4. **Long Stay Special:** Automatic discounts for stays exceeding 7 or 14 nights.
5. **Meal Plan Bundles (`hotel.meal.plan`):**
   - **EP (European Plan):** Room Only.
   - **CP (Continental Plan):** Bed & Breakfast.
   - **MAP (Modified American Plan):** Half Board (Breakfast + Dinner).
   - **AP (American Plan):** Full Board (Breakfast, Lunch, Dinner).
   - **AI:** All-Inclusive.

## 4. Stay Restrictions & Controls
- **Minimum Length of Stay (MinLOS) / Maximum Length of Stay (MaxLOS).**
- **Closed to Arrival (CTA):** Prevents bookings checking in on peak days.
- **Closed to Departure (CTD):** Restricts departures on high-demand holiday transitions.
