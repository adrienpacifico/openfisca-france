# -*- coding: utf-8 -*-

from __future__ import division

from openfisca_core import formulas, reforms
from ..model.base import *
from ..model.prelevements_obligatoires.impot_revenu import ir


# What if the reform was applied the year before it should

def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf2016',
        name = u'Projet de Loi de Finances 2016 appliquée aux revenus 2014',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Décote IR 2016 appliquée en 2015 sur revenus 2014"
        reference = ir.decote

        @dated_function(start = date(2014, 1, 1), stop = date(2014, 12, 31))
        def function_2014(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period)
            plf = simulation.legislation_at(period.start).plf2016

            decote_celib = (ir_plaf_qf < plf.decote_seuil_celib) * (plf.decote_seuil_celib - .75 * ir_plaf_qf)
            decote_couple = (ir_plaf_qf < plf.decote_seuil_couple) * (plf.decote_seuil_couple - .75 * ir_plaf_qf)
            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform


def modify_legislation_json(reference_legislation_json_copy):
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2016 sur revenus 2014",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 1165}],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2014-01-01', 'stop': u'2014-12-31', 'value': 1920}],
                },
            },
        }
    reference_legislation_json_copy['children']['plf2016'] = reform_legislation_subtree
    return reference_legislation_json_copy


# Counterfactual ie business as usual

def build_counterfactual_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'plf2016_counterfactual',
        name = u'Contrefactuel du PLF 2016 sur les revenus 2015',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class decote(formulas.DatedFormulaColumn):
        label = u"Décote IR 2015 appliquée sur revenus 2015 (contrefactuel)"
        reference = ir.decote

        @dated_function(start = date(2015, 1, 1))
        def function_2015__(self, simulation, period):
            period = period.start.offset('first-of', 'year').period('year')
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period)
            plf2016 = simulation.legislation_at(period.start).plf2016_conterfactual
            decote_seuil_celib = plf2016.decote_seuil_celib
            decote_seuil_couple = plf2016.decote_seuil_couple

            decote_celib = (ir_plaf_qf < decote_seuil_celib) * (decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < decote_seuil_couple) * (decote_seuil_couple - ir_plaf_qf)

            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple

    reform = Reform()
    reform.modify_legislation_json(modifier_function = counterfactual_modify_legislation_json)
    return reform


def counterfactual_modify_legislation_json(reference_legislation_json_copy):
    # TODO: inflater les paramètres de la décote le barème de l'IR
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2016 sur revenus 2015",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2015-01-01', 'stop': u'2015-12-31', 'value': 1135}],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [{'start': u'2015-01-01', 'stop': u'2015-12-31', 'value': 1870}],
                },
            },
        }
    reference_legislation_json_copy['children']['plf2016_conterfactual'] = reform_legislation_subtree
    return reference_legislation_json_copy

    # WIP : Nouveaux parametres à actualiser :
    # 1° Le 1 est remplacé par les dispositions suivantes :
    # (3) « 1. L'impôt est calculé en appliquant à la fraction de chaque part de revenu qui excède 9 700 € le taux de :
    # (4) « 14 % pour la fraction supérieure à 9 700 € et inférieure ou égale à 26 791 € ;
    # (5) « 30 % pour la fraction supérieure à 26 791 € et inférieure ou égale à 71 826 € ;
    # (6) « 41 % pour la fraction supérieure à 71 826 € et inférieure ou égale à 152 108 € ;
    # (7) « 45 % pour la fraction supérieure à 152 108 €. » ;
    # (8) 2° Au 2 :
    # (9) a) Au premier alinéa, le montant : « 1 508 € » est remplacé par le montant : « 1 510 € » ;
    # (10) b) Au deuxième alinéa, le montant : « 3 558 € » est remplacé par le montant : « 3 562 € » ;
    # (11) c) Au troisième alinéa, le montant : « 901 € » est remplacé par le montant : « 902 € » ;
    # (12) d) Au quatrième alinéa, le montant : « 1 504 € » est remplacé par le montant : « 1 506 € » ;
    # (13) e) Au dernier alinéa, le montant : « 1 680 € » est remplacé par le montant : « 1 682 € » ;
    # (14) 3° Au 4, les mots : « 1 135 € et » sont remplacés par les mots : « 1 165 € et les trois quarts de » et
    # les mots : « 1 870 €
    # et » sont remplacés par les mots : « 1 920 € et les trois quarts de ».
    # (15) II. – Au second alinéa de l'article 196 B du même code, le montant : « 5 726 € » est remplacé par le
    # montant : « 5 732 € ».
