from __future__ import division

import openfisca_core
from openfisca_core import periods
from openfisca_core import simulations
from openfisca_france.tests.base import tax_benefit_system
from openfisca_france.reforms.mensualisation import mensualisation_ir_3 as mensualisation_ir

old_calculate = simulations.Simulation.calculate

def new_calculate(self, column_name, period = None, **parameters):
    print column_name
    try:
        return old_calculate(self, column_name = column_name, period = period, **parameters)
    except AssertionError as e:
        print e
        print column_name
        new_period = periods.period(period).this_year
        return old_calculate(self, column_name = column_name, period = new_period, **parameters) / 12

simulations.Simulation.calculate = new_calculate

from openfisca_utils.make_ready_to_use_scenario import make_single_with_child_scenario





simulation = tax_benefit_system.new_scenario().init_single_entity(
    parent1 = dict(age = 36, salaire_de_base = 100000),
    period = 2014
    ).new_simulation()

reform = mensualisation_ir.build_reform(tax_benefit_system)
reform_simulation = tax_benefit_system.new_scenario().init_single_entity(
    parent1 = dict(age = 36, salaire_de_base = 100000),
    period = 2014
    ).new_simulation()

assert simulation.calculate("salaire_de_base") == 100000
print simulation.calculate('irpp', "2014")

print simulation.calculate('irpp', "2014-01")

assert reform_simulation.calculate("salaire_de_base") == 100000

print reform_simulation.calculate('ir_plaf_qf', "2014")

