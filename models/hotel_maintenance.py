# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HotelMaintenanceRequest(models.Model):
    _name = 'hotel.maintenance.request'
    _description = 'Hotel Engineering & Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'

    name = fields.Char(string='Request Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    subject = fields.Char(string='Issue Summary', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)

    room_id = fields.Many2one('hotel.room', string='Room / Location', required=True, tracking=True)
    floor_id = fields.Many2one(related='room_id.floor_id', string='Floor', store=True)

    category = fields.Selection([
        ('hvac', 'HVAC / Air Conditioning / Heating'),
        ('plumbing', 'Plumbing / Bathroom / Water Leak'),
        ('electrical', 'Electrical / Lighting / Sockets'),
        ('keycard_lock', 'Electronic Door Lock / RFID Keycard'),
        ('tv_internet', 'Smart TV / Wi-Fi / Phone Ext.'),
        ('furniture', 'Furniture / Carpentry / Fixtures'),
        ('safety', 'Fire Alarm / Smoke Detector / Safe'),
        ('general', 'General Facility Maintenance'),
    ], string='Maintenance Category', default='general', required=True, tracking=True)

    priority = fields.Selection([
        ('0', 'Low (Non-Urgent)'),
        ('1', 'Normal (Standard Repair)'),
        ('2', 'High (Guest Inconvenience)'),
        ('3', 'Emergency (Room Uninhabitable)'),
    ], string='Priority', default='1', tracking=True)

    block_room = fields.Boolean(
        string='Place Room Out-of-Order (OOO)',
        default=False,
        help="If enabled, this room is removed from inventory and locked as Under Maintenance."
    )

    technician_id = fields.Many2one('res.users', string='Assigned Technician', tracking=True)
    reported_by = fields.Many2one('res.users', string='Reported By', default=lambda self: self.env.user)
    reported_date = fields.Datetime(string='Reported Date', default=fields.Datetime.now)
    resolved_date = fields.Datetime(string='Resolved Date')

    description = fields.Text(string='Detailed Defect Description')
    resolution_notes = fields.Text(string='Resolution / Work Carried Out')
    repair_cost = fields.Float(string='Total Parts / Repair Cost', default=0.0)

    state = fields.Selection([
        ('reported', 'Reported / Logged'),
        ('assigned', 'Assigned to Technician'),
        ('in_progress', 'Work in Progress'),
        ('resolved', 'Repaired & Resolved'),
        ('cancelled', 'Cancelled'),
    ], string='Ticket Status', default='reported', tracking=True, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.maintenance.request') or _('New')
            if vals.get('block_room') and vals.get('room_id'):
                room = self.env['hotel.room'].browse(vals['room_id'])
                room.write({'status': 'maintenance'})
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'block_room' in vals or 'room_id' in vals:
            for rec in self:
                if rec.block_room and rec.room_id and rec.state != 'resolved':
                    rec.room_id.write({'status': 'maintenance'})
        return res

    def action_assign_technician(self):
        self.write({'state': 'assigned'})

    def action_start_repair(self):
        self.write({'state': 'in_progress'})

    def action_mark_resolved(self):
        for rec in self:
            rec.write({
                'state': 'resolved',
                'resolved_date': fields.Datetime.now()
            })
            # Unlock room if it was blocked
            if rec.block_room and rec.room_id and rec.room_id.status == 'maintenance':
                rec.room_id.write({'status': 'clean'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancelled'})
            if rec.block_room and rec.room_id and rec.room_id.status == 'maintenance':
                rec.room_id.write({'status': 'available'})
