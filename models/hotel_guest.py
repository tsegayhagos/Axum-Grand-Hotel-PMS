# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_hotel_guest = fields.Boolean(string='Is Hotel Guest', default=True)
    vip_status = fields.Selection([
        ('standard', 'Standard Guest'),
        ('silver', 'Silver Member'),
        ('gold', 'Gold VIP'),
        ('platinum', 'Platinum Elite'),
        ('vip', 'VVIP / Dignitary'),
    ], string='VIP Status', default='standard', tracking=True)

    # Identification & Demographics
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('national_id', 'National Identity Card'),
        ('driving_license', 'Driving License'),
        ('residence_permit', 'Residence Permit'),
    ], string='ID Type', default='passport')
    id_number = fields.Char(string='ID / Passport Number', tracking=True)
    id_expiry_date = fields.Date(string='ID Expiry Date')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')

    # Hospitality Preferences
    bed_preference = fields.Selection([
        ('king', 'King Size'),
        ('twin', 'Twin Beds'),
        ('double', 'Double Bed'),
    ], string='Bed Preference')
    floor_preference = fields.Selection([
        ('high', 'High Floor'),
        ('low', 'Low Floor'),
        ('ground', 'Ground Floor (Accessible)'),
        ('quiet', 'Quiet Corner'),
    ], string='Floor / Location Preference')
    smoking_preference = fields.Selection([
        ('non_smoking', 'Non-Smoking (Strict)'),
        ('smoking', 'Smoking Allowed'),
    ], string='Smoking Preference', default='non_smoking')
    allergies = fields.Char(string='Known Allergies / Medical Notes')
    dietary_notes = fields.Char(string='Dietary Requirements (Halal, Kosher, Vegan, Gluten-Free)')
    guest_notes = fields.Text(string='General Guest Preferences / Notes')

    # Security & Blacklist
    is_blacklisted = fields.Boolean(string='Blacklisted', default=False, tracking=True)
    blacklist_reason = fields.Text(string='Blacklist Justification')

    # Metrics
    reservation_ids = fields.One2many('hotel.reservation', 'partner_id', string='Reservations')
    reservation_count = fields.Integer(string='Stay Count', compute='_compute_hotel_metrics')
    total_spent = fields.Monetary(string='Lifetime Spent', compute='_compute_hotel_metrics', currency_field='currency_id')
    last_stay_date = fields.Date(string='Last Departure Date', compute='_compute_hotel_metrics')

    @api.depends('reservation_ids.state', 'reservation_ids.total_amount')
    def _compute_hotel_metrics(self):
        for rec in self:
            stays = rec.reservation_ids.filtered(lambda r: r.state in ('checkout', 'checkin'))
            rec.reservation_count = len(stays)
            rec.total_spent = sum(stays.mapped('total_amount'))
            checkouts = stays.mapped('checkout_date')
            rec.last_stay_date = max(checkouts).date() if checkouts else False

    def action_view_guest_reservations(self):
        self.ensure_one()
        return {
            'name': _('Guest Reservations'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'list,form,calendar',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_view_guest_folios(self):
        self.ensure_one()
        return {
            'name': _('Guest Folios & Billing'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.folio',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
