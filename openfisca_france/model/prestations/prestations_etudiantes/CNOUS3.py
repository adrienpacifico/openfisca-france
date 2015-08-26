# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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

from ...base import *  # noqa

"""
!!!Work in progress, not reliable!!!

This file takes into account some Cnous welfare benefits.
Cnous is an organism that is in change of student's grants (Centre national des œuvres universitaires et scolaires)

Official simulator for student's grants can be found at: http://www.cnous.fr/bourses/simulateur/

legislation : http://www.enseignementsup-recherche.gouv.fr/pid20536/bulletin-officiel.html?cid_bo=81151&cbo=1
"""

reference_input_variable(
    column = IntCol(),
    entity_class = Individus,
    label = u"distance foyer étude (en km)",
    name = 'distance_foyer_etude',
    )


@reference_formula
class nombre_enfants_individu(EntityToPersonColumn):
    entity_class = Individus
    label = u"Nombre d'enfants dans la famille de l'individu"
    variable = Familles.column_by_name['af_nbenf']  # TODO: Check for the right entity variable


@reference_formula
class points_de_charge(SimpleFormulaColumn):
     column = FloatCol
     entity_class = Individus
     label = u"Points de charges pour les bourses étudiantes au sens de la CNAF"

     def function(self, simulation, period):
         period = period.start.offset('first-of', 'year').period('year')
         distance_foyer_etude = simulation.calculate('distance_foyer_etude', period)
         nombre_enfants_individu = simulation.calculate('nombre_enfants_individu', period)
        # distance lieu d'étude
         points_de_charge = (distance_foyer_etude >= 30) * 1 +  (distance_foyer_etude > 249)
        # children in the household  : chaque enfant à charge à l'exception du cadidat boursier compte pour 2 points

         points_de_charge += (nombre_enfants_individu - 1) * 2
         # S'ils sont étudiants ils comptent pour 2 pts suplémentaire

         points_de_charge = points_de_charge + ((2 - 1) * 2)
         print(points_de_charge)
         return points_de_charge, period



def echelon_bourse_etudiant(pts_de_charge, sali):


# Approximation test (but good approximation at 50 euros yearly income precision )
#   http://www.legifrance.gouv.fr/affichTexte.do;jsessionid=?cidTexte=JORFTEXT000029374760&dateTexte=&oldAction=dernierJO&categorieLien=id

#TODO : Passer echelon_bourse_etudiant en string pour échelon 0bis ?


    echelon_bourse_etudiant = 0
    echelon_bourse_etudiant = 7 * ( sali < (pts_de_charge + 1) * 250) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 6 * ((pts_de_charge + 1) * 250 < sali < (pts_de_charge) * 840 + 7540) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 5 * ((pts_de_charge) * 840 + 7540 < sali < (pts_de_charge) * 1330 + 11950) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 4 * ((pts_de_charge) * 1330 + 11950 < sali < (pts_de_charge) * 1560 + 13990) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 3 * ((pts_de_charge) * 1560 + 13990 < sali < (pts_de_charge) * 1790 + 16070) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 2 * ((pts_de_charge) * 1790 + 16070< sali < (pts_de_charge) * 2020 + 18190) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 1 * ((pts_de_charge) * 2020 + 18190 < sali < (pts_de_charge) * 2490 + 22500) + echelon_bourse_etudiant
    echelon_bourse_etudiant = 0.5 * ((pts_de_charge) * 2490 + 22500 < sali < (pts_de_charge) * 3400 + 31000) + echelon_bourse_etudiant  #echelon 0 bis
    echelon_bourse_etudiant = 0 * ( (pts_de_charge) * 3400 + 31000 < sali < (pts_de_charge)* 3680 + 33100) + echelon_bourse_etudiant
#    echelon_bourse_etudiant = False * ( sali > pts_de_charge * 3400 + 31000 ) #modifier pour avoir nan si en dessous du seuil des boursiers

#TODO: bien corriger les inférieurs ou égal

    print(echelon_bourse_etudiant)
    return echelon_bourse_etudiant


def montant_bourse_etudiant(echelon_bourse_etudiant):
    montant_bourse_etudiant = 5539 * (echelon_bourse_etudiant == 7)
    montant_bourse_etudiant = 4768 * (echelon_bourse_etudiant == 6) + montant_bourse_etudiant
    montant_bourse_etudiant = 4496 * (echelon_bourse_etudiant == 5) + montant_bourse_etudiant
    montant_bourse_etudiant = 3916  * (echelon_bourse_etudiant == 4) + montant_bourse_etudiant
    montant_bourse_etudiant = 3212  * (echelon_bourse_etudiant == 3) + montant_bourse_etudiant
    montant_bourse_etudiant = 2507  * (echelon_bourse_etudiant == 2) + montant_bourse_etudiant
    montant_bourse_etudiant = 1665 * (echelon_bourse_etudiant == 1) + montant_bourse_etudiant
    montant_bourse_etudiant = 1007 * (echelon_bourse_etudiant == 0.5) + montant_bourse_etudiant
    montant_bourse_etudiant = 0  * (echelon_bourse_etudiant == 0) + montant_bourse_etudiant

    print(montant_bourse_etudiant)
    return montant_bourse_etudiant

def eligibilite_bourse_etu(nb_year_of_bourse_etu = 0):


##TODO : condition de maintient (semestre réussite, au dela du master, etc )
    if nb_year_of_bourse_etu > 7:
            montant_bourse_etudiant = 0

def boursier():
    return (echelon_bourse_etudiant <> nan)


if __name__ == "__main__":
    sali = 37400
    distance_foy_etude = 456

#    nb_enf_charge = nbJ + nbF
    nb_enf_charge = 5 + 1

    nb_enf_charge_enseignementsup = 2 + 1  #f7ef ?
    pts_de_charge = pts_de_charge(distance_foy_etude, nb_enf_charge)
    echelon_bourse_etudiant = echelon_bourse_etudiant(pts_de_charge, sali)
    montant_bourse_etudiant(echelon_bourse_etudiant)