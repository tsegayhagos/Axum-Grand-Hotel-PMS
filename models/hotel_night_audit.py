# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta

class HotelNightAudit(models.Model):
    _name = 'hotel.night.audit'
    _description = 'Hotel Night Audit & Daily Financial Rollover'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    name = fields.Char(string='Audit Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    audit_date = fields.Date(string='Audit Business Date', default=fields.Date.today, required=True, tracking=True)
    next_business_date = fields.Date(string='New Rolled Business Date', compute='_compute_next_date', store=True)
    auditor_id = fields.Many2one('res.users', string='Night Auditor', default=lambda self: self.env.user, required=True)

    state = fields.Selection([
        ('draft', 'Initiated / Draft'),
        ('in_progress', 'Audit In Progress'),
        ('completed', 'Audit Closed & Rolled Over'),
        ('failed', 'Audit Blocked with Discrepancies'),
    ], string='Audit Status', default='draft', tracking=True, required=True)

    # Operational Check Figures
    total_salable_rooms = fields.Integer(string='Salable Rooms Inventory')
    occupied_rooms = fields.Integer(string='Occupied Rooms')
    occupancy_rate = fields.Float(string='Occupancy Rate (%)')
    
    arrivals_expected = fields.Integer(string='Expected Arrivals')
    arrivals_actual = fields.Integer(string='Arrivals Checked In')
    arrivals_pending = fields.Integer(string='Pending / Unchecked Arrivals')

    departures_expected = fields.Integer(string='Expected Departures')
    departures_actual = fields.Integer(string='Departures Checked Out')
    departures_pending = fields.Integer(string='Pending / Overstay Departures')

    # Financial Reconciliation
    daily_room_revenue = fields.Monetary(string='Room Charges Posted', currency_field='currency_id')
    daily_laundry_revenue = fields.Monetary(string='Laundry Charges', currency_field='currency_id')
    daily_minibar_revenue = fields.Monetary(string='Minibar Charges', currency_field='currency_id')
    daily_other_revenue = fields.Monetary(string='Other Extra Services', currency_field='currency_id')
    daily_total_revenue = fields.Monetary(string='Total Daily Gross Revenue', currency_field='currency_id')
    daily_payments_received = fields.Monetary(string='Total Collections / Payments', currency_field='currency_id')

    discrepancy_log = fields.Text(string='Audit Discrepancies & Exceptions Log')
    audit_notes = fields.Text(string='Night Auditor Report Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.night.audit') or _('New')
        return super().create(vals_list)

    @api.depends('audit_date')
    def _compute_next_date(self):
        for rec in self:
            rec.next_business_date = rec.audit_date + timedelta(days=1) if rec.audit_date else False

    def action_verify_discrepancies(self):
        for rec in self:
            rec.state = 'in_progress'
            today = rec.audit_date

            # Total salable rooms
            salable = self.env['hotel.room'].search_count([
                ('company_id', '=', rec.company_id.id),
                ('status', 'not in', ('out_of_service',))
            ])
            in_house = self.env['hotel.reservation'].search([
                ('company_id', '=', rec.company_id.id),
                ('state', '=', 'checkin'),
            ])
            rec.total_salable_rooms = salable
            rec.occupied_rooms = len(in_house)
            rec.occupancy_rate = (len(in_house) / salable * 100.0) if salable else 0.0

            # Arrivals
            expected_arr = self.env['hotel.reservation'].search([
                ('company_id', '=', rec.company_id.id),
                ('checkin_date', '>=', datetime.combine(today, datetime.min.time())),
                ('checkin_date', '<=', datetime.combine(today, datetime.max.time())),
            ])
            rec.arrivals_expected = len(expected_arr)
            rec.arrivals_actual = len(expected_arr.filtered(lambda r: r.state == 'checkin'))
            pending_arr = expected_arr.filtered(lambda r: r.state in ('draft', 'confirmed'))
            rec.arrivals_pending = len(pending_arr)

            # Departures
            expected_dep = self.env['hotel.reservation'].search([
                ('company_id', '=', rec.company_id.id),
                ('checkout_date', '>=', datetime.combine(today, datetime.min.time())),
                ('checkout_date', '<=', datetime.combine(today, datetime.max.time())),
            ])
            rec.departures_expected = len(expected_dep)
            rec.departures_actual = len(expected_dep.filtered(lambda r: r.state == 'checkout'))
            overstays = expected_dep.filtered(lambda r: r.state == 'checkin')
            rec.departures_pending = len(overstays)

            # Build log
            logs = []
            if pending_arr:
                logs.append(_("[WARNING] %s reservations have not checked in yet (Potential No-Shows).") % len(pending_arr))
                for p in pending_arr:
                    logs.append("  - %s: %s (Room %s)" % (p.name, p.partner_id.name, p.room_id.name or 'Unassigned'))
            if overstays:
                logs.append(_("[ALERT] %s guests expected to depart today have not checked out (Potential Overstay).") % len(overstays))
                for o in overstays:
                    logs.append("  - %s: %s (Room %s)" % (o.name, o.partner_id.name, o.room_id.name or 'Unknown'))

            # Financial snapshot for the audit date
            lines = self.env['hotel.folio.line'].search([
                ('company_id', '=', rec.company_id.id),
                ('date', '=', today),
            ])
            rec.daily_room_revenue = sum(l.price_subtotal for l in lines if l.charge_type == 'room')
            rec.daily_laundry_revenue = sum(l.price_subtotal for l in lines if l.charge_type == 'laundry')
            rec.daily_minibar_revenue = sum(l.price_subtotal for l in lines if l.charge_type == 'minibar')
            rec.daily_other_revenue = sum(l.price_subtotal for l in lines if l.charge_type not in ('room', 'laundry', 'minibar'))
            rec.daily_total_revenue = sum(l.price_subtotal for l in lines)

            payments = self.env['hotel.folio.payment'].search([
                ('company_id', '=', rec.company_id.id),
                ('payment_date', '=', today),
            ])
            rec.daily_payments_received = sum(p.amount for p in payments)

            rec.discrepancy_log = "\n".join(logs) if logs else _("No discrepancies found. All arrivals and departures verified clean.")

    def action_execute_night_audit(self):
        self.ensure_one()
        self.action_verify_discrepancies()
        
        # Mark completed and close business date
        self.write({
            'state': 'completed',
            'audit_notes': (self.audit_notes or '') + _("\nNight Audit finalized on %s by %s.") % (fields.Datetime.now(), self.env.user.name)
        })

    @api.model
    def run_night_audit_cron(self):
        """Automated daily cron runner"""
        companies = self.env['res.company'].search([])
        for comp in companies:
            audit = self.create({
                'company_id': comp.id,
                'audit_date': fields.Date.today(),
            })
            audit.action_execute_night_audit()
