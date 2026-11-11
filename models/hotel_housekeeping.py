# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HotelHousekeepingTask(models.Model):
    _name = 'hotel.housekeeping.task'
    _description = 'Housekeeping Room Cleaning Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    name = fields.Char(string='Task Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', store=True)

    room_id = fields.Many2one('hotel.room', string='Room Number', required=True, tracking=True)
    floor_id = fields.Many2one(related='room_id.floor_id', string='Floor', store=True)
    room_status = fields.Selection(related='room_id.status', string='Current Room Status')

    reservation_id = fields.Many2one('hotel.reservation', string='Associated Reservation')
    partner_id = fields.Many2one(related='reservation_id.partner_id', string='Guest In-House', store=True)

    task_type = fields.Selection([
        ('daily_clean', 'Stayover Daily Cleaning'),
        ('departure_clean', 'Checkout Turnaround Cleaning'),
        ('deep_clean', 'Periodic Deep Clean'),
        ('turndown', 'Evening Turndown Service'),
        ('touch_up', 'Pre-Arrival Touch-up'),
    ], string='Task Type', default='daily_clean', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High Priority'),
        ('2', 'Urgent / VIP Arrival'),
    ], string='Priority', default='0', tracking=True)

    attendant_id = fields.Many2one('res.users', string='Assigned Attendant', tracking=True)
    supervisor_id = fields.Many2one('res.users', string='Inspecting Supervisor')

    scheduled_date = fields.Date(string='Scheduled Date', default=fields.Date.today, required=True)
    start_time = fields.Datetime(string='Work Started At')
    end_time = fields.Datetime(string='Work Completed At')

    state = fields.Selection([
        ('pending', 'Pending Assignment'),
        ('in_progress', 'Cleaning In Progress'),
        ('cleaned', 'Cleaned (Awaiting Inspection)'),
        ('inspected', 'Inspected & Approved'),
        ('cancelled', 'Cancelled'),
    ], string='Cleaning Status', default='pending', tracking=True, required=True)

    # Standard Sanitation Checklist
    check_bed_linen = fields.Boolean(string='Linens Changed & Bed Dressed')
    check_bathroom_sanitized = fields.Boolean(string='Bathroom Scrubbed & Sanitized')
    check_amenities_restocked = fields.Boolean(string='Toiletries & Amenities Restocked')
    check_vacuumed = fields.Boolean(string='Floor Vacuumed / Mopped')
    check_trash_cleared = fields.Boolean(string='Trash Emptied')
    check_minibar = fields.Boolean(string='Minibar Verified')

    # Minibar Tracking on Housekeeping
    minibar_line_ids = fields.One2many('hotel.minibar.consumption', 'task_id', string='Minibar Consumed Items')
    minibar_total = fields.Monetary(string='Total Minibar Charge', compute='_compute_minibar_total', store=True, currency_field='currency_id')

    notes = fields.Text(string='Attendant Observations / Lost & Found')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.housekeeping.task') or _('New')
        return super().create(vals_list)

    @api.depends('minibar_line_ids.price_subtotal')
    def _compute_minibar_total(self):
        for rec in self:
            rec.minibar_total = sum(line.price_subtotal for line in rec.minibar_line_ids)

    def action_start_cleaning(self):
        self.write({
            'state': 'in_progress',
            'start_time': fields.Datetime.now()
        })

    def action_mark_cleaned(self):
        for rec in self:
            rec.write({
                'state': 'cleaned',
                'end_time': fields.Datetime.now()
            })
            if rec.room_id:
                rec.room_id.write({'status': 'clean'})

    def action_mark_inspected(self):
        for rec in self:
            rec.write({'state': 'inspected'})
            if rec.room_id:
                if rec.room_id.status != 'occupied':
                    rec.room_id.write({'status': 'inspected'})

    def action_post_minibar_charges(self):
        for rec in self:
            if not rec.reservation_id or not rec.reservation_id.folio_id:
                raise UserError(_("No active in-house folio linked to this housekeeping task to post minibar charges."))
            unposted = rec.minibar_line_ids.filtered(lambda l: not l.posted)
            if not unposted:
                raise UserError(_("No unposted minibar items found."))

            folio = rec.reservation_id.folio_id
            for line in unposted:
                self.env['hotel.folio.line'].create({
                    'folio_id': folio.id,
                    'charge_type': 'minibar',
                    'name': _("Minibar: %s x %s (Room %s)") % (line.item_name, line.quantity, rec.room_id.name),
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'company_id': rec.company_id.id,
                    'date': fields.Date.today(),
                })
                line.posted = True


class HotelMinibarConsumption(models.Model):
    _name = 'hotel.minibar.consumption'
    _description = 'Housekeeping Minibar Consumption Record'

    task_id = fields.Many2one('hotel.housekeeping.task', string='Housekeeping Task', ondelete='cascade', required=True)
    item_name = fields.Char(string='Minibar Item', required=True, default='Mineral Water / Soda / Snack')
    quantity = fields.Integer(string='Qty Consumed', default=1, required=True)
    unit_price = fields.Float(string='Unit Price', required=True, default=5.0)
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    posted = fields.Boolean(string='Charged to Folio', default=False, readonly=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.unit_price
