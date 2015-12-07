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
from openfisca_core.formulas import (DatedFormulaColumn, calculate_output_add, calculate_output_add_divide, 
    calculate_output_divide,dated_function, DatedFormulaColumn, EntityToPersonColumn, last_duration_last_value,
    make_reference_formula_decorator, missing_value, PersonToEntityColumn, reference_input_variable,
    requested_period_added_value, requested_period_default_value, requested_period_last_value,
    set_input_dispatch_by_period, set_input_divide_by_period, SimpleFormulaColumn)

from datetime import date

from numpy import minimum as min_, maximum as max_, logical_not as not_
from openfisca_france.model.base import QUIFOY, QUIFAM
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
    class decote(formulas.SimpleFormulaColumn):
        label = u"Nouvelle décote 2015"
        reference = ir.decote

        def function(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period)
            plf = simulation.legislation_at(period.start).plf2015

            decote_celib = (ir_plaf_qf < plf.decote_seuil_celib) * (plf.decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < plf.decote_seuil_couple) * (plf.decote_seuil_couple - ir_plaf_qf)
            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple
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
            


    @Reform.formula
    class rev_cat_rvcm(DatedFormulaColumn):
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"Revenu catégoriel - Capitaux"
        url = "http://www.insee.fr/fr/methodes/default.asp?page=definitions/revenus-categoriesl.htm"
        @dated_function(start = date(2002, 1, 1), stop = date(2015, 12, 31))
        def function_20130101_20151231(self, simulation, period):
            """
            Revenus des valeurs et capitaux mobiliers
            """
            period = period.start.offset('first-of', 'year').period('year')
            marpac = simulation.calculate('marpac', period)
            deficit_rcm = simulation.calculate('deficit_rcm', period)
            f2ch = simulation.calculate('f2ch', period)
            f2dc = simulation.calculate('f2dc', period)
            f2ts = simulation.calculate('f2ts', period)
            f2ca = simulation.calculate('f2ca', period)
            f2fu = simulation.calculate('f2fu', period)
            f2go = simulation.calculate('f2go', period)
            f2tr = simulation.calculate('f2tr', period)
            f2da = simulation.calculate('f2da', period)
            f2ee = simulation.calculate('f2ee', period)
            finpfl = simulation.legislation_at(period.start).ir.autre.finpfl
            rvcm = simulation.legislation_at(period.start).ir.rvcm
    
            # Add f2da to f2dc and f2ee to f2tr when no PFL
            f2dc_bis = f2dc + f2da  # TODO: l'abattement de 40% est déduit uniquement en l'absence de revenus déclarés case 2DA
            f2tr_bis = f2tr + f2ee
    
            # # Calcul du revenu catégoriel
            # 1.2 Revenus des valeurs et capitaux mobiliers
            b12 = min_(f2ch, rvcm.abat_assvie * (1 + marpac))
            TOT1 = f2ch - b12  # c12
            # Part des frais s'imputant sur les revenus déclarés case DC
            den = ((f2dc_bis + f2ts) != 0) * (f2dc_bis + f2ts) + ((f2dc_bis + f2ts) == 0)
            F1 = f2ca / den * f2dc_bis  # f12
            # Revenus de capitaux mobiliers nets de frais, ouvrant droit à abattement
            # partie négative (à déduire des autres revenus nets de frais d'abattements
            g12a = -min_(f2dc_bis * (1 - rvcm.abatmob_taux) - F1, 0)
            # partie positive
            g12b = max_(f2dc_bis * (1 - rvcm.abatmob_taux) - F1, 0)
            rev = g12b + f2fu * (1 - rvcm.abatmob_taux)
    
            # Abattements, limité au revenu
            h12 = rvcm.abatmob * (1 + marpac)
            TOT2 = max_(0, rev - h12)
            # i121= -min_(0,rev - h12)
    
            # Part des frais s'imputant sur les revenus déclarés ligne TS
            F2 = f2ca - F1
            TOT3 = (f2ts - F2) + f2go * rvcm.majGO + f2tr_bis - g12a
    
            DEF = deficit_rcm
            return period, max_(TOT1 + TOT2 + TOT3 - DEF, 0)



    
    @Reform.formula
    class rev_cap_lib(DatedFormulaColumn):
        '''Revenu du capital imposé au prélèvement libératoire
    
        Annuel pour les impôts mais mensuel pour la base ressource des minimas sociaux donc mensuel.
        '''
        calculate_output = calculate_output_add
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"rev_cap_lib"
        set_input = set_input_divide_by_period
        url = "http://fr.wikipedia.org/wiki/Revenu#Revenu_du_Capital"
    
        @dated_function(start = date(2002, 1, 1), stop = date(2015, 12, 31))
        def function_20080101_20151231(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            year = period.start.offset('first-of', 'year').period('year')
            f2da = simulation.calculate('f2da', year)
            f2dh = simulation.calculate('f2dh', year)
            f2ee = simulation.calculate('f2ee', year)
            _P = simulation.legislation_at(period.start)
            finpfl = simulation.legislation_at(period.start).ir.autre.finpfl
    
            out = f2da + f2dh + f2ee
            return period, out * not_(finpfl) / 12
#    VOUS = QUIFOY['vous']
#    CONJ = QUIFOY['conj']
#    CHEF = QUIFAM['chef']       
#    @Reform.formula
#    class plus_values(DatedFormulaColumn):
#        column = FloatCol(default = 0)
#        entity_class = FoyersFiscaux
#        label = u"plus_values"
#        @dated_function(start = date(2002, 1, 1), stop = date(2015, 12, 31))
#        def function_20130101_20151231(self, simulation, period):  # f3sd is in f3vd holder
#            """
#            Taxation des plus value
#            TODO: f3vt, 2013 f3Vg au barème / tout refaire
#            """
#            period = period.start.offset('first-of', 'year').period('year')
#            f3vg = simulation.calculate('f3vg', period)
#            f3vh = simulation.calculate('f3vh', period)
#            f3vl = simulation.calculate('f3vl', period)
#            f3vm = simulation.calculate('f3vm', period)
#            f3vi_holder = simulation.compute('f3vi', period)
#            f3vf_holder = simulation.compute('f3vf', period)
#            f3vd_holder = simulation.compute('f3vd', period)
#            f3sa = simulation.calculate('f3sa', period)
#            rpns_pvce_holder = simulation.compute('rpns_pvce', period)
#            _P = simulation.legislation_at(period.start)
#            plus_values = simulation.legislation_at(period.start).ir.plus_values
#    
#            rpns_pvce = self.sum_by_entity(rpns_pvce_holder)
#            f3vd = self.filter_role(f3vd_holder, role = VOUS)
#            f3sd = self.filter_role(f3vd_holder, role = CONJ)
#            f3vi = self.filter_role(f3vi_holder, role = VOUS)
#            f3si = self.filter_role(f3vi_holder, role = CONJ)
#            f3vf = self.filter_role(f3vf_holder, role = VOUS)
#            f3sf = self.filter_role(f3vf_holder, role = CONJ)
#            #  TODO: remove this todo use sum for all fields after checking
#            # revenus taxés à un taux proportionnel
#            rdp = max_(0, f3vg - f3vh) + f3vl + rpns_pvce + f3vm + f3vi + f3vf
#            out = (plus_values.pvce * rpns_pvce +
#                   plus_values.taux1 * max_(0, f3vg - f3vh) +
#                   plus_values.caprisque * f3vl +
#                   plus_values.pea * f3vm +
#                   plus_values.taux3 * f3vi +
#                   plus_values.taux4 * f3vf)
#    
#            # revenus taxés à un taux proportionnel
#            rdp += f3vd
#            out += plus_values.taux1 * f3vd
#            #  out = plus_values.taux2 * f3vd + plus_values.taux3 * f3vi + plus_values.taux4 * f3vf + plus_values.taux1 * max_(
#            #          0, f3vg - f3vh)
#            out = (plus_values.taux2 * (f3vd + f3sd) + plus_values.taux3 * (f3vi + f3si) +
#                plus_values.taux4 * (f3vf + f3sf) + plus_values.taux1 * max_(0, - f3vh) + plus_values.pvce * (rpns_pvce + f3sa))
#            # TODO: chek this 3VG
#            return period, round(out)


    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform



def modify_legislation_json(reference_legislation_json_copy):
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2015",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1135}],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1870}],
                },
            },
        }
    reform_period = periods.period('year', 2002,20)
    # FIXME update_legislation is deprecated.
#    reference_legislation_json_copy = reforms.update_legislation(
#        legislation_json = reference_legislation_json_copy,
#        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'rate'),
#        period = reform_period,
#        value = 0,
#        )
    # FIXME update_legislation is deprecated.
#    reference_legislation_json_copy = reforms.update_legislation(
#        legislation_json = reference_legislation_json_copy,
#        path = ('children', 'ir', 'children', 'bareme', 'brackets', 2, 'threshold'),
#        period = reform_period,
#        value = 9690,
#        )
    reference_legislation_json_copy['children']['plf2015'] = reform_legislation_subtree
    return reference_legislation_json_copy
