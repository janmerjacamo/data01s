# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class NiPayrollRule(models.Model):
    _name = 'ni.payroll.rule'
    _description = 'Regla de Nómina Nicaragua'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    rule_type = fields.Selection([
        ('earning', 'Ingreso'),
        ('deduction', 'Deducción'),
        ('employer', 'Aporte patronal'),
    ], string='Tipo', required=True, default='earning')
    active = fields.Boolean(default=True)
    note = fields.Text(string='Nota')


class NiPayrollPayslip(models.Model):
    _name = 'ni.payroll.payslip'
    _description = 'Boleta de Nómina Nicaragua'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_id desc, employee_id'

    name = fields.Char(string='Referencia', compute='_compute_name', store=True)
    period_id = fields.Many2one('ni.payroll.period', string='Período', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Departamento', store=True)
    job_id = fields.Many2one(related='employee_id.job_id', string='Puesto', store=True)
    basic_salary = fields.Monetary(string='Salario básico mensual', currency_field='currency_id')
    worked_days = fields.Float(string='Días trabajados', default=30.0)
    overtime_amount = fields.Monetary(string='Horas extras', currency_field='currency_id', default=0.0)
    bonus_amount = fields.Monetary(string='Bonos / comisiones', currency_field='currency_id', default=0.0)
    absence_amount = fields.Monetary(string='Ausencias / permisos no pagados', currency_field='currency_id', default=0.0)
    other_deductions = fields.Monetary(string='Otras deducciones', currency_field='currency_id', default=0.0)
    total_gross = fields.Monetary(string='Total devengado', currency_field='currency_id', compute='_compute_totals', store=True)
    inss_employee = fields.Monetary(string='INSS laboral 7%', currency_field='currency_id', compute='_compute_totals', store=True)
    ir_salary = fields.Monetary(string='IR salarial estimado', currency_field='currency_id', compute='_compute_totals', store=True)
    total_deductions = fields.Monetary(string='Total deducciones', currency_field='currency_id', compute='_compute_totals', store=True)
    total_net = fields.Monetary(string='Neto a pagar', currency_field='currency_id', compute='_compute_totals', store=True)
    inss_employer = fields.Monetary(string='INSS patronal estimado', currency_field='currency_id', compute='_compute_totals', store=True)
    inatec_employer = fields.Monetary(string='INATEC 2%', currency_field='currency_id', compute='_compute_totals', store=True)
    line_ids = fields.One2many('ni.payroll.payslip.line', 'payslip_id', string='Líneas')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('computed', 'Calculada'),
        ('approved', 'Aprobada'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)
    notes = fields.Text(string='Notas')

    @api.depends('period_id.name', 'employee_id.name')
    def _compute_name(self):
        for rec in self:
            rec.name = '%s - %s' % (rec.period_id.name or 'Nómina', rec.employee_id.name or '')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for rec in self:
            rec.basic_salary = rec.employee_id.ni_basic_salary or 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('employee_id') and not vals.get('basic_salary'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                vals['basic_salary'] = employee.ni_basic_salary or 0.0
        return super().create(vals_list)

    @api.depends('basic_salary', 'worked_days', 'overtime_amount', 'bonus_amount', 'absence_amount', 'other_deductions')
    def _compute_totals(self):
        for rec in self:
            monthly_salary = rec.basic_salary or 0.0
            worked_ratio = (rec.worked_days or 0.0) / 30.0
            ordinary = monthly_salary * worked_ratio
            gross = max(ordinary + rec.overtime_amount + rec.bonus_amount - rec.absence_amount, 0.0)
            inss_emp = gross * 0.07
            taxable_month = max(gross - inss_emp, 0.0)
            ir = rec._compute_monthly_ir(taxable_month)
            deductions = inss_emp + ir + rec.other_deductions
            rec.total_gross = gross
            rec.inss_employee = inss_emp
            rec.ir_salary = ir
            rec.total_deductions = deductions
            rec.total_net = gross - deductions
            # Parámetro patronal editable a futuro; por defecto 21.5%
            rec.inss_employer = gross * 0.215
            rec.inatec_employer = gross * 0.02

    def _compute_monthly_ir(self, taxable_month):
        annual = taxable_month * 12.0
        if annual <= 100000:
            annual_tax = 0.0
        elif annual <= 200000:
            annual_tax = (annual - 100000) * 0.15
        elif annual <= 350000:
            annual_tax = 15000 + (annual - 200000) * 0.20
        elif annual <= 500000:
            annual_tax = 45000 + (annual - 350000) * 0.25
        else:
            annual_tax = 82500 + (annual - 500000) * 0.30
        return annual_tax / 12.0

    def action_compute(self):
        for rec in self:
            rec._rebuild_lines()
            rec.state = 'computed'
        return True

    def _rebuild_lines(self):
        self.ensure_one()
        self.line_ids.unlink()
        lines = [
            ('BASIC', 'Salario ordinario', 'earning', self.total_gross - self.overtime_amount - self.bonus_amount + self.absence_amount),
            ('OT', 'Horas extras', 'earning', self.overtime_amount),
            ('BONUS', 'Bonos / comisiones', 'earning', self.bonus_amount),
            ('ABS', 'Ausencias / permisos no pagados', 'deduction', self.absence_amount),
            ('INSS_EMP', 'INSS laboral', 'deduction', self.inss_employee),
            ('IR', 'IR salarial', 'deduction', self.ir_salary),
            ('OTHER_DED', 'Otras deducciones', 'deduction', self.other_deductions),
            ('INSS_PAT', 'INSS patronal', 'employer', self.inss_employer),
            ('INATEC', 'INATEC patronal', 'employer', self.inatec_employer),
            ('NET', 'Neto a pagar', 'earning', self.total_net),
        ]
        seq = 10
        for code, name, line_type, amount in lines:
            if abs(amount) > 0.00001 or code in ('INSS_EMP', 'IR', 'NET'):
                self.env['ni.payroll.payslip.line'].create({
                    'payslip_id': self.id,
                    'sequence': seq,
                    'code': code,
                    'name': name,
                    'line_type': line_type,
                    'amount': amount,
                })
                seq += 10

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class NiPayrollPayslipLine(models.Model):
    _name = 'ni.payroll.payslip.line'
    _description = 'Línea de Boleta de Nómina Nicaragua'
    _order = 'sequence, id'

    payslip_id = fields.Many2one('ni.payroll.payslip', string='Boleta', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Concepto', required=True)
    line_type = fields.Selection([
        ('earning', 'Ingreso'),
        ('deduction', 'Deducción'),
        ('employer', 'Aporte patronal'),
    ], string='Tipo', required=True)
    amount = fields.Monetary(string='Monto', currency_field='currency_id')
    currency_id = fields.Many2one(related='payslip_id.currency_id', store=True)
