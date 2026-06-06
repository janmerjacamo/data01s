from odoo import fields, models

class LocalizaBodegaDashboard(models.Model):
    _name = 'localiza.bodega.dashboard'
    _description = 'Panel Principal Bodega Operativa'

    name = fields.Char(default='Panel Principal')

    def _action(self, model, name, domain=None, context=None):
        return {'type': 'ir.actions.act_window', 'name': name, 'res_model': model, 'view_mode': 'list,form', 'domain': domain or [], 'context': context or {}}

    def action_puestos(self):
        return self._action('localiza.puesto', 'Puestos')

    def action_articulos(self):
        return self._action('localiza.bodega.articulo', 'Articulos Operativos')

    def action_formularios(self):
        return self._action('localiza.bodega.formulario', 'Formularios Operativos')

    def action_asignaciones(self):
        return self._action('localiza.bodega.asignacion', 'Asignaciones')

    def action_pendientes(self):
        return self._action('localiza.bodega.formulario', 'Formularios Pendientes', [('state', '=', 'draft')])

    def action_control_especial(self):
        return self._action('localiza.bodega.articulo', 'Control Especial', [('category', '=', 'control_especial')], {'default_category': 'control_especial'})

    def action_gps(self):
        return self._action('localiza.bodega.articulo', 'GPS', [('category', '=', 'gps')], {'default_category': 'gps'})

    def action_herramientas(self):
        return self._action('localiza.bodega.articulo', 'Herramientas', [('category', '=', 'herramienta')], {'default_category': 'herramienta'})
