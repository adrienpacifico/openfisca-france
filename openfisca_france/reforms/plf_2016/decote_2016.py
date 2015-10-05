# -*- coding: utf-8 -*-

from __future__ import division

from openfisca_core import formulas, periods, reforms
from ...model.base import *
from ...model.prelevements_obligatoires.impot_revenu import ir


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf2016',
        name = u'Projet de Loi de Finances 2016',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Décote IR 2015 appliquée sur IR 2014 (revenus 2013)"
        reference = ir.decote

        @dated_function(start = date(2015, 1, 1), stop = date(2016, 12, 31) )
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period)
            plf = simulation.legislation_at(period.start).plf2015
            print 'hello'
            decote_celib = (ir_plaf_qf < plf.decote_seuil_celib) * (plf.decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < plf.decote_seuil_couple) * (plf.decote_seuil_couple - ir_plaf_qf)
            return period, ((nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple) * 0.75

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform


def modify_legislation_json(reference_legislation_json_copy):
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2015 sur revenus 2013",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2013-01-01', 'stop': u'2013-12-31', 'value': 1553}],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2013-01-01', 'stop': u'2013-12-31', 'value': 2560}],
                },
            },
        }
    reform_year = 2015
    reform_period = periods.period('year', reform_year)
    # FIXME update_legislation is deprecated.
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'rate'),
        period = reform_period,
        value = 0,
        )
    # FIXME update_legislation is deprecated.
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 2, 'threshold'),
        period = reform_period,
        value = 9700,
        )
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 3, 'threshold'),
        period = reform_period,
        value = 26791,
        )
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 4, 'threshold'),
        period = reform_period,
        value = 71826,
        )
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 5, 'threshold'),
        period = reform_period,
        value = 152108,
        )
    reference_legislation_json_copy['children']['plf2015'] = reform_legislation_subtree
    return reference_legislation_json_copy
