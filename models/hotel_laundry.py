# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HotelLaundryService(models.Model):
    _name = 'hotel.laundry.service'
    _description = 'Hotel Laundry & Valet Service Item'
    _order = 'category, name'

    name = fields.Char(string='Garment / Item Name', required=True)
    code = fields.Char(string='Service Code', size=10)
    category = fields.Selection([
        ('gent', "Men's Wear"),
        ('lady', "Women's Wear"),
        ('children', "Children's Wear"),
        ('linen', 'Bedding & Linens'),
        ('special', 'Delicates / Evening Wear'),
    ], string='Item Category', default='gent', required=True)
    
    service_type = fields.Selection([
        ('wash_iron', 'Wash & Iron (Standard)'),
        ('dry_clean', 'Dry Cleaning'),
        ('press_only', 'Pressing / Ironing Only'),
        ('stain_removal', 'Special Stain Treatment'),
    ], string='Service Type', default='wash_iron', required=True)

    standard_price = fields.Float(string='Standard Price', required=True, default=10.0)
    express_price = fields.Float(string='Express Rush Price', compute='_compute_express_price', store=True)
    description = fields.Text(string='Care Instructions / Notes')
    active = fields.Boolean(default=True)

    @api.depends('standard_price')
    def _compute_express_price(self):
        for rec in self:
            rec.express_price = rec.standard_price * 1.5


class HotelLaundryOrder(models.Model):
    _name = 'hotel.laundry.order'
    _description = 'Guest Laundry & Valet Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_date desc, id desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    reservation_id = fields.Many2one('hotel.reservation', string='In-House Reservation', required=True, tracking=True)
    room_id = fields.Many2one(related='reservation_id.room_id', string='Room Number', store=True)
    partner_id = fields.Many2one(related='reservation_id.partner_id', string='Guest', store=True)

    order_date = fields.Datetime(string='Order Received Date', default=lambda self: fields.Datetime.now(), required=True)
    expected_delivery = fields.Datetime(string='Expected Delivery Time', compute='_compute_expected_delivery', store=True)
    actual_delivery = fields.Datetime(string='Delivered At')

    speed = fields.Selection([
        ('standard', 'Standard Service (24 Hours)'),
        ('express', 'Express Service (Rush 4 Hours - 50% Surcharge)'),
    ], string='Service Speed', default='standard', required=True, tracking=True)

    provider_type = fields.Selection([
        ('in_house', 'In-House Hotel Laundry'),
        ('external_vendor', 'Contracted External Dry Cleaner'),
    ], string='Processing Location', default='in_house', required=True)
    vendor_id = fields.Many2one('res.partner', string='External Vendor Partner')

    line_ids = fields.One2many('hotel.laundry.order.line', 'order_id', string='Garment Items')
    
    total_pieces = fields.Integer(string='Total Garments', compute='_compute_totals', store=True)
    subtotal = fields.Monetary(string='Service Subtotal', compute='_compute_totals', store=True, currency_field='currency_id')
    express_surcharge = fields.Monetary(string='Rush Express Surcharge', compute='_compute_totals', store=True, currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Laundry Charge', compute='_compute_totals', store=True, currency_field='currency_id')

    state = fields.Selection([
        ('draft', 'Draft Ticket'),
        ('received', 'Garments Collected & Tagged'),
        ('processing', 'Washing / Dry Cleaning in Process'),
        ('ready', 'Inspected & Ready for Delivery'),
        ('delivered', 'Delivered to Guest Room'),
        ('posted', 'Charged to Folio'),
        ('cancelled', 'Cancelled'),
    ], string='Order Status', default='draft', tracking=True, required=True)

    folio_line_id = fields.Many2one('hotel.folio.line', string='Posted Folio Charge Line', readonly=True)
    notes = fields.Text(string='Special Guest Instructions / Delicate Fabric Alert')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.laundry.order') or _('New')
        return super().create(vals_list)

    @api.depends('order_date', 'speed')
    def _compute_expected_delivery(self):
        for rec in self:
            if rec.order_date:
                hours = 4 if rec.speed == 'express' else 24
                rec.expected_delivery = rec.order_date + fields.Date.to_duration(hours=hours) if hasattr(fields.Date, 'to_duration') else fields.Datetime.add(rec.order_date, hours=hours)

    @api.depends('line_ids.quantity', 'line_ids.price_subtotal', 'speed')
    def _compute_totals(self):
        for rec in self:
            rec.total_pieces = sum(line.quantity for line in rec.line_ids)
            base = sum(line.price_subtotal for line in rec.line_ids)
            rec.subtotal = base
            rec.express_surcharge = (base * 0.5) if rec.speed == 'express' else 0.0
            rec.total_amount = rec.subtotal + rec.express_surcharge

    def action_confirm_received(self):
        self.write({'state': 'received'})

    def action_start_processing(self):
        self.write({'state': 'processing'})

    def action_mark_ready(self):
        self.write({'state': 'ready'})

    def action_mark_delivered(self):
        self.write({'state': 'delivered', 'actual_delivery': fields.Datetime.now()})

    def action_post_to_guest_folio(self):
        for rec in self:
            if not rec.reservation_id.folio_id:
                raise UserError(_("Cannot post laundry charge: In-house guest reservation does not have an active Folio."))
            if rec.state == 'posted' or rec.folio_line_id:
                raise UserError(_("This laundry order has already been charged to the folio."))
            if rec.total_amount <= 0:
                raise UserError(_("Laundry order total is zero. Add items before posting."))

            folio = rec.reservation_id.folio_id
            line = self.env['hotel.folio.line'].create({
                'folio_id': folio.id,
                'charge_type': 'laundry',
                'name': _("Laundry & Valet Order %s (%s pcs - %s)") % (rec.name, rec.total_pieces, dict(rec._fields['speed'].selection).get(rec.speed)),
                'quantity': 1,
                'unit_price': rec.total_amount,
                'company_id': rec.company_id.id,
                'date': fields.Date.today(),
            })
            rec.write({'state': 'posted', 'folio_line_id': line.id})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'posted':
                raise UserError(_("Cannot cancel an order that has already been posted to the folio. Please reverse the charge on the folio first."))
            rec.state = 'cancelled'


class HotelLaundryOrderLine(models.Model):
    _name = 'hotel.laundry.order.line'
    _description = 'Laundry Order Line Item'

    order_id = fields.Many2one('hotel.laundry.order', string='Laundry Order', ondelete='cascade', required=True)
    service_id = fields.Many2one('hotel.laundry.service', string='Garment / Service', required=True)
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    barcode_tag = fields.Char(string='Garment Laundry Tag / Barcode')

    @api.onchange('service_id')
    def _onchange_service(self):
        if self.service_id:
            self.unit_price = self.service_id.standard_price

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.unit_price
