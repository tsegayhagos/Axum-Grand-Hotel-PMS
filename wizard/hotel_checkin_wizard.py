# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HotelCheckinWizard(models.TransientModel):
    _name = 'hotel.checkin.wizard'
    _description = 'Front Desk Quick Check-In Wizard'

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation', required=True)
    partner_id = fields.Many2one(related='reservation_id.partner_id', string='Guest Name', readonly=True)
    room_id = fields.Many2one('hotel.room', string='Assign Physical Room', required=True)
    keycard_code = fields.Char(string='Keycard / Electronic Lock Code')
    
    id_verified = fields.Boolean(string='Guest Identity / Passport Verified', default=True)
    deposit_amount = fields.Float(string='Pre-Authorized Security Deposit', default=0.0)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card Pre-Auth'),
        ('direct_bill', 'Corporate City Ledger'),
    ], string='Deposit Method', default='credit_card')
    
    checkin_notes = fields.Text(string='Front Desk Check-In Remarks')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id:
            reservation = self.env['hotel.reservation'].browse(active_id)
            res['reservation_id'] = reservation.id
            if reservation.room_id:
                res['room_id'] = reservation.room_id.id
            else:
                available = self.env['hotel.room'].search([
                    ('room_type_id', '=', reservation.room_type_id.id),
                    ('status', 'in', ('available', 'clean', 'inspected')),
                ], limit=1)
                if available:
                    res['room_id'] = available.id
        return res

    def action_confirm_checkin(self):
        self.ensure_one()
        res = self.reservation_id
        if not self.id_verified:
            raise UserError(_("You must verify guest identity before completing check-in."))
        if self.room_id.status not in ('available', 'clean', 'inspected', 'reserved'):
            raise UserError(_("Selected room %s is currently in '%s' status and cannot be checked into.") % (self.room_id.name, self.room_id.status))

        res.room_id = self.room_id.id
        if self.keycard_code:
            self.room_id.keycard_code = self.keycard_code

        res.action_checkin()

        # If deposit received, record payment on folio
        if self.deposit_amount > 0 and res.folio_id:
            self.env['hotel.folio.payment'].create({
                'folio_id': res.folio_id.id,
                'amount': self.deposit_amount,
                'payment_method': self.payment_method,
                'reference': _("Pre-Auth Deposit upon Check-in"),
                'company_id': res.company_id.id,
                'payment_date': fields.Date.today(),
            })

        return {'type': 'ir.actions.act_window_close'}
