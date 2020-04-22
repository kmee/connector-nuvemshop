# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp import models, fields, api
import unicodedata
import re

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None


def get_slug(name):
    if slugify_lib:
        try:
            return slugify_lib.slugify(name)
        except TypeError:
            pass
    uni = unicodedata.normalize('NFKD', name).encode(
        'ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[\W_]', ' ', uni).strip().lower()
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


class HandleAbstract(models.AbstractModel):

    _name = 'nuvemshop.handle.abstract'
    _description = 'Nuvemshop Slug handle'
    handle = fields.Char('Handle', translate=True)

    def _handle_name(self, name):
        result = ''
        if name:
            result = get_slug(name)
        return result
