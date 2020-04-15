# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.addons.connector.backend as backend

nuvemshop = backend.Backend('nuvemshop')
nuvemshop1 = backend.Backend(parent=nuvemshop, version='v1')
