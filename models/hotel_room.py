# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HotelRoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Hotel Room Amenity'
    _order = 'name'

    name = fields.Char(string='Amenity Name', required=True)
    icon = fields.Char(string='FontAwesome Icon / Code', default='fa-star')
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)


class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Hotel Room Type / Category'
    _order = 'sequence, name'

    name = fields.Char(string='Room Type Name', required=True)
    code = fields.Char(string='Code', size=10, required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    
    # Capacity
    max_adults = fields.Integer(string='Max Adults', default=2, required=True)
    max_children = fields.Integer(string='Max Children', default=1)
    max_occupancy = fields.Integer(string='Max Total Occupancy', compute='_compute_max_occupancy', store=True)
    bed_type = fields.Selection([
        ('single', 'Single Bed'),
        ('double', 'Double Bed'),
        ('queen', 'Queen Size'),
        ('king', 'King Size'),
        ('twin', 'Twin Beds'),
        ('suite', 'Master King + Sofa Bed'),
    ], string='Bed Configuration', default='king', required=True)
    room_size_sqm = fields.Float(string='Size (sqm)')

    # Pricing
    base_price = fields.Float(string='Base Nightly Rate', default=100.0, required=True)
    extra_adult_price = fields.Float(string='Extra Adult Supplement', default=25.0)
    extra_child_price = fields.Float(string='Extra Child Supplement', default=15.0)

    # Inclusions & Amenities
    amenity_ids = fields.Many2many('hotel.room.amenity', string='Amenities')
    description = fields.Html(string='Marketing Description')
    image_1920 = fields.Image(string='Room Type Image')

    # Inventory Metrics
    room_ids = fields.One2many('hotel.room', 'room_type_id', string='Physical Rooms')
    total_rooms = fields.Integer(string='Total Rooms', compute='_compute_room_metrics')
    available_rooms = fields.Integer(string='Available', compute='_compute_room_metrics')
    occupied_rooms = fields.Integer(string='Occupied', compute='_compute_room_metrics')
    dirty_rooms = fields.Integer(string='Dirty', compute='_compute_room_metrics')
    maintenance_rooms = fields.Integer(string='Maintenance', compute='_compute_room_metrics')

    @api.depends('max_adults', 'max_children')
    def _compute_max_occupancy(self):
        for rec in self:
            rec.max_occupancy = rec.max_adults + rec.max_children

    @api.depends('room_ids.status')
    def _compute_room_metrics(self):
        for rec in self:
            rooms = rec.room_ids
            rec.total_rooms = len(rooms)
            rec.available_rooms = len(rooms.filtered(lambda r: r.status in ('available', 'inspected', 'clean')))
            rec.occupied_rooms = len(rooms.filtered(lambda r: r.status == 'occupied'))
            rec.dirty_rooms = len(rooms.filtered(lambda r: r.status == 'dirty'))
            rec.maintenance_rooms = len(rooms.filtered(lambda r: r.status in ('maintenance', 'out_of_service')))


class HotelRatePlan(models.Model):
    _name = 'hotel.rate.plan'
    _description = 'Hotel Rate Plan'
    _order = 'sequence, name'

    name = fields.Char(string='Rate Plan Name', required=True)
    code = fields.Char(string='Code', size=10, required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)

    plan_type = fields.Selection([
        ('bar', 'Best Available Rate (BAR)'),
        ('non_refundable', 'Non-Refundable (Discounted)'),
        ('corporate', 'Corporate Negotiated'),
        ('package', 'Package / Promotional'),
        ('long_stay', 'Long Stay Special (7+ Nights)'),
    ], string='Plan Type', default='bar', required=True)

    meal_plan_id = fields.Many2one('hotel.meal.plan', string='Included Meal Plan')

    # Price Calculation
    pricing_type = fields.Selection([
        ('fixed', 'Fixed Nightly Override'),
        ('percent_discount', 'Percentage Discount off Base Rate'),
        ('percent_surcharge', 'Percentage Surcharge over Base Rate'),
    ], string='Rate Calculation Mode', default='bar', required=True)
    discount_percent = fields.Float(string='Discount %', default=0.0)
    surcharge_percent = fields.Float(string='Surcharge %', default=0.0)
    fixed_override_price = fields.Float(string='Fixed Price Override')

    # Restrictions
    min_stay_nights = fields.Integer(string='Min Length of Stay', default=1)
    max_stay_nights = fields.Integer(string='Max Length of Stay', default=0, help="0 means no limit")
    closed_to_arrival = fields.Boolean(string='Closed to Arrival (CTA)', default=False)
    closed_to_departure = fields.Boolean(string='Closed to Departure (CTD)', default=False)
    cancellation_policy = fields.Text(string='Cancellation & Deposit Policy')


class HotelRoom(models.Model):
    _name = 'hotel.room'
    _description = 'Physical Hotel Room'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Room Number / Name', required=True, tracking=True)
    room_type_id = fields.Many2one('hotel.room.type', string='Room Type', required=True, tracking=True)
    floor_id = fields.Many2one('hotel.floor', string='Floor / Level', required=True)
    building_id = fields.Many2one(related='floor_id.building_id', string='Building / Wing', store=True)
    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)

    status = fields.Selection([
        ('available', 'Available (Vacant & Ready)'),
        ('reserved', 'Reserved (Arrival Today)'),
        ('occupied', 'Occupied'),
        ('dirty', 'Vacant Dirty'),
        ('clean', 'Vacant Clean'),
        ('inspected', 'Vacant Inspected'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service (OOS)'),
    ], string='Room Status', default='clean', tracking=True, required=True)

    status_color = fields.Char(string='Status Badge Color', compute='_compute_status_color')

    current_reservation_id = fields.Many2one('hotel.reservation', string='Current In-House Reservation', compute='_compute_current_stay', store=True)
    current_guest_id = fields.Many2one(related='current_reservation_id.partner_id', string='Current Guest', store=True)
    
    keycard_code = fields.Char(string='Keycard Identifier / Lock ID')
    telephone_ext = fields.Char(string='Telephone Ext.')
    notes = fields.Text(string='Room Notes / Specifics')

    @api.depends('status')
    def _compute_status_color(self):
        color_map = {
            'available': '#28a745',     # Green
            'inspected': '#20c997',     # Teal
            'clean': '#17a2b8',         # Cyan
            'reserved': '#fd7e14',      # Orange
            'occupied': '#007bff',      # Blue
            'dirty': '#dc3545',         # Red
            'maintenance': '#ffc107',   # Yellow
            'out_of_service': '#6c757d' # Grey
        }
        for rec in self:
            rec.status_color = color_map.get(rec.status, '#6c757d')

    @api.depends('company_id')
    def _compute_current_stay(self):
        for rec in self:
            # Active checked-in reservation for this room
            res = self.env['hotel.reservation'].search([
                ('room_id', '=', rec.id),
                ('state', '=', 'checkin'),
            ], limit=1)
            rec.current_reservation_id = res.id if res else False

    def action_set_clean(self):
        self.write({'status': 'clean'})

    def action_set_dirty(self):
        self.write({'status': 'dirty'})

    def action_set_inspected(self):
        self.write({'status': 'inspected'})

    def action_set_available(self):
        self.write({'status': 'available'})

    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})
