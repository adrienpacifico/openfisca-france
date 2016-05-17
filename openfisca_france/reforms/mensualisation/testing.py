from __future__ import division

from openfisca_france.tests.base import tax_benefit_system
from openfisca_france.reforms.mensualisation import mensualisation_ir_5 as mensualisation_ir
from openfisca_utils.make_ready_to_use_scenario import make_single_with_child_scenario
from matplotlib import pyplot as plt

import numpy as np
np.set_printoptions(suppress = True, precision = 4)


# from openfisca_parsers import source_formulas_extractors

# source_list = source_formulas_extractors.extract_source_formulas(tax_benefit_system, "ip_net")


# import ipdb
# ipdb.set_trace()

reforme = mensualisation_ir.build_reform(tax_benefit_system)

scenario = make_single_with_child_scenario(tax_benefit_system = reforme, year = 2014,
                                           ax_variable_max=100000, count=10,
                                           axes_variable= 'salaire_imposable')
# 100 000 annuel

simulation = scenario.new_simulation()
reference_simulation = scenario.new_simulation(debug = True, reference = True)


print simulation.calculate("rng_mensuel_times_12", "2014-01")
print reference_simulation.calculate("rng", "2014")

print simulation.calculate("rni_mensuel_times_12", "2014-01")
print reference_simulation.calculate("rni", "2014")


ir_brut_mensualise = simulation.calculate("ir_brut_mensuel_times_12", "2014-01")
ir_brut = reference_simulation.calculate("ir_brut", "2014")


simulation.calculate("ip_net_mensuel", "2014-01")*12


# difference = ir_brut - ir_brut_mensualise
difference = ir_brut - ir_brut_mensualise
# TODO : assert if > 30
# plt.plot(difference)
# plt.show()




print "ir_plaf_qf", simulation.calculate("ir_plaf_qf", "2014-02")
print "ir_plaf_qf_add", simulation.calculate_add("ir_plaf_qf")

print simulation.calculate("ip_net_mensuel", '2014-01')

print "ip_net_mensuel", simulation.calculate_add("ip_net_mensuel", '2014')
print "ip_net", reference_simulation.calculate("ip_net", '2014')



print simulation.calculate("iaidrdi", "2014")


iaidrdi_reference = reference_simulation.calculate("iaidrdi", "2014")

iaidrdi = simulation.calculate("iaidrdi", "2014")


difference = iaidrdi_reference - iaidrdi
#plt.plot(difference)
#plt.ylim([-1,90])
#plt.show()

print "irpp", simulation.calculate('irpp',"2014-01")


print simulation.calculate("revdisp", "2014-01")


simulation.calculate_add_divide()


from openfisca_core.columns import Column

def json_to_():
    return
Column.json_to_python = json_to_()



