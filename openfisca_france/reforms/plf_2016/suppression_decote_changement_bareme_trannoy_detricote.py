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
from openfisca_core import columns, formulas, reforms, periods
from collections import OrderedDict

from ...model.prelevements_obligatoires.impot_revenu import ir


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'trannoy_detricote_la_decote',
        name = u'Trannoy détricote la décote',
        reference = tax_benefit_system,
        )

    reform_year = 2016
    reform_period = periods.period('year', reform_year)
    # FIXME update_legislation is deprecated.
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = tax_benefit_system.legislation_json,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'rate'),
        period = reform_period,
        value = 0.16,
        )
    # FIXME update_legislation is deprecated.
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'threshold'),
        period = reform_period,
        value = 17800,
        )
    reference_legislation_json_copy['children']['plf2015'] = reform_legislation_subtree
    return reference_legislation_json_copy
    
    
    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Suppression décote"
        reference = ir.rbg
        def function(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            return period, 0
            
    reform = Reform()
    reform.modify_legislation_json(modifier_function = reference_legislation_json_copy)
    return reform