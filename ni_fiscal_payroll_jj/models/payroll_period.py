# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class NiPayrollPeriod(models.Model):
    _name = 'ni.payroll.period'
    _description = 'Período de Nómina Nicaragua'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Nombre', required=True, tracking=True)
    date_start = fields.Date(string='Fecha inicial', required=True, tracking=True)
    date_end = fields.Date(string='Fecha final', required=True, tracking=True)
    payment_date = fields.Date(string='Fecha de pago', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('computed', 'Calculado'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    payslip_ids = fields.One2many('ni.payroll.payslip', 'period_id', string='Boletas')
    payslip_count = fields.Integer(compute='_compute_totals', string='Cantidad de boletas')
    total_gross = fields.Monetary(compute='_compute_totals', currency_field='currency_id', string='Total devengado')
    total_deductions = fields.Monetary(compute='_compute_totals', currency_field='currency_id', string='Total deducciones')
    total_net = fields.Monetary(compute='_compute_totals', currency_field='currency_id', string='Total neto')

    @api.depends('payslip_ids.total_gross', 'payslip_ids.total_deductions', 'payslip_ids.total_net')
    def _compute_totals(self):
        for rec in self:
            rec.payslip_count = len(rec.payslip_ids)
            rec.total_gross = sum(rec.payslip_ids.mapped('total_gross'))
            rec.total_deductions = sum(rec.payslip_ids.mapped('total_deductions'))
            rec.total_net = sum(rec.payslip_ids.mapped('total_net'))

    def action_generate_payslips(self):
        for period in self:
            employees = self.env['hr.employee'].search([
                ('company_id', 'in', [False, period.company_id.id]),
                ('ni_payroll_enabled', '=', True),
                ('ni_basic_salary', '>', 0),
            ])
            if not employees:
                raise UserError(_('No hay empleados activos para nómina con salario básico configurado.'))
            for employee in employees:
                existing = self.env['ni.payroll.payslip'].search([
                    ('period_id', '=', period.id),
                    ('employee_id', '=', employee.id),
                ], limit=1)
                if not existing:
                    self.env['ni.payroll.payslip'].create({
                        'period_id': period.id,
                        'employee_id': employee.id,
                        'company_id': period.company_id.id,
                    })
            period.state = 'computed'
        return True

    def action_compute_all(self):
        for period in self:
            if not period.payslip_ids:
                period.action_generate_payslips()
            period.payslip_ids.action_compute()
            period.state = 'computed'
        return True

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
