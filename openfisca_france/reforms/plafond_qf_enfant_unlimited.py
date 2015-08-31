# -*- coding: utf-8 -*-

from __future__ import division

import copy
from openfisca_core.columns import FloatCol
from openfisca_core import reforms, columns
from openfisca_core.formulas import dated_function, DatedFormulaColumn
from openfisca_france.entities import Familles
from openfisca_france.tests import base

from datetime import date

# Reform legislation

reform_legislation_subtree = {
    "plafond_qf": {
        "@type": "Node",
        "description": "Plafonnement du quotient familial",
        "children": {
            "marpac": {
                "@type": "Parameter",
                "description": "Mariés ou PACS",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2000-01-01', 'stop': u'2100-12-31', 'value': 10**10}
                    ],
                },
            "celib_enf": {
                "@type": "Parameter",
                "description": "Cas célibataires avec enfant(s)",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2000-01-01', 'stop': u'2010-12-31', 'value': 10**10},
                    {'start': u'2013-01-01', 'stop': u'2100-12-31', 'value': 10**10}
                    ],
                },
            "veuf": {
                "@type": "Parameter",
                "description": "Veuf avec enfants à charge",
                "format": "integer",
                "values": [
                    {'start': u'2000-01-01', 'stop': u'2014-12-31', 'value': 10**10}
                    ],
                },
            }
        }
    }
#TODO : actualise parameters with respect to inflation

tax_benefit_system =  base.tax_benefit_system
def build_reform(tax_benefit_system):
    # Update legislation
    reference_legislation_json = tax_benefit_system.legislation_json
    reform_legislation_json = copy.deepcopy(reference_legislation_json)
    reform_legislation_json['children']['ir']['children']['plafond_qf']['children'].update(
        reform_legislation_subtree['plafond_qf']['children'])



    # Removing the formula starting in 2015-07-01
    # TODO: improve because very dirty
    # may be by creating the following functions
    # get_formulas(entity, variable, period), set_formulas(entity, variable, period)


    
    Reform = reforms.make_reform(
        legislation_json = reform_legislation_json,
        name = u"Legislion du plafond qf de 2012 et des af sans modulations",
        reference = tax_benefit_system,
        )