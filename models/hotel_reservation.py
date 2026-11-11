# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'checkin_date desc, id desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Guest Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    # Stay Details
    checkin_date = fields.Datetime(string='Arrival Date & Time', required=True, default=lambda self: fields.Datetime.now(), tracking=True)
    checkout_date = fields.Datetime(string='Departure Date & Time', required=True, default=lambda self: fields.Datetime.now() + timedelta(days=1), tracking=True)
    nights = fields.Integer(string='Duration (Nights)', compute='_compute_nights', store=True)
    
    adults = fields.Integer(string='Adults', default=2, required=True)
    children = fields.Integer(string='Children', default=0)
    total_guests = fields.Integer(string='Total Guests', compute='_compute_total_guests', store=True)

    # Room Allocation
    room_type_id = fields.Many2one('hotel.room.type', string='Booked Room Type', required=True, tracking=True)
    room_id = fields.Many2one('hotel.room', string='Assigned Room Number', tracking=True)
    rate_plan_id = fields.Many2one('hotel.rate.plan', string='Rate Plan', tracking=True)
    meal_plan_id = fields.Many2one('hotel.meal.plan', string='Meal Plan')
    nightly_rate = fields.Monetary(string='Nightly Room Rate', currency_field='currency_id', required=True, default=100.0)

    # Channel & Booking Source
    channel = fields.Selection([
        ('walk_in', 'Walk-in (Front Desk)'),
        ('direct_web', 'Direct Website / Web Booking'),
        ('phone', 'Phone / Direct Call'),
        ('booking_com', 'Booking.com OTA'),
        ('expedia', 'Expedia Group'),
        ('airbnb', 'Airbnb / Vacation Rental'),
        ('corporate', 'Corporate Contract / B2B'),
        ('travel_agent', 'Travel Agent / Tour Operator'),
    ], string='Booking Channel / Source', default='walk_in', required=True)
    external_booking_ref = fields.Char(string='OTA / External Confirmation Code')

    # State Lifecycle
    state = fields.Selection([
        ('draft', 'Draft / Inquiry'),
        ('confirmed', 'Confirmed (Guaranteed)'),
        ('checkin', 'Checked In (In-House)'),
        ('checkout', 'Checked Out (Departed)'),
        ('cancel', 'Cancelled'),
        ('no_show', 'No-Show'),
    ], string='Reservation Status', default='draft', tracking=True, required=True)

    special_requests = fields.Text(string='Special Requests / Notes')

    # Financials & Folio
    folio_id = fields.Many2one('hotel.folio', string='Guest Master Folio', readonly=True)
    room_subtotal = fields.Monetary(string='Room Charges Subtotal', compute='_compute_financials', store=True, currency_field='currency_id')
    extras_subtotal = fields.Monetary(string='Extras Subtotal (Laundry/Minibar/Services)', compute='_compute_financials', store=True, currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Bill Amount', compute='_compute_financials', store=True, currency_field='currency_id')
    folio_balance = fields.Monetary(string='Outstanding Folio Balance', compute='_compute_financials', store=True, currency_field='currency_id')

    # Associated Operational Orders
    laundry_order_ids = fields.One2many('hotel.laundry.order', 'reservation_id', string='Laundry Orders')
    housekeeping_task_ids = fields.One2many('hotel.housekeeping.task', 'reservation_id', string='Housekeeping Tasks')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or _('New')
        return super().create(vals_list)

    @api.depends('checkin_date', 'checkout_date')
    def _compute_nights(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                delta = (rec.checkout_date.date() - rec.checkin_date.date()).days
                rec.nights = max(1, delta)
            else:
                rec.nights = 1

    @api.depends('adults', 'children')
    def _compute_total_guests(self):
        for rec in self:
            rec.total_guests = (rec.adults or 0) + (rec.children or 0)

    @api.onchange('room_type_id', 'rate_plan_id')
    def _onchange_room_and_rate(self):
        if self.room_type_id:
            base = self.room_type_id.base_price
            if self.rate_plan_id:
                if self.rate_plan_id.pricing_type == 'percent_discount':
                    base -= (base * (self.rate_plan_id.discount_percent / 100.0))
                elif self.rate_plan_id.pricing_type == 'percent_surcharge':
                    base += (base * (self.rate_plan_id.surcharge_percent / 100.0))
                elif self.rate_plan_id.pricing_type == 'fixed' and self.rate_plan_id.fixed_override_price > 0:
                    base = self.rate_plan_id.fixed_override_price
                if self.rate_plan_id.meal_plan_id:
                    self.meal_plan_id = self.rate_plan_id.meal_plan_id
            self.nightly_rate = base

    @api.depends('nights', 'nightly_rate', 'folio_id', 'folio_id.total_charges', 'folio_id.balance_due')
    def _compute_financials(self):
        for rec in self:
            rec.room_subtotal = rec.nights * rec.nightly_rate
            if rec.folio_id:
                rec.extras_subtotal = max(0.0, rec.folio_id.total_charges - rec.room_subtotal)
                rec.total_amount = rec.folio_id.total_charges
                rec.folio_balance = rec.folio_id.balance_due
            else:
                rec.extras_subtotal = 0.0
                rec.total_amount = rec.room_subtotal
                rec.folio_balance = rec.room_subtotal

    @api.constrains('checkin_date', 'checkout_date')
    def _check_dates(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date and rec.checkout_date <= rec.checkin_date:
                raise ValidationError(_("Check-out date must be strictly after Check-in date."))

    def action_confirm(self):
        for rec in self:
            if rec.partner_id.is_blacklisted:
                raise UserError(_("Guest '%s' is blacklisted! Reason: %s") % (rec.partner_id.name, rec.partner_id.blacklist_reason or 'No reason specified'))
            if rec.room_id and rec.room_id.status in ('dirty', 'maintenance', 'out_of_service'):
                raise UserError(_("Assigned Room %s is currently in '%s' status. Please reassign or clean the room before confirming.") % (rec.room_id.name, rec.room_id.status))
            rec.state = 'confirmed'
            if rec.room_id and rec.room_id.status == 'available':
                rec.room_id.status = 'reserved'

    def action_checkin(self):
        for rec in self:
            if not rec.room_id:
                raise UserError(_("Please assign a physical room number before checking in the guest."))
            if rec.room_id.status == 'occupied' and rec.room_id.current_reservation_id != rec:
                raise UserError(_("Room %s is already occupied by another guest!") % rec.room_id.name)
            
            # Transition room to occupied
            rec.room_id.write({'status': 'occupied'})
            rec.state = 'checkin'

            # Create or link master folio
            if not rec.folio_id:
                folio = self.env['hotel.folio'].create({
                    'reservation_id': rec.id,
                    'partner_id': rec.partner_id.id,
                    'company_id': rec.company_id.id,
                    'room_id': rec.room_id.id,
                })
                rec.folio_id = folio.id
                # Post initial room charge lines for the stay duration
                folio._post_room_stay_charges()

    def action_checkout(self):
        for rec in self:
            if rec.folio_id and rec.folio_id.balance_due > 0.01:
                raise UserError(_("Folio has an outstanding balance of %s %s. Please settle the balance before completing checkout.") % (rec.folio_id.balance_due, rec.currency_id.symbol or ''))
            
            # Mark room as dirty for housekeeping
            if rec.room_id:
                rec.room_id.write({'status': 'dirty'})
                # Automatically spawn departure cleaning task
                self.env['hotel.housekeeping.task'].create({
                    'room_id': rec.room_id.id,
                    'task_type': 'departure_clean',
                    'reservation_id': rec.id,
                    'company_id': rec.company_id.id,
                    'priority': 'high',
                })
            rec.state = 'checkout'
            if rec.folio_id:
                rec.folio_id.state = 'closed'

    def action_cancel(self):
        for rec in self:
            if rec.room_id and rec.room_id.status in ('reserved', 'occupied'):
                rec.room_id.write({'status': 'available'})
            rec.state = 'cancel'

    def action_no_show(self):
        for rec in self:
            if rec.room_id:
                rec.room_id.write({'status': 'available'})
            rec.state = 'no_show'

    def action_view_folio(self):
        self.ensure_one()
        return {
            'name': _('Guest Folio'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.folio',
            'view_mode': 'form',
            'res_id': self.folio_id.id,
        }
