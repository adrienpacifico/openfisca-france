# -*- coding: utf-8 -*-

import datetime

from nose.tools import assert_less

from openfisca_core import periods
from openfisca_france.tests import base
from openfisca_france.reforms.plf_2016 import decote_2016
from openfisca_france.tests.base import tax_benefit_system


#TODO: put the import in base.
def test(year = 2015):
    max_sal = 18000
    count = 2
    people = 1
    reform = decote_2016.build_reform(tax_benefit_system)
    scenario = reform.new_scenario().init_single_entity(
        axes = [
            dict(
                count = count,
                max = max_sal,
                min = 0,
                name = 'salaire_imposable',
                ),
            ],
        period = periods.period('year', year),
        parent1 = dict(birth = datetime.date(year - 40, 1, 1)),
        parent2 = dict(birth = datetime.date(year - 40, 1, 1)) if people >= 2 else None,
        enfants = [
            dict(birth = datetime.date(year - 9, 1, 1)) if people >= 3 else None,
            dict(birth = datetime.date(year - 9, 1, 1)) if people >= 4 else None,
            ] if people >= 3 else None,
        )

    reference_simulation = scenario.new_simulation(debug = True, reference = True)
    reform_simulation = scenario.new_simulation(debug = True)
    error_margin = 1

    impo = reference_simulation.calculate('impo')
    reform_impo = reform_simulation.calculate('impo')
    ir_plaf_qf = reference_simulation.calculate('ir_plaf_qf')
    reform_ir_plaf_qf = reform_simulation.calculate('ir_plaf_qf')



if __name__ == '__main__':
    import logging
    import sys
    logging.basicConfig(level = logging.ERROR, stream = sys.stdout)
    test()
