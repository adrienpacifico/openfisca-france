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

from numpy import (floor, maximum as max_, logical_not as not_, logical_and as and_, logical_or as or_, nan as nan)

from openfisca_core.accessors import law
from openfisca_core.columns import BoolCol, FloatCol
from openfisca_core.formulas import SimpleFormulaColumn

from openfisca_france.entities import Familles, Individus
from openfisca_france.model.base import QUIFAM, QUIFOY
from openfisca_france.model.pfam import nb_enf

"""
!!!Work in progress, not reliable!!!

This file takes into account some Cnous welfare benefits.
Cnous is an organism that is in change of student's grants (Centre national des œuvres universitaires et scolaires)

Official simulator for student's grants can be found at: http://www.cnous.fr/bourses/simulateur/

legislation : http://www.enseignementsup-recherche.gouv.fr/pid20536/bulletin-officiel.html?cid_bo=81151&cbo=1
"""








#CHEF = QUIFAM['chef']
#PART = QUIFAM['part']
#ENFS = [QUIFAM['enf1'], QUIFAM['enf2'], QUIFAM['enf3'], QUIFAM['enf4'], QUIFAM['enf5'], QUIFAM['enf6'], QUIFAM['enf7'], QUIFAM['enf8'], QUIFAM['enf9'], ]
#VOUS = QUIFOY['vous']
#CONJ = QUIFOY['conj']
#
#
#
#
#
#def _div_ms(self, f3vc_holder, f3ve_holder, f3vg_holder, f3vl_holder, f3vm_holder):
#    f3vc = self.cast_from_entity_to_role(f3vc_holder, role = VOUS)
#
#
#
#
#@reference_formula
#class aefa(DatedFormulaColumn):




def pts_de_charge(distance_foy_etude, nb_enf_charge):
    pts_de_charge = 0

#distance lieu d'étude
    pts_de_charge = (distance_foy_etude >= 30) * 1
    pts_de_charge = (distance_foy_etude > 249) * 2



#children in the household  : chaque enfant à charge à l'exception du cadidat boursier compte pour 2 points

    pts_de_charge = pts_de_charge + ((nb_enf_charge - 1) * 2)


#S'ils sont étudiants ils comptent pour 2 pts suplémentaire
    pts_de_charge = pts_de_charge + ((nb_enf_charge_enseignementsup - 1) * 2)
    print(pts_de_charge)
    return pts_de_charge


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