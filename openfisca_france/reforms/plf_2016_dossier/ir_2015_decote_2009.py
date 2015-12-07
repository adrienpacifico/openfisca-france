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


# TODO switch to to average tax rates

from __future__ import division

from openfisca_core import formulas, periods, reforms

from model.prelevements_obligatoires.impot_revenu import ir
from openfisca_core.columns import FloatCol
from entities import entity_class_by_symbol, Familles, FoyersFiscaux, Individus, Menages


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf2015_2',
        name = u'Projet de Loi de Finances 2015',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class ir_brut(formulas.SimpleFormulaColumn):
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"
    
        def function(self, simulation, period):
            period_init = period
            period = periods.period('year', 2015)
            period = period.start.offset('first-of', 'month').period('year')
            nbptr = simulation.calculate('nbptr', period)
            taux_effectif = simulation.calculate('taux_effectif', period)
            rni = simulation.calculate('rni', period)
            bareme = simulation.legislation_at(period.start).ir.bareme
            print bareme
    
            return period_init, (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni 

    reform = Reform()
    return reform
