# -*- coding: utf-8 -*-

from __future__ import division


from openfisca_core import columns, formulas, reforms


from ...model.prelevements_obligatoires.impot_revenu import ir


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'suppression_decote',
        name = u'Suppression decote',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Nouveau revenu brut global intégrant les allocations familiales"
        reference = ir.decote

        #@dated_function(start = date(2015, 1, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            print "suppression decote marche"

            return period, 0 * ir_plaf_qf
    reform = Reform()
    return reform