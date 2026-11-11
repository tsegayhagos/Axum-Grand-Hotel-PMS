# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HotelKpiDashboard(models.Model):
    _name = 'hotel.kpi.dashboard'
    _description = 'Hospitality KPI Dashboard & Real-Time Performance Analytics'

    name = fields.Char(string='Dashboard', default='Real-time KPI Overview')
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    # Room Inventory Metrics
    total_rooms = fields.Integer(string='Total Rooms', compute='_compute_kpi_metrics')
    available_rooms = fields.Integer(string='Available & Inspected', compute='_compute_kpi_metrics')
    occupied_rooms = fields.Integer(string='In-House Occupied', compute='_compute_kpi_metrics')
    dirty_rooms = fields.Integer(string='Vacant Dirty', compute='_compute_kpi_metrics')
    maintenance_rooms = fields.Integer(string='Out of Order / Repair', compute='_compute_kpi_metrics')

    # Core Hospitality KPIs
    occupancy_rate = fields.Float(string='Occupancy Rate (%)', compute='_compute_kpi_metrics')
    adr = fields.Monetary(string='ADR (Average Daily Rate)', compute='_compute_kpi_metrics', currency_field='currency_id')
    revpar = fields.Monetary(string='RevPAR (Rev. Per Avail. Room)', compute='_compute_kpi_metrics', currency_field='currency_id')
    total_daily_revenue = fields.Monetary(string='Total Revenue Today', compute='_compute_kpi_metrics', currency_field='currency_id')

    # Today's Operations
    today_arrivals = fields.Integer(string='Arrivals Today', compute='_compute_kpi_metrics')
    today_departures = fields.Integer(string='Departures Today', compute='_compute_kpi_metrics')
    inhouse_vip_count = fields.Integer(string='VIP Guests In-House', compute='_compute_kpi_metrics')
    pending_hk_tasks = fields.Integer(string='Pending Housekeeping Tasks', compute='_compute_kpi_metrics')
    open_maintenance_tickets = fields.Integer(string='Open Maintenance Issues', compute='_compute_kpi_metrics')

    def _compute_kpi_metrics(self):
        for rec in self:
            comp_id = rec.company_id.id
            today = fields.Date.today()

            # Rooms
            rooms = self.env['hotel.room'].search([('company_id', '=', comp_id)])
            salable_rooms = rooms.filtered(lambda r: r.status not in ('out_of_service',))
            occupied = rooms.filtered(lambda r: r.status == 'occupied')

            rec.total_rooms = len(rooms)
            rec.available_rooms = len(rooms.filtered(lambda r: r.status in ('available', 'inspected', 'clean')))
            rec.occupied_rooms = len(occupied)
            rec.dirty_rooms = len(rooms.filtered(lambda r: r.status == 'dirty'))
            rec.maintenance_rooms = len(rooms.filtered(lambda r: r.status in ('maintenance', 'out_of_service')))

            # Occupancy %
            salable_count = len(salable_rooms)
            rec.occupancy_rate = (len(occupied) / salable_count * 100.0) if salable_count > 0 else 0.0

            # Today's In-House Reservations
            inhouse_res = self.env['hotel.reservation'].search([
                ('company_id', '=', comp_id),
                ('state', '=', 'checkin'),
            ])
            room_revenue = sum(res.nightly_rate for res in inhouse_res)
            
            # ADR & RevPAR
            rec.adr = (room_revenue / len(occupied)) if len(occupied) > 0 else 0.0
            rec.revpar = (room_revenue / salable_count) if salable_count > 0 else 0.0

            # Total charges posted today
            today_lines = self.env['hotel.folio.line'].search([
                ('company_id', '=', comp_id),
                ('date', '=', today),
            ])
            rec.total_daily_revenue = sum(l.price_subtotal for l in today_lines)

            # Operations
            rec.today_arrivals = self.env['hotel.reservation'].search_count([
                ('company_id', '=', comp_id),
                ('checkin_date', '>=', fields.Datetime.now().replace(hour=0, minute=0, second=0)),
                ('checkin_date', '<=', fields.Datetime.now().replace(hour=23, minute=59, second=59)),
            ])
            rec.today_departures = self.env['hotel.reservation'].search_count([
                ('company_id', '=', comp_id),
                ('checkout_date', '>=', fields.Datetime.now().replace(hour=0, minute=0, second=0)),
                ('checkout_date', '<=', fields.Datetime.now().replace(hour=23, minute=59, second=59)),
            ])
            rec.inhouse_vip_count = len(inhouse_res.filtered(lambda r: r.partner_id.vip_status in ('gold', 'platinum', 'vip')))
            rec.pending_hk_tasks = self.env['hotel.housekeeping.task'].search_count([
                ('company_id', '=', comp_id),
                ('state', 'in', ('pending', 'in_progress')),
            ])
            rec.open_maintenance_tickets = self.env['hotel.maintenance.request'].search_count([
                ('company_id', '=', comp_id),
                ('state', 'in', ('reported', 'assigned', 'in_progress')),
            ])
