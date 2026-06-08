# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ni_payroll_enabled = fields.Boolean(string='Aplicar nómina fiscal Nicaragua', default=True)
    ni_identification = fields.Char(string='Cédula Nicaragua')
    ni_inss_number = fields.Char(string='Número INSS')
    ni_basic_salary = fields.Monetary(string='Salario básico mensual', currency_field='currency_id', default=0.0)
    ni_payment_frequency = fields.Selection([
        ('monthly', 'Mensual'),
        ('biweekly', 'Quincenal'),
        ('weekly', 'Semanal'),
    ], string='Frecuencia de pago', default='monthly')
    ni_bank_account = fields.Char(string='Cuenta bancaria para nómina')
    ni_employee_type = fields.Selection([
        ('permanent', 'Permanente'),
        ('temporary', 'Temporal'),
        ('services', 'Servicios profesionales'),
    ], string='Tipo laboral', default='permanent')
    ni_hire_date = fields.Date(string='Fecha de ingreso nómina')
    ni_salary_notes = fields.Text(string='Notas de nómina')
