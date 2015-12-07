# -*- coding: utf-8 -*-

import datetime


from openfisca_core import periods
from openfisca_core.tools import assert_near
from openfisca_france.tests.base import tax_benefit_system

import openfisca_france.reforms.plf_2016_dossier.suppression_decote as reform1
def test_allocations_familiales_imposables():
    year = 2012
    reform = reform1.build_reform(tax_benefit_system)
    scenario = reform.new_scenario().init_single_entity(
        axes = [
            dict(
                count = 10,
                max = 30000,
                min = 0,
                name = 'salaire_imposable',
                ),
            ],
        period = periods.period('year', year),
        parent1 = dict(birth = datetime.date(year - 40, 1, 1)),
        parent2 = dict(birth = datetime.date(year - 40, 1, 1)),
        enfants = [
            dict(birth = datetime.date(year - 9, 1, 1)),
            dict(birth = datetime.date(year - 9, 1, 1)),
            ],
        )

    reference_simulation = scenario.new_simulation(debug = True, reference = True)

    rbg = reference_simulation.calculate('revdisp')

    reform_rbg = reform_simulation.calculate('rbg')
    print 'hello'


if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level = logging.ERROR, stream = sys.stdout)
    test_allocations_familiales_imposables()
