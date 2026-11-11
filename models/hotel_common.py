# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HotelBuilding(models.Model):
    _name = 'hotel.building'
    _description = 'Hotel Building / Wing'
    _order = 'sequence, name'

    name = fields.Char(string='Building / Wing Name', required=True)
    code = fields.Char(string='Code', size=10)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Property / Hotel', default=lambda self: self.env.company, required=True)
    floor_ids = fields.One2many('hotel.floor', 'building_id', string='Floors')
    room_count = fields.Integer(string='Total Rooms', compute='_compute_room_count')
    notes = fields.Text(string='Notes')

    @api.depends('floor_ids.room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = sum(len(floor.room_ids) for floor in rec.floor_ids)


class HotelFloor(models.Model):
    _name = 'hotel.floor'
    _description = 'Hotel Floor'
    _order = 'sequence, name'

    name = fields.Char(string='Floor Name / Level', required=True)
    number = fields.Integer(string='Floor Number', default=1)
    sequence = fields.Integer(string='Sequence', default=10)
    building_id = fields.Many2one('hotel.building', string='Building / Wing')
    company_id = fields.Many2one('res.company', string='Property / Hotel', default=lambda self: self.env.company, required=True)
    room_ids = fields.One2many('hotel.room', 'floor_id', string='Rooms')
    room_count = fields.Integer(string='Room Count', compute='_compute_room_count')

    @api.depends('room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)


class HotelMealPlan(models.Model):
    _name = 'hotel.meal.plan'
    _description = 'Hotel Meal Plan'
    _order = 'code, name'

    name = fields.Char(string='Meal Plan Name', required=True)
    code = fields.Char(string='Code', size=10, required=True, help="e.g. EP, CP, MAP, AP, AI")
    price = fields.Float(string='Daily Supplement Price', default=0.0)
    description = fields.Text(string='Included Meals Description')
    active = fields.Boolean(default=True)
