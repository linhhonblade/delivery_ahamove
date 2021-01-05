# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    token_ahamove = fields.Char("Ahamove Token", config_parameter='ahamove_api_token',
                         default='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhaGEiLCJ0eXAiOiJ1c2VyIiwiY2lkIjoiODQ4Mzg0Mzk0ODMiLCJzdGF0dXMiOiJPTkxJTkUiLCJlb2MiOm51bGwsIm5vYyI6IlwiUGhhbSBUaGkgTmdvYyBNYWlcIiIsImN0eSI6IkhBTiIsImFjY291bnRfc3RhdHVzIjoiQUNUSVZBVEVEIiwiZXhwIjoxNjA5MjExNDUzLCJwYXJ0bmVyIjoiYXJyb3doaXRlY2gifQ.wDMPf78V7xH3x74T1nRmnWME5Cquf5KsMXJLbLIpWKo')
    refresh_token = fields.Char("Ahamove Refresh Token",
                                config_parameter='ahamove_refresh_token', default='df27098effd1338af01581511f92be4b')