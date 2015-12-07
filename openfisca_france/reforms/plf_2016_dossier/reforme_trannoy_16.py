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

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform


def modify_legislation_json(reference_legislation_json_copy):
    <BAREME code="bareme" description="Impôt de solidarité" type="monetary">
      <TRANCHE code="tranche0">
        <SEUIL>
          <VALUE deb="2001-01-01" fin="2014-12-31" valeur="0" />
        </SEUIL>
        <TAUX>
          <VALUE deb="2001-01-01" fin="2014-12-31" valeur="0" />
        </TAUX>
      </TRANCHE>
      <TRANCHE code="tranche1">
        <SEUIL>
          <VALUE deb="2002-01-01" fin="2004-12-31" valeur="720000" />
          <VALUE deb="2005-01-01" fin="2006-12-31" valeur="732000" />
          <VALUE deb="2007-01-01" fin="2007-12-31" valeur="760000" />
          <VALUE deb="2008-01-01" fin="2008-12-31" valeur="770000" />
          <VALUE deb="2009-01-01" fin="2009-12-31" valeur="790000" />
          <VALUE deb="2010-01-01" fin="2010-12-31" valeur="790000" />
          <VALUE deb="2011-01-01" fin="2014-12-31" valeur="800000" />
        </SEUIL>
        <TAUX>
          <VALUE deb="2002-01-01" fin="2012-12-31" valeur="0.0055" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="0.0050" />
        </TAUX>
      </TRANCHE>
      <TRANCHE code="tranche2">
        <SEUIL>
          <VALUE deb="2002-01-01" fin="2004-12-31" valeur="1160000" />
          <VALUE deb="2005-01-01" fin="2006-12-31" valeur="1180000" />
          <VALUE deb="2007-01-01" fin="2007-12-31" valeur="1220000" />
          <VALUE deb="2008-01-01" fin="2008-12-31" valeur="1240000" />
          <VALUE deb="2009-01-01" fin="2009-12-31" valeur="1280000" />
          <VALUE deb="2010-01-01" fin="2010-12-31" valeur="1290000" />
          <VALUE deb="2011-01-01" fin="2012-12-31" valeur="1310000" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="1300000" />
        </SEUIL>
        <TAUX>
          <VALUE deb="2002-01-01" fin="2012-12-31" valeur="0.0075" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="0.007" />
        </TAUX>
      </TRANCHE>
      <TRANCHE code="tranche3">
        <SEUIL>
          <VALUE deb="2002-01-01" fin="2004-12-31" valeur="2300000" />
          <VALUE deb="2005-01-01" fin="2006-12-31" valeur="2339000" />
          <VALUE deb="2007-01-01" fin="2007-12-31" valeur="2420000" />
          <VALUE deb="2008-01-01" fin="2008-12-31" valeur="2450000" />
          <VALUE deb="2009-01-01" fin="2009-12-31" valeur="2520000" />
          <VALUE deb="2010-01-01" fin="2010-12-31" valeur="2530000" />
          <VALUE deb="2011-01-01" fin="2012-12-31" valeur="2570000" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="2570000" />
        </SEUIL>
        <TAUX>
          <VALUE deb="2002-01-01" fin="2014-12-31" valeur="0.01" />
        </TAUX>
      </TRANCHE>
      <TRANCHE code="tranche4">
        <SEUIL>
          <VALUE deb="2002-01-01" fin="2004-12-31" valeur="3600000" />
          <VALUE deb="2005-01-01" fin="2006-12-31" valeur="3661000" />
          <VALUE deb="2007-01-01" fin="2007-12-31" valeur="3800000" />
          <VALUE deb="2008-01-01" fin="2008-12-31" valeur="3850000" />
          <VALUE deb="2009-01-01" fin="2009-12-31" valeur="3960000" />
          <VALUE deb="2010-01-01" fin="2010-12-31" valeur="3980000" />
          <VALUE deb="2011-01-01" fin="2012-12-31" valeur="4040000" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="5000000" />
        </SEUIL>
        <TAUX>
          <VALUE deb="2002-01-01" fin="2012-12-31" valeur="0.013" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="0.0125" />
        </TAUX>
      </TRANCHE>
      <TRANCHE code="tranche5">
        <SEUIL>
          <VALUE deb="2002-01-01" fin="2004-12-31" valeur="6900000" />
          <VALUE deb="2005-01-01" fin="2006-12-31" valeur="7017000" />
          <VALUE deb="2007-01-01" fin="2007-12-31" valeur="7270000" />
          <VALUE deb="2008-01-01" fin="2008-12-31" valeur="7360000" />
          <VALUE deb="2009-01-01" fin="2009-12-31" valeur="7570000" />
          <VALUE deb="2010-01-01" fin="2010-12-31" valeur="7600000" />
          <VALUE deb="2011-01-01" fin="2012-12-31" valeur="7710000" />
          <VALUE deb="2013-01-01" fin="2014-12-31" valeur="10000000" />
        </SEUIL>
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "reforme Trannoy taux 16 en 2015",
        "children": {
            "bareme": {
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
