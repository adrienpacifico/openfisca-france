from openfisca_france.tests.base import tax_benefit_system
from openfisca_utils.make_ready_to_use_scenario import make_single_with_child_scenario
from openfisca_france.reforms.mensualisation import allocation_chomage
reforme = allocation_chomage.build_reform(tax_benefit_system)
scenario = make_single_with_child_scenario(tax_benefit_system = reforme, year = 2014)
simulation = scenario.new_simulation()
print simulation.calculate('chomage_are',"2014-01")