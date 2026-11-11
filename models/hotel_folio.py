# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class HotelFolio(models.Model):
    _name = 'hotel.folio'
    _description = 'Hotel Guest Master Folio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Folio Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    partner_id = fields.Many2one('res.partner', string='Billing Contact / Guest', required=True, tracking=True)
    reservation_id = fields.Many2one('hotel.reservation', string='Linked Reservation', ondelete='cascade', tracking=True)
    room_id = fields.Many2one('hotel.room', string='Room Number')

    state = fields.Selection([
        ('open', 'Open (Active In-House)'),
        ('closed', 'Closed (Fully Settled)'),
        ('cancelled', 'Cancelled / Void'),
    ], string='Folio State', default='open', tracking=True, required=True)

    line_ids = fields.One2many('hotel.folio.line', 'folio_id', string='Charge Items')
    payment_ids = fields.One2many('hotel.folio.payment', 'folio_id', string='Payments & Deposits')

    # Totals
    total_room_charges = fields.Monetary(string='Room Charges', compute='_compute_totals', store=True, currency_field='currency_id')
    total_extras_charges = fields.Monetary(string='Incidental & Extra Services', compute='_compute_totals', store=True, currency_field='currency_id')
    total_tax = fields.Monetary(string='Applicable Taxes', compute='_compute_totals', store=True, currency_field='currency_id')
    total_charges = fields.Monetary(string='Total Folio Charges', compute='_compute_totals', store=True, currency_field='currency_id')
    total_payments = fields.Monetary(string='Total Payments Received', compute='_compute_totals', store=True, currency_field='currency_id')
    balance_due = fields.Monetary(string='Balance Due', compute='_compute_totals', store=True, currency_field='currency_id')

    invoice_id = fields.Many2one('account.move', string='Generated Odoo Customer Invoice', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.folio') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.price_subtotal', 'line_ids.charge_type', 'payment_ids.amount')
    def _compute_totals(self):
        for rec in self:
            room = sum(line.price_subtotal for line in rec.line_ids if line.charge_type == 'room')
            extras = sum(line.price_subtotal for line in rec.line_ids if line.charge_type not in ('room', 'tax', 'discount'))
            tax = sum(line.price_subtotal for line in rec.line_ids if line.charge_type == 'tax')
            discounts = sum(line.price_subtotal for line in rec.line_ids if line.charge_type == 'discount')
            
            rec.total_room_charges = room
            rec.total_extras_charges = extras
            rec.total_tax = tax
            rec.total_charges = (room + extras + tax) - abs(discounts)
            rec.total_payments = sum(p.amount for p in rec.payment_ids)
            rec.balance_due = rec.total_charges - rec.total_payments

    def _post_room_stay_charges(self):
        self.ensure_one()
        if not self.reservation_id:
            return
        res = self.reservation_id
        start_date = res.checkin_date.date()
        for night in range(res.nights):
            current_date = start_date + timedelta(days=night)
            self.env['hotel.folio.line'].create({
                'folio_id': self.id,
                'charge_type': 'room',
                'name': _("Room Accommodation Night %s (%s - %s)") % (night + 1, current_date, res.room_id.name if res.room_id else res.room_type_id.name),
                'quantity': 1,
                'unit_price': res.nightly_rate,
                'company_id': self.company_id.id,
                'date': current_date,
            })

    def action_register_payment_dialog(self):
        self.ensure_one()
        return {
            'name': _('Register Folio Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.folio.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_folio_id': self.id,
                'default_amount': self.balance_due if self.balance_due > 0 else 0.0,
                'default_company_id': self.company_id.id,
            }
        }

    def action_create_invoice(self):
        for rec in self:
            if rec.invoice_id:
                raise UserError(_("An invoice already exists for this folio (%s).") % rec.invoice_id.name)
            if not rec.line_ids:
                raise UserError(_("Folio has no charges to invoice."))

            move_lines = []
            for line in rec.line_ids:
                move_lines.append((0, 0, {
                    'name': line.name,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price,
                }))

            move = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': rec.partner_id.id,
                'company_id': rec.company_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': move_lines,
            })
            rec.invoice_id = move.id

    def action_close_folio(self):
        for rec in self:
            if rec.balance_due > 0.01:
                raise UserError(_("Cannot close folio: Outstanding balance of %s remains unpaid.") % rec.balance_due)
            rec.state = 'closed'


class HotelFolioLine(models.Model):
    _name = 'hotel.folio.line'
    _description = 'Hotel Folio Charge Line'
    _order = 'date asc, id asc'

    folio_id = fields.Many2one('hotel.folio', string='Folio', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    date = fields.Date(string='Posting Date', default=fields.Date.today, required=True)
    
    charge_type = fields.Selection([
        ('room', 'Room Accommodation Charge'),
        ('laundry', 'Laundry & Valet Service'),
        ('minibar', 'Minibar & Refreshments'),
        ('restaurant_pos', 'Restaurant / F&B POS'),
        ('valet', 'Valet & Parking Service'),
        ('transport', 'Airport Shuttle / Transport'),
        ('tax', 'City / Tourism Tax / VAT'),
        ('discount', 'Promotional / Manager Discount'),
        ('other', 'Miscellaneous / Incidental'),
    ], string='Charge Category', default='room', required=True)

    name = fields.Char(string='Charge Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.unit_price


class HotelFolioPayment(models.Model):
    _name = 'hotel.folio.payment'
    _description = 'Hotel Folio Payment Record'
    _order = 'payment_date desc, id desc'

    folio_id = fields.Many2one('hotel.folio', string='Folio', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    payment_date = fields.Date(string='Payment Date', default=fields.Date.today, required=True)
    amount = fields.Monetary(string='Payment Amount', currency_field='currency_id', required=True)
    
    payment_method = fields.Selection([
        ('cash', 'Cash (Front Desk Till)'),
        ('credit_card', 'Credit / Debit Card Terminal'),
        ('bank_transfer', 'Direct Bank Transfer / Wire'),
        ('direct_bill', 'Direct Bill / Corporate City Ledger'),
        ('mobile_money', 'Mobile Payment (CBE Birr / Telebirr / M-Pesa)'),
    ], string='Payment Method', default='credit_card', required=True)

    reference = fields.Char(string='Payment Ref / Terminal Auth Slip / Trans ID')
    notes = fields.Text(string='Payment Notes')

    def action_post_payment(self):
        """Confirm and record folio payment"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

