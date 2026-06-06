import base64
import csv
import io
from odoo import fields, models, _
from odoo.exceptions import UserError


class LocalizaFormsImport(models.Model):
    _name = 'localiza.forms.import'
    _description = 'Importacion de formularios operativos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Nombre', required=True, default='Importacion formularios')
    import_type = fields.Selection([
        ('entrega_bodega', 'Entrega desde Bodega'),
        ('instalacion_puesto', 'Instalacion en Puesto'),
        ('inventario_puesto', 'Inventario de Puesto'),
        ('prestamo_herramientas', 'Prestamo de Herramientas'),
    ], string='Tipo', required=True, default='entrega_bodega')
    file = fields.Binary(string='Archivo CSV/XLSX', required=True)
    filename = fields.Char(string='Nombre archivo')
    state = fields.Selection([('draft','Borrador'),('done','Importado'),('error','Error')], default='draft', tracking=True)
    log = fields.Text(string='Resultado')
    created_count = fields.Integer(string='Registros creados', readonly=True)

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_('Cargue un archivo.'))
        rows = self._read_rows()
        if not rows:
            raise UserError(_('No se encontraron filas para importar.'))
        created = 0
        errors = []
        for idx, row in enumerate(rows, start=2):
            try:
                vals = self._map_row(row)
                form = self.env['localiza.forms.operation'].create(vals)
                line_name = row.get('articulo') or row.get('herramienta') or row.get('insumo') or row.get('producto')
                if line_name:
                    self.env['localiza.forms.operation.line'].create({
                        'form_id': form.id,
                        'name': line_name,
                        'code': row.get('codigo') or row.get('serie') or '',
                        'serial': row.get('serie') or row.get('imei') or '',
                        'qty': float(row.get('cantidad') or 1),
                        'movement': row.get('movimiento') or vals.get('movement_type') or 'salida',
                        'notes': row.get('observaciones') or row.get('observacion') or '',
                    })
                created += 1
            except Exception as exc:
                errors.append('Fila %s: %s' % (idx, exc))
        self.created_count = created
        self.state = 'error' if errors else 'done'
        self.log = 'Creados: %s\n%s' % (created, '\n'.join(errors))
        return True

    def _read_rows(self):
        data = base64.b64decode(self.file)
        fname = (self.filename or '').lower()
        if fname.endswith('.csv'):
            text = data.decode('utf-8-sig', errors='ignore')
            return [self._normalize_dict(r) for r in csv.DictReader(io.StringIO(text))]
        if fname.endswith('.xlsx'):
            try:
                import openpyxl
            except Exception:
                raise UserError(_('El servidor no tiene la libreria openpyxl. Use CSV o instale openpyxl.'))
            wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [self._normalize_key(h) for h in rows[0]]
            result = []
            for values in rows[1:]:
                result.append({headers[i]: values[i] for i in range(min(len(headers), len(values))) if headers[i]})
            return [self._normalize_dict(r) for r in result]
        raise UserError(_('Formato no soportado. Use CSV o XLSX.'))

    def _normalize_key(self, key):
        key = str(key or '').strip().lower()
        repl = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ñ':'n'}
        for a, b in repl.items():
            key = key.replace(a, b)
        key = key.replace(' ', '_').replace('/', '_')
        return key

    def _normalize_dict(self, row):
        return {self._normalize_key(k): ('' if v is None else str(v).strip()) for k, v in row.items()}

    def _map_row(self, row):
        puesto = row.get('puesto') or row.get('puesto_principal') or row.get('puesto_destino')
        puesto_id = False
        if puesto:
            puesto_rec = self.env['localiza.puesto'].search([('name', 'ilike', puesto)], limit=1)
            if not puesto_rec:
                puesto_rec = self.env['localiza.puesto'].create({'name': puesto, 'tipo': 'otro'})
            puesto_id = puesto_rec.id
        return {
            'form_type': self.import_type,
            'folio': row.get('folio') or row.get('numero') or row.get('id_externo'),
            'puesto_id': puesto_id,
            'receiver_name': row.get('persona_que_recibe') or row.get('receptor') or row.get('solicita'),
            'delivered_by': row.get('encargado_de_entrega') or row.get('persona_encargada_de_entrega'),
            'requested_by': row.get('persona_que_solicita') or row.get('solicitante'),
            'supervisor_name': row.get('persona_que_supervisa') or row.get('supervisor'),
            'guard_name': row.get('guardia_de_turno') or row.get('guardia'),
            'installer_name': row.get('persona_que_instala') or row.get('instalador'),
            'main_serial': row.get('serie') or row.get('serie_principal'),
            'controlled_qty': int(float(row.get('cantidad_controlada') or row.get('cantidad') or 0)),
            'motive': row.get('motivo') or row.get('motivo_de_solicitud'),
            'observations': row.get('observaciones') or row.get('observacion'),
            'summary': row.get('resumen'),
            'gps_coordinates': row.get('ubicacion') or row.get('coordenadas'),
            'movement_type': row.get('movimiento') or row.get('tipo_movimiento') or 'salida',
        }
