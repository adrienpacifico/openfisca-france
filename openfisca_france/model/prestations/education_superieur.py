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

from numpy import zeros#, logical_not as not_, logical_or as or_, floor, maximum as max_, logical_not as not_, logical_and as and_, logical_or as or_ #TODO :factorise import

from ..base import *  # noqa analysis:ignore


SCOLARITE_INCONNUE = 0
SCOLARITE_COLLEGE = 1
SCOLARITE_LYCEE = 2




@reference_formula
class bourse_cnous_points_de_charge(SimpleFormulaColumn):
    column = FloatCol
    label = u"Nombre de points de charge pour la bourse étudiante"
    entity_class = Individus

    def function(self, simulation, period):
        rfr = simulation.calculate('rfr', period)
        period = period.start.offset('first-of', 'month').period('month')
        age_holder = simulation.compute('age', period)
        age = simulation.calculate('age', period)
        distance_foy_etude_holder = zeros(len(rfr)) * 100 #simulation..compute('distance_foy_etude', period) TODO1
        nb_enf_charge = simulation.calculate('af_nbenf', period) #check if good variable for nbenf.
        etu_holder = simulation.compute('etu', period)


        etudiants = self.split_by_roles(etu_holder, roles = ENFS)
        nb_etu = zeros(len(rfr))
        for enfs in etudiants.itervalues():
            nb_etu += enfs == 1


        #distance lieu d'étude
        points_de_charge = (distance_foy_etude_holder >= 30) * 1
        points_de_charge += (distance_foy_etude_holder > 249) * 1 #TODO : Check if 249 and not 250

        #children in the household  : chaque enfant à charge à l'exception du cadidat boursier compte pour 2 points
        points_de_charge += ((nb_enf_charge - 1) * 2)
        #S'ils sont étudiants ils comptent pour 2 pts suplémentaire
        points_de_charge += ((nb_enf_charge_enseignementsup - 1) * 2)

        return period, points_de_charge



reference_input_variable(
    column = EnumCol(
        enum = Enum(
            [
                u"Inconnue",
                u"Collège",
                u"Lycée"
                ],
            ),
        default = 0
        ),
    entity_class = Individus,
    label = u"Scolarité de l'enfant : collège, lycée...",
    name = "scolarite",
    )


reference_input_variable(
    column = BoolCol,
    entity_class = Individus,
    label = u"Élève ou étudiant boursier",
    name = 'boursier',
    )
