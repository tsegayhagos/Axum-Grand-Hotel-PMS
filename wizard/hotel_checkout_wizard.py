# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HotelCheckoutWizard(models.TransientModel):
    _name = 'hotel.checkout.wizard'
    _description = 'Front Desk Quick Check-Out & Settlement Wizard'

    reservation_id = fields.Many2one('hotel.reservation', string='Reservation', required=True)
    partner_id = fields.Many2one(related='reservation_id.partner_id', string='Guest Name', readonly=True)
    room_id = fields.Many2one(related='reservation_id.room_id', string='Room Number', readonly=True)
    folio_id = fields.Many2one(related='reservation_id.folio_id', string='Folio', readonly=True)

    total_charges = fields.Monetary(related='folio_id.total_charges', string='Total Charges', readonly=True)
    total_payments = fields.Monetary(related='folio_id.total_payments', string='Total Payments Received', readonly=True)
    balance_due = fields.Monetary(related='folio_id.balance_due', string='Outstanding Balance', readonly=True)
    currency_id = fields.Many2one(related='reservation_id.currency_id', string='Currency', readonly=True)

    settlement_payment_amount = fields.Monetary(string='Settlement Amount to Pay', currency_field='currency_id')
    payment_method = fields.Selection([
        ('cash', 'Cash (Front Desk Till)'),
        ('credit_card', 'Credit / Debit Card'),
        ('bank_transfer', 'Bank Transfer / Wire'),
        ('direct_bill', 'Corporate Direct Billing'),
        ('mobile_money', 'Mobile Payment (CBE Birr / Telebirr)'),
    ], string='Settlement Method', default='credit_card')
    payment_reference = fields.Char(string='Payment Reference / Transaction ID')

    keycard_returned = fields.Boolean(string='Room Keycard(s) Returned', default=True)
    minibar_settled = fields.Boolean(string='Minibar Checked & Finalized', default=True)
    checkout_feedback = fields.Text(string='Guest Departure Feedback / Rating')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id:
            reservation = self.env['hotel.reservation'].browse(active_id)
            res['reservation_id'] = reservation.id
            if reservation.folio_id:
                bal = reservation.folio_id.balance_due
                res['settlement_payment_amount'] = bal if bal > 0 else 0.0
        return res

    def action_confirm_checkout(self):
        self.ensure_one()
        res = self.reservation_id
        folio = res.folio_id

        # Settle any balance
        if self.settlement_payment_amount > 0 and folio:
            self.env['hotel.folio.payment'].create({
                'folio_id': folio.id,
                'amount': self.settlement_payment_amount,
                'payment_method': self.payment_method,
                'reference': self.payment_reference or _("Final Checkout Settlement"),
                'company_id': res.company_id.id,
                'payment_date': fields.Date.today(),
            })

        # Recalculate balance
        folio._compute_totals()
        if folio.balance_due > 0.01:
            raise UserError(_("Cannot check out: An unsettled balance of %s remains.") % folio.balance_due)

        res.action_checkout()
        return {'type': 'ir.actions.act_window_close'}
