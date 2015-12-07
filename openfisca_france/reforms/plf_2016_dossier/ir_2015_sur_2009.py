# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# TODO switch to to average tax rates

from __future__ import division

from openfisca_core import formulas, periods, reforms
from openfisca_core.columns import FloatCol
from entities import entity_class_by_symbol, Familles, FoyersFiscaux, Individus, Menages

from model.prelevements_obligatoires.impot_revenu import ir


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf2015_2',
        name = u'Projet de Loi de Finances 2015',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.SimpleFormulaColumn):
        label = u"Nouvelle décote 2015"
        reference = ir.decote

        def function(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period)
            plf = simulation.legislation_at(period.start).plf2015

            decote_celib = (ir_plaf_qf < plf.decote_seuil_celib) * (plf.decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < plf.decote_seuil_couple) * (plf.decote_seuil_couple - ir_plaf_qf)
            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple
            
      
    
    @Reform.formula
    class ir_brut(formulas.SimpleFormulaColumn):
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"
    
        def function(self, simulation, period):
            period_init = period
            period = periods.period('year', 2015)
            period = period.start.offset('first-of', 'month').period('year')
            nbptr = simulation.calculate('nbptr', period)
            taux_effectif = simulation.calculate('taux_effectif', period)
            rni = simulation.calculate('rni', period)
            bareme = simulation.legislation_at(period.start).ir.bareme
            print bareme
    
            return period_init, (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni      
            
            



def modify_legislation_json(reference_legislation_json_copy):
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2015",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1135}],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1870}],
                },
            },
        }            
            
            
            
            
            
            

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform


#def modify_legislation_json(reference_legislation_json_copy):
#    reform_legislation_subtree = {
#        "bareme": {
#        "@type": "Node",
#        "description": "Tranches de l'IR",
#        "type":"monetary",
#        }
#        "@type": "Node",
#        "description": "PLF 2015",
#        "children": {
#            "bareme": {
#                "@type": "Parameter",
#                "description": "Seuil de la décôte pour un célibataire",
#                "format": "integer",
#                "unit": "currency",
#                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1135}],
#                },
#            "decote_seuil_couple": {
#                "@type": "Parameter",
#                "description": "Seuil de la décôte pour un couple",
#                "format": "integer",
#                "unit": "currency",
#                "values": [{'start': u'2002-01-01', 'stop': u'2014-12-31', 'value': 1870}],
#                },
#            },
#        }
        
       #####IR####### 
        

