def post_init_hook(env):
    """Marca como propietarios CRM permitidos a los usuarios solicitados si existen."""
    names = ['Maribel García', 'Maribel Garcia', 'Ana Beatriz Guinea', 'Carolina Ortiz']
    users = env['res.users'].sudo().search(['|', ('name', 'in', names), ('login', 'in', names)])
    if users:
        users.write({'x_localiza_crm_owner_allowed': True})
