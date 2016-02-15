from __future__ import division

from openfisca_france.tests.base import tax_benefit_system
from openfisca_france.reforms.mensualisation import mensualisation_ir_3 as mensualisation_ir
from openfisca_utils.make_ready_to_use_scenario import make_single_with_child_scenario
from matplotlib import pyplot as plt




#from openfisca_parsers import source_formulas_extractors

#source_list = source_formulas_extractors.extract_source_formulas(tax_benefit_system, "ip_net")


#import ipdb
#ipdb.set_trace()

reforme = mensualisation_ir.build_reform(tax_benefit_system)

scenario = make_single_with_child_scenario(tax_benefit_system = reforme, year = 2014)

simulation = scenario.new_simulation()
reference_simulation = scenario.new_simulation(debug = True, reference = True)

simulation.calculate("rni", "2014-01")

ir_brut_mensualise = simulation.calculate("ir_brut", "2014-01")
ir_brut = reference_simulation.calculate("ir_brut", "2014")

#difference = ir_brut - ir_brut_mensualise
difference = ir_brut - ir_brut_mensualise
#TODO : assert if > 30
#plt.plot(difference)
#plt.show()



print simulation.calculate("ir_plaf_qf", "2014-02")

print simulation.calculate("iaidrdi", "2014")


iaidrdi_reference = reference_simulation.calculate("iaidrdi", "2014")

iaidrdi = simulation.calculate("iaidrdi", "2014")


difference = iaidrdi_reference - iaidrdi
#plt.plot(difference)
#plt.ylim([-1,90])
#plt.show()

simulation.calculate('irpp',"2014-01")
simulation.calculate("revdisp", "2014-01")