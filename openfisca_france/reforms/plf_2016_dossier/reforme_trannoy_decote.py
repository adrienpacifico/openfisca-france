# -*- coding: utf-8 -*-

from __future__ import division

from openfisca_core import formulas, periods, reforms
from ...model.base import *
from ...model.prelevements_obligatoires.impot_revenu import ir






def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf_2016',
        name = u'Proposition de reforme Trannoy',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Suppression décote"
        reference = ir.decote

        @dated_function(start = date(2015, 1, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            print "decote marche"

            return period, 0 * ir_plaf_qf

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform
def modify_legislation_json(reference_legislation_json_copy):

    reform_year = 2015
    reform_period = periods.period('year', reform_year)
    # FIXME update_legislation is deprecated.
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'rate'),
        period = reform_period,
        value = 0.16,
        )
    reference_legislation_json_copy = reforms.update_legislation(
        legislation_json = reference_legislation_json_copy,
        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'threshold'),
        period = reform_period,
        value = 17800,#17800
        )
    # FIXME update_legislation is deprecated.

    return reference_legislation_json_copy