# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

from numpy import maximum as max_
from openfisca_core import columns, formulas, reforms
from collections import OrderedDict

from ...model.prelevements_obligatoires.impot_revenu import ir

def modify_legislation_json(reference_legislation_json_copy):
    reference_legislation_json_copy['children']['ir']['children']['bareme']['brackets'][1]['threshold'][0] =\
        [OrderedDict([('start_line_number', 2119), ('start', u'2014-01-01'), ('stop', u'2014-12-31'), ('value', 9690.0)])]
    reference_legislation_json_copy['children']['ir']['children']['bareme']['brackets'][1]['rate'] =\
        [OrderedDict([('start_line_number', 2125), ('start', u'2014-01-01'), ('stop', u'2014-12-31'), ('value', 0.14)])]
    return reference_legislation_json_copy

def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'trannoy_detricote_la_decote',
        name = u'Trannoy détricote la décote',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Suppression décote"
        reference = ir.rbg
        def function(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            return period, 0
            
    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform


