# -*- coding: utf-8 -*-
{
    'name': 'Axum Grand Hotel PMS',
    'version': '18.0.1.0.0',
    'category': 'Industries/Hospitality',
    'summary': 'Enterprise Hotel PMS for Axum Grand Hotel (Addis Ababa): Multi-property, Front Desk, Housekeeping, Laundry, Folios, Night Audit & Analytics',
    'description': """
Axum Grand Hotel Management System (PMS) for Odoo 18
====================================================
Comprehensive Enterprise Hospitality & Property Management Platform for Axum Grand Hotel (Addis Ababa, Ethiopia, Currency: ETB), covering 7 key operational domains:

1. Auth, Multi-Tenancy & RBAC: Multi-property isolation, granular roles (Manager, Front Desk, Housekeeping, Laundry, Maintenance, Night Auditor).
2. Property, Rooms & Rates: Floors, room types, amenities, physical room inventory, dynamic rate plans, meal plans & seasonal pricing.
3. Guest CRM & Front Desk: Guest 360 profile, VIP tiers, reservation lifecycle, quick check-in / check-out workflows, tape chart view.
4. Laundry & Valet Service: Valet order management, service catalog, express surcharges, one-click guest folio charge posting.
5. Housekeeping & Maintenance: Attendant task assignment, room status transitions (Clean/Dirty/Inspected), minibar checks & maintenance ticketing.
6. Billing, Folios & Night Audit: Master & sub-folios, split billing, automatic room charge & tax posting, daily financial rollover wizard.
7. Hospitality KPIs & Analytics: Occupancy Rate (%), ADR, RevPAR, RevPAC, daily flash manager reports, financial summaries.

Contact: tsegayhagos1942@gmail.com | +251914387813 | Addis Ababa, Ethiopia
    """,
    'author': 'Tsegay Hagos',
    'website': 'https://github.com/tsegayhagos/axum-grand-hotel-pms',
    'depends': [
        'base',
        'mail',
        'account',
    ],
    'data': [
        # Security
        'security/hotel_security.xml',
        'security/ir.model.access.csv',

        # Data & Sequences
        'data/hotel_data.xml',
        'data/hotel_cron.xml',

        # Wizards
        'wizard/hotel_wizard_views.xml',

        # Views
        'views/hotel_room_views.xml',
        'views/hotel_guest_views.xml',
        'views/hotel_reservation_views.xml',
        'views/hotel_laundry_views.xml',
        'views/hotel_housekeeping_views.xml',
        'views/hotel_maintenance_views.xml',
        'views/hotel_folio_views.xml',
        'views/hotel_dashboard_views.xml',
        'views/hotel_night_audit_views.xml',
        'views/hotel_menus.xml',

        # Reports
        'report/hotel_reports.xml',
        'report/hotel_folio_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
