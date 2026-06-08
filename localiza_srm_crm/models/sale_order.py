from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    localiza_modalidad = fields.Selection([
        ('renta', 'Renta'),
        ('venta', 'Venta'),
    ], string='Modalidad')
    localiza_condicion_pago = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ], string='Condición comercial')