#
#@reference_formula
#class ir_brut(SimpleFormulaColumn):
#    column = FloatCol(default = 0)
#    entity_class = FoyersFiscaux
#    label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"
#
#    def function(self, simulation, period):
#        period = period.start.offset('first-of', 'month').period('year')
#        nbptr = simulation.calculate('nbptr', period)
#        taux_effectif = simulation.calculate('taux_effectif', period)
#        rni = simulation.calculate('rni', period)
#        bareme = simulation.legislation_at(period.start).ir.bareme
#
#        return period, (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni
#        
#        
#        
#
#@reference_formula
#class ir_ss_qf(SimpleFormulaColumn):
#    column = FloatCol(default = 0)
#    entity_class = FoyersFiscaux
#    label = u"ir_ss_qf"
#
#    def function(self, simulation, period):
#        '''
#        Impôt sans quotient familial
#        '''
#        period = period.start.offset('first-of', 'year').period('year')
#        ir_brut = simulation.calculate('ir_brut', period)
#        rni = simulation.calculate('rni', period)
#        nb_adult = simulation.calculate('nb_adult', period)
#        bareme = simulation.legislation_at(period.start).ir.bareme
#
#        A = bareme.calc(rni / nb_adult)
#        return period, nb_adult * A
#
#
#@reference_formula
#class ir_plaf_qf(SimpleFormulaColumn):
#    column = FloatCol(default = 0)
#    entity_class = FoyersFiscaux
#    label = u"ir_plaf_qf"
#
#    def function(self, simulation, period):
#        '''
#        Impôt après plafonnement du quotient familial et réduction complémentaire
#        '''
#        period = period.start.offset('first-of', 'year').period('year')
#        ir_brut = simulation.calculate('ir_brut', period)
#        ir_ss_qf = simulation.calculate('ir_ss_qf', period)
#        nb_adult = simulation.calculate('nb_adult', period)
#        nb_pac = simulation.calculate('nb_pac', period)
#        nbptr = simulation.calculate('nbptr', period)
#        marpac = simulation.calculate('marpac', period)
#        veuf = simulation.calculate('veuf', period)
#        jveuf = simulation.calculate('jveuf', period)
#        celdiv = simulation.calculate('celdiv', period)
#        caseE = simulation.calculate('caseE', period)
#        caseF = simulation.calculate('caseF', period)
#        caseG = simulation.calculate('caseG', period)
#        caseH = simulation.calculate('caseH', period)
#        caseK = simulation.calculate('caseK', period)
#        caseN = simulation.calculate('caseN', period)
#        caseP = simulation.calculate('caseP', period)
#        caseS = simulation.calculate('caseS', period)
#        caseT = simulation.calculate('caseT', period)
#        caseW = simulation.calculate('caseW', period)
#        nbF = simulation.calculate('nbF', period)
#        nbG = simulation.calculate('nbG', period)
#        nbH = simulation.calculate('nbH', period)
#        nbI = simulation.calculate('nbI', period)
#        nbR = simulation.calculate('nbR', period)
#        plafond_qf = simulation.legislation_at(period.start).ir.plafond_qf
#
#        A = ir_ss_qf
#        I = ir_brut
#
#        aa0 = (nbptr - nb_adult) * 2  # nombre de demi part excédant nbadult
#        # on dirait que les impôts font une erreur sur aa1 (je suis obligé de
#        # diviser par 2)
#        aa1 = min_((nbptr - 1) * 2, 2) / 2  # deux première demi part excédants une part
#        aa2 = max_((nbptr - 2) * 2, 0)  # nombre de demi part restantes
#        # celdiv parents isolés
#        condition61 = celdiv & caseT
#        B1 = plafond_qf.celib_enf * aa1 + plafond_qf.marpac * aa2
#        # tous les autres
#        B2 = plafond_qf.marpac * aa0  # si autre
#        # celdiv, veufs (non jveuf) vivants seuls et autres conditions
#        # TODO: année en dur... pour caseH
#        condition63 = (celdiv | (veuf & not_(jveuf))) & not_(caseN) & (nb_pac == 0) & (caseK | caseE) & (caseH < 1981)
#        B3 = plafond_qf.celib
#
#        B = B1 * condition61 + \
#            B2 * (not_(condition61 | condition63)) + \
#            B3 * (condition63 & not_(condition61))
#        C = max_(0, A - B)
#        # Impôt après plafonnement
#        IP0 = max_(I, C)
#
#        # 6.2 réduction d'impôt pratiquée sur l'impot après plafonnement et le cas particulier des DOM
#        # pas de réduction complémentaire
#        condition62a = (I >= C)
#        # réduction complémentaire
#        condition62b = (I < C)
#        # celdiv veuf
#        condition62caa0 = (celdiv | (veuf & not_(jveuf)))
#        condition62caa1 = (nb_pac == 0) & (caseP | caseG | caseF | caseW)
#        condition62caa2 = caseP & ((nbF - nbG > 0) | (nbH - nbI > 0))
#        condition62caa3 = not_(caseN) & (caseE | caseK) & (caseH >= 1981)
#        condition62caa = condition62caa0 & (condition62caa1 | condition62caa2 | condition62caa3)
#        # marié pacs
#        condition62cab = (marpac | jveuf) & caseS & not_(caseP | caseF)
#        condition62ca = (condition62caa | condition62cab)
#
#        # plus de 590 euros si on a des plus de
#        condition62cb = ((nbG + nbR + nbI) > 0) | caseP | caseF
#        D = plafond_qf.reduc_postplafond * (condition62ca + ~condition62ca * condition62cb * (
#            1 * caseP + 1 * caseF + nbG + nbR + nbI / 2))
#
#        E = max_(0, A - I - B)
#        Fo = D * (D <= E) + E * (E < D)
#        IP1 = IP0 - Fo
#
#        # TODO: 6.3 Cas particulier: Contribuables domiciliés dans les DOM.
#        # conditionGuadMarReu =
#        # conditionGuyane=
#        # conitionDOM = conditionGuadMarReu | conditionGuyane
#        # postplafGuadMarReu = 5100
#        # postplafGuyane = 6700
#        # IP2 = IP1 - conditionGuadMarReu*min( postplafGuadMarReu,.3*IP1)  - conditionGuyane*min(postplafGuyane,.4*IP1)
#
#        # Récapitulatif
#
#        return period, condition62a * IP0 + condition62b * IP1  # IP2 si DOM        
#        
#
#        
#        
#        
#        
#        
#        
#        
#        
#    reform_period = periods.period('year', 2002,20)
#    # FIXME update_legislation is deprecated.
##    reference_legislation_json_copy = reforms.update_legislation(
##        legislation_json = reference_legislation_json_copy,
##        path = ('children', 'ir', 'children', 'bareme', 'brackets', 1, 'rate'),
##        period = reform_period,
##        value = 0,
##        )
#    # FIXME update_legislation is deprecated.
##    reference_legislation_json_copy = reforms.update_legislation(
##        legislation_json = reference_legislation_json_copy,
##        path = ('children', 'ir', 'children', 'bareme', 'brackets', 2, 'threshold'),
##        period = reform_period,
##        value = 9690,
##        )
#    reference_legislation_json_copy['children']['plf2015'] = reform_legislation_subtree
#    return reference_legislation_json_copy
#
#
#
#
#
#
#
#




        
        
