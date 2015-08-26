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
                    {'start': u'2010-01-01', 'stop': u'2100-12-31', 'value': 2336}
                    ],
                },
            "celib_enf": {
                "@type": "Parameter",
                "description": "Cas célibataires avec enfant(s)",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2010-01-01', 'stop': u'2010-12-31', 'value': 4040},
                    {'start': u'2013-01-01', 'stop': u'2100-12-31', 'value': 4040}
                    ],
                },
            "veuf": {
                "@type": "Parameter",
                "description": "Veuf avec enfants à charge",
                "format": "integer",
                "values": [
                    {'start': u'2010-01-01', 'stop': u'2014-12-31', 'value': 2236}
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
#    af_base = Reform.column_by_name['af_base']
#    if len(af_base.formula_class.dated_formulas_class) > 1:
#        del af_base.formula_class.dated_formulas_class[1]
#        af_base.formula_class.dated_formulas_class[0]['stop_instant'] = None

#    @Reform.formula
#    class af_taux_modulation(formulas.DatedFormulaColumn):
#        column = columns.FloatCol
#        entity_class = Familles
#        label = u"Taux de modulation à appliquer au montant des AF depuis 2015"
#
#        @dated_function(start = date(2002, 1, 1))
#        def function_2002(self, simulation, period):
#            period = period.start.offset('first-of', 'month').period('month')
#            af_nbenf = simulation.calculate('af_nbenf', period)
#            return period, 1 + 0 * af_nbenf  # Trick pour avoir la bonne longueur d'array numpy. #Todo trouver mieux
#
#        @dated_function(start = date(9999, 7, 1))
#        def function_2015(self, simulation, period):
#            period = period.start.offset('first-of', 'month').period('month')
#            af_nbenf = simulation.calculate('af_nbenf', period)
#            pfam = simulation.legislation_at(period.start).fam.af
#            br_pf = simulation.calculate('br_pf', period)
#            modulation = pfam.modulation
#            plafond1 = modulation.plafond1 + af_nbenf * modulation.enfant_supp
#            plafond2 = modulation.plafond2 + af_nbenf * modulation.enfant_supp
#
#            taux = (
#                (br_pf <= plafond1) * 1 +
#                (br_pf > plafond1) * (br_pf <= plafond2) * modulation.taux1 +
#                (br_pf > plafond2) * modulation.taux2
#            )
#
#            return period, taux
#
#    @Reform.formula
#    class af_complement_degressif(DatedFormulaColumn):
#        column = FloatCol
#        entity_class = Familles
#        label = u"AF - Complément dégressif en cas de dépassement du plafond"
#    
#        @dated_function(start = date(9999, 7, 1))
#        def function_2015(self, simulation, period):
#            period = period.start.offset('first-of', 'month').period('month')
#            af_nbenf = simulation.calculate('af_nbenf', period)
#            br_pf = simulation.calculate('br_pf', period)
#            af_base = simulation.calculate('af_base', period)
#            af_majo = simulation.calculate('af_majo', period)
#            pfam = simulation.legislation_at(period.start).fam.af
#            modulation = pfam.modulation
#            plafond1 = modulation.plafond1 + af_nbenf * modulation.enfant_supp
#            plafond2 = modulation.plafond2 + af_nbenf * modulation.enfant_supp
#    
#            depassement_plafond1 = max_(0, br_pf - plafond1)
#            depassement_plafond2 = max_(0, br_pf - plafond2)
#    
#            depassement_mensuel = (
#                (depassement_plafond2 == 0) * depassement_plafond1 +
#                (depassement_plafond2 > 0) * depassement_plafond2
#            ) / 12
#    
#            af = af_base + af_majo
#            return period, max_(0, af - depassement_mensuel) * (depassement_mensuel > 0)
            
            
####################
####################
    @Reform.formula
    class af_taux_modulation(DatedFormulaColumn):
        column = FloatCol
        entity_class = Familles
        label = u"Taux de modulation à appliquer au montant des AF depuis 2015"
    
        @dated_function(start = date(2002, 1, 1))
        def function_2002(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            af_nbenf = simulation.calculate('af_nbenf', period)
            return period, 1 + 0 * af_nbenf  # Trick pour avoir la bonne longueur d'array numpy. #Todo trouver mieux
    
        @dated_function(start = date(9999, 7, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            af_nbenf = simulation.calculate('af_nbenf', period)
            pfam = simulation.legislation_at(period.start).fam.af
            br_pf = simulation.calculate('br_pf', period)
            modulation = pfam.modulation
            plafond1 = modulation.plafond1 + af_nbenf * modulation.enfant_supp
            plafond2 = modulation.plafond2 + af_nbenf * modulation.enfant_supp
    
            taux = (
                (br_pf <= plafond1) * 1 +
                (br_pf > plafond1) * (br_pf <= plafond2) * modulation.taux1 +
                (br_pf > plafond2) * modulation.taux2
            )
    
            return period, taux
    
    
    @Reform.formula
    class af_forf_taux_modulation(DatedFormulaColumn):
        column = FloatCol
        entity_class = Familles
        label = u"Taux de modulation à appliquer à l'allocation forfaitaire des AF depuis 2015"
    
        @dated_function(start = date(2002, 1, 1))
        def function_2002(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            af_nbenf = simulation.calculate('af_nbenf', period)
            return period, 1 + 0 * af_nbenf  # Trick pour avoir la bonne longueur d'array numpy. #Todo trouver mieux
    
        @dated_function(start = date(9999, 7, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            pfam = simulation.legislation_at(period.start).fam.af
            af_nbenf = simulation.calculate('af_nbenf', period)
            af_forf_nbenf = simulation.calculate('af_forf_nbenf', period)
            nb_enf_tot = af_nbenf + af_forf_nbenf
            br_pf = simulation.calculate('br_pf', period)
            modulation = pfam.modulation
            plafond1 = modulation.plafond1 + nb_enf_tot * modulation.enfant_supp
            plafond2 = modulation.plafond2 + nb_enf_tot * modulation.enfant_supp
    
            taux = (
                (br_pf <= plafond1) * 1 +
                (br_pf > plafond1) * (br_pf <= plafond2) * modulation.taux1 +
                (br_pf > plafond2) * modulation.taux2
            )
    
            return period, taux
    
    @Reform.formula
    class af_complement_degressif(DatedFormulaColumn):
        column = FloatCol
        entity_class = Familles
        label = u"AF - Complément dégressif en cas de dépassement du plafond"
    
        @dated_function(start = date(9999, 7, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            af_nbenf = simulation.calculate('af_nbenf', period)
            br_pf = simulation.calculate('br_pf', period)
            af_base = simulation.calculate('af_base', period)
            af_majo = simulation.calculate('af_majo', period)
            pfam = simulation.legislation_at(period.start).fam.af
            modulation = pfam.modulation
            plafond1 = modulation.plafond1 + af_nbenf * modulation.enfant_supp
            plafond2 = modulation.plafond2 + af_nbenf * modulation.enfant_supp
    
            depassement_plafond1 = max_(0, br_pf - plafond1)
            depassement_plafond2 = max_(0, br_pf - plafond2)
    
            depassement_mensuel = (
                (depassement_plafond2 == 0) * depassement_plafond1 +
                (depassement_plafond2 > 0) * depassement_plafond2
            ) / 12
    
            af = af_base + af_majo
            return period, max_(0, af - depassement_mensuel) * (depassement_mensuel > 0)
    
    
    @Reform.formula
    class af_forf_complement_degressif(DatedFormulaColumn):
        column = FloatCol
        entity_class = Familles
        label = u"AF - Complément dégressif pour l'allocation forfaitaire en cas de dépassement du plafond"
    
        @dated_function(start = date(9999, 7, 1))
        def function_2015(self, simulation, period):
            period = period.start.offset('first-of', 'month').period('month')
            af_nbenf = simulation.calculate('af_nbenf', period)
            af_forf_nbenf = simulation.calculate('af_forf_nbenf', period)
            pfam = simulation.legislation_at(period.start).fam.af
            nb_enf_tot = af_nbenf + af_forf_nbenf
            br_pf = simulation.calculate('br_pf', period)
            af_forf = simulation.calculate('af_forf', period)
            modulation = pfam.modulation
            plafond1 = modulation.plafond1 + nb_enf_tot * modulation.enfant_supp
            plafond2 = modulation.plafond2 + nb_enf_tot * modulation.enfant_supp
    
            depassement_plafond1 = max_(0, br_pf - plafond1)
            depassement_plafond2 = max_(0, br_pf - plafond2)
    
            depassement_mensuel = (
                (depassement_plafond2 == 0) * depassement_plafond1 +
                (depassement_plafond2 > 0) * depassement_plafond2
            ) / 12
    
            return period, max_(0, af_forf - depassement_mensuel) * (depassement_mensuel > 0)
            af_forf + af_complement_degressif + af_forf_complement_degressif
                
    return Reform()