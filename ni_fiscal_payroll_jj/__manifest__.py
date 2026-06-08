# -*- coding: utf-8 -*-
{
    'name': 'Nómina Fiscal Nicaragua',
    'version': '19.0.1.0.0',
    'summary': 'Nómina fiscal modular para Nicaragua basada en Empleados',
    'description': '''
Nómina Fiscal Nicaragua para Odoo 19.
Creado por Janmer Jácamo.

Funcionalidades:
- Campos de nómina en empleados.
- Períodos de nómina.
- Cálculo de planillas sin depender de contratos.
- INSS laboral, INSS patronal, INATEC e IR salarial.
- Liquidaciones laborales.
- Boletas e informes básicos.
''',
    'author': 'Janmer Jácamo',
    'category': 'Human Resources/Payroll',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/payroll_rule_data.xml',
        'views/hr_employee_views.xml',
        'views/payroll_period_views.xml',
        'views/payroll_payslip_views.xml',
        'views/payroll_liquidation_views.xml',
        'views/payroll_menu.xml',
    ],
    'installable': True,
    'application': True,
}
