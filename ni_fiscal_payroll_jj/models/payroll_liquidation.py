# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models


class NiPayrollLiquidation(models.Model):
    _name = 'ni.payroll.liquidation'
    _description = 'Liquidación Laboral Nicaragua'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_end desc, id desc'

    name = fields.Char(string='Referencia', compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    date_start = fields.Date(string='Fecha de ingreso', required=True)
    date_end = fields.Date(string='Fecha de salida', required=True, default=fields.Date.context_today)
    monthly_salary = fields.Monetary(string='Salario mensual base', currency_field='currency_id', required=True)
    pending_salary = fields.Monetary(string='Salario pendiente', currency_field='currency_id', default=0.0)
    pending_vacation_days = fields.Float(string='Días de vacaciones pendientes', default=0.0)
    vacation_amount = fields.Monetary(string='Vacaciones', currency_field='currency_id', compute='_compute_amounts', store=True)
    thirteenth_month_amount = fields.Monetary(string='Aguinaldo proporcional', currency_field='currency_id', compute='_compute_amounts', store=True)
    severance_amount = fields.Monetary(string='Indemnización estimada', currency_field='currency_id', compute='_compute_amounts', store=True)
    other_income = fields.Monetary(string='Otros ingresos', currency_field='currency_id', default=0.0)
    other_deductions = fields.Monetary(string='Otras deducciones', currency_field='currency_id', default=0.0)
    total_to_pay = fields.Monetary(string='Total a pagar', currency_field='currency_id', compute='_compute_amounts', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('computed', 'Calculada'),
        ('approved', 'Aprobada'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
    ], default='draft', string='Estado', tracking=True)
    notes = fields.Text(string='Notas legales / administrativas')

    @api.depends('employee_id.name', 'date_end')
    def _compute_name(self):
        for rec in self:
            rec.name = 'Liquidación - %s - %s' % (rec.employee_id.name or '', rec.date_end or '')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.monthly_salary = rec.employee_id.ni_basic_salary or 0.0
            rec.date_start = rec.employee_id.ni_hire_date or (rec.employee_id.create_date.date() if rec.employee_id.create_date else False)

    @api.depends('monthly_salary', 'date_start', 'date_end', 'pending_salary', 'pending_vacation_days', 'other_income', 'other_deductions')
    def _compute_amounts(self):
        for rec in self:
            daily = (rec.monthly_salary or 0.0) / 30.0
            rec.vacation_amount = daily * (rec.pending_vacation_days or 0.0)
            months = rec._months_between(rec.date_start, rec.date_end)
            rec.thirteenth_month_amount = ((rec.monthly_salary or 0.0) / 12.0) * min(months, 12.0)
            years = months / 12.0
            severance_months = min(years, 5.0)
            rec.severance_amount = (rec.monthly_salary or 0.0) * severance_months
            rec.total_to_pay = rec.pending_salary + rec.vacation_amount + rec.thirteenth_month_amount + rec.severance_amount + rec.other_income - rec.other_deductions

    def _months_between(self, start, end):
        if not start or not end:
            return 0.0
        if isinstance(start, str):
            start = fields.Date.from_string(start)
        if isinstance(end, str):
            end = fields.Date.from_string(end)
        days = max((end - start).days, 0)
        return days / 30.0

    def action_compute(self):
        self._compute_amounts()
        self.write({'state': 'computed'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
