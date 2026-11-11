# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HotelNightAuditWizard(models.TransientModel):
    _name = 'hotel.night.audit.wizard'
    _description = 'Run Night Audit Wizard'

    company_id = fields.Many2one('res.company', string='Property', default=lambda self: self.env.company, required=True)
    audit_date = fields.Date(string='Business Date to Audit', default=fields.Date.today, required=True)
    auto_post_room_charges = fields.Boolean(string='Post Today Room Charges & City Taxes', default=True)
    advance_date = fields.Boolean(string='Advance Business Date to Tomorrow', default=True)

    def action_start_audit(self):
        self.ensure_one()
        audit = self.env['hotel.night.audit'].create({
            'company_id': self.company_id.id,
            'audit_date': self.audit_date,
        })
        audit.action_verify_discrepancies()
        return {
            'name': _('Night Audit Operational Review'),
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.night.audit',
            'view_mode': 'form',
            'res_id': audit.id,
            'target': 'current',
        }