#        
#def modify_legislation_json(reference_legislation_json_copy):
#    plfr2014_legislation_subtree = {
#        "@type": "Node",
#        "description": "Projet de loi de finance rectificative 2014",
#        "children": {
#            "reduction_impot_exceptionnelle": {
#                "@type": "Node",
#                "description": "Réduction d'impôt exceptionnelle",
#                "children": {
#                    "montant_plafond": {
#                        "@type": "Parameter",
#                        "description": "Montant plafond par part pour les deux premières parts",
#                        "format": "integer",
#                        "unit": "currency",
#                        "values": [{'start': u'2013-01-01', 'stop': u'2014-12-31', 'value': 350}],
#                        },
#                    "seuil": {
#                        "@type": "Parameter",
#                        "description": "Seuil (à partir duquel la réduction décroît) par part pour les deux "
#                                       "premières parts",
#                        "format": "integer",
#                        "unit": "currency",
#                        "values": [{'start': u'2013-01-01', 'stop': u'2014-12-31', 'value': 13795}],
#                        },
#                    "majoration_seuil": {
#                        "@type": "Parameter",
#                        "description": "Majoration du seuil par demi-part supplémentaire",
#                        "format": "integer",
#                        "unit": "currency",
#                        "values": [{'start': u'2013-01-01', 'stop': u'2014-12-31', 'value': 3536}],
#                        },
#                    },
#                },
#            },
#        }
#    plfrss2014_legislation_subtree = {
#        "@type": "Node",
#        "description": "Barème 2015 sur 2009",
#        "children": {
#            "exonerations_bas_salaires": {
#                "@type": "Node",
#                "description": "Exonérations de cotisations salariées sur les bas salaires",
#                "children": {
#                    "prive": {
#                        "@type": "Node",
#                        "description": "Salariés du secteur privé",
#                        "children": {
#                            "taux": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.03}],
#                                },
#                            "seuil": {
#                                "@type": "Parameter",
#                                "description": "Seuil (en SMIC)",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 1.3}],
#                                },
#                            },
#                        },
#                    "public": {
#                        "@type": "Node",
#                        "description": "Salariés du secteur public",
#                        "children": {
#                            "taux_1": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.02}],
#                                },
#                            "seuil_1": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 312}],
#                                },
#                            "taux_2": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.018}],
#                                },
#                            "seuil_2": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 328}],
#                                },
#                            "taux_3": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.016}],
#                                },
#                            "seuil_3": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 343}],
#                                },
#                            "taux_4": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.014}],
#                                },
#                            "seuil_4": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 359}],
#                                },
#                            "taux_5": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.012}],
#                                },
#                            "seuil_5": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 375}],
#                                },
#                            "taux_6": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.01}],
#                                },
#                            "seuil_6": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 390}],
#                                },
#                            "taux_7": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.008}],
#                                },
#                            "seuil_7": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 406}],
#                                },
#                            "taux_8": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.007}],
#                                },
#                            "seuil_8": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 421}],
#                                },
#                            "taux_9": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.006}],
#                                },
#                            "seuil_9": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 437}],
#                                },
#                            "taux_10": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.005}],
#                                },
#                            "seuil_10": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 453}],
#                                },
#                            "taux_11": {
#                                "@type": "Parameter",
#                                "description": "Taux",
#                                "format": "rate",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 0.002}],
#                                },
#                            "seuil_11": {
#                                "@type": "Parameter",
#                                "description": "Indice majoré plafond",
#                                "format": "integer",
#                                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 468}],
#                                },
#                            },
#                        },
#                    },
#                },
#            },
#        }
#    reference_legislation_json_copy['children']['plfr2014'] = plfr2014_legislation_subtree
#    reference_legislation_json_copy['children']['plfrss2014'] = plfrss2014_legislation_subtree        
#        