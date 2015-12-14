# -*- coding: utf-8 -*-

from __future__ import division

from numpy import (datetime64, logical_and as and_, logical_not as not_, logical_or as or_, logical_xor as xor_,
    maximum as max_, minimum as min_, round)
from openfisca_core import columns, formulas, reforms

from ... import entities
from ...model.base import QUIFOY
from ...model.prelevements_obligatoires.impot_revenu import ir


#
# from openfisca_utils import make_ready_to_use_scenario
# scenario = make_ready_to_use_scenario.make_couple_with_child_scenario(year = 2014)
# simulation = scenario.new_simulation()
# simulation.calculate("tspr")
# simulation.calculate("tspr", "2014-01-01")



### Technique, faire d'amont en aval sur une simulation simple inputant du salaire_de_base
## MP pour month proof

def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'allocations_familiales_imposables',
        name = u"Mensualisation de l'ir",
        reference = tax_benefit_system,
        )


    class rev_sal(Reform.Variable):
        label = u"Nouveau revenu brut global intégrant les allocations familiales"
        reference = ir.rev_sal
        def function(self, simulation, period):
            period = period.this_month
            salaire_imposable =  simulation.calculate_add('salaire_imposable', period)
 #           cho = simulation.calculate('cho', period) #TODO: gérer le chomage

            return period, salaire_imposable #+ cho


    class salcho_imp(Reform.Variable):
        label = u"Salaires et chômage imposables après abattements"
        reference = ir.salcho_imp

        def function(self, simulation, period):
            period = period.this_month
            rev_sal = simulation.calculate('rev_sal', period)
            chomeur_longue_duree = simulation.calculate('chomeur_longue_duree', period) #MP
            frais_reels = simulation.calculate('frais_reels', period) #MP
            abatpro = simulation.legislation_at(period.start).ir.tspr.abatpro #TODO: check if need to multiply threshold

            abattement_minimum = abatpro.min * not_(chomeur_longue_duree) + abatpro.min2 * chomeur_longue_duree
            abatfor = round(min_(max_(abatpro.taux * rev_sal, abattement_minimum/12), abatpro.max/12))
            return period, (frais_reels > abatfor) * (rev_sal - frais_reels) + (frais_reels <= abatfor) * max_(0, rev_sal - abatfor)

    class sal_pen_net(Reform.Variable):
        label = u"Salaires et chômage imposables après abattements"
        reference = ir.rev_sal

        def function(self, simulation, period):
            period = period.this_month
            salcho_imp = simulation.calculate('salcho_imp', period)  #NMP
            #pen_net = simulation.calculate('pen_net', period)    #NMP #TODO: mensualize pen_net
            abat_sal_pen = simulation.calculate('abat_sal_pen', period) #MP

            return period, salcho_imp #+ pen_net - abat_sal_pen

    class tspr(Reform.Variable):

        label = u"Traitements salaires pensions et rentes individuelles"
        reference = ir.tspr

        def function(self, simulation, period):
            period = period.this_month
            sal_pen_net = simulation.calculate('sal_pen_net', period)
            # Quand tspr est calculé sur une année glissante, rto_net_declarant1 est calculé sur l'année légale
            # correspondante.
            #rto_net_declarant1 = simulation.calculate('rto_net_declarant1', period.offset('first-of')) #TODO: Mensualiser

            return period, sal_pen_net #+ rto_net_declarant1

    class rev_cat_tspr(Reform.Variable):
        reference = ir.rev_cat_tspr
        label = u"Revenu catégoriel - Traitements, salaires, pensions et rentes"

        def function(self, simulation, period):
            period = period.this_month
            tspr_holder = simulation.compute('tspr', period)
            #indu_plaf_abat_pen = simulation.calculate('indu_plaf_abat_pen', period) #NMP

            tspr = self.sum_by_entity(tspr_holder)

            return period, tspr #+ indu_plaf_abat_pen


    class rev_cat(Reform.Variable):
        reference = ir.rev_cat
        label = u"Revenu catégoriel "
        def function(self, simulation, period):
            '''
            Revenus Categoriels
            '''
            period = period.this_month
            rev_cat_tspr = simulation.calculate('rev_cat_tspr', period)
            #rev_cat_rvcm = simulation.calculate('rev_cat_rvcm', period)
            #rev_cat_rfon = simulation.calculate('rev_cat_rfon', period)
            #rev_cat_rpns = simulation.calculate('rev_cat_rpns', period)
            #rev_cat_pv = simulation.calculate('rev_cat_pv', period)

            return period, rev_cat_tspr #+ rev_cat_rvcm + rev_cat_rfon + rev_cat_rpns + rev_cat_pv

    class rbg(Reform.Variable):
        reference = ir.rbg
        label = "revenu brut global"
        def function(self, simulation, period):
            '''Revenu brut global
            '''
            period = period.this_month
            rev_cat = simulation.calculate('rev_cat', period)
            deficit_ante = simulation.calculate('deficit_ante', period.this_year)/12
           # f6gh = simulation.calculate('f6gh', period)
            #nbic_impm_holder = simulation.compute('nbic_impm', period)
            #nacc_pvce_holder = simulation.compute('nacc_pvce', period)
            cga = simulation.legislation_at(period.start).ir.rpns.cga_taux2

            # (Total 17)
            # sans les revenus au quotient
            #nacc_pvce = self.sum_by_entity(nacc_pvce_holder)
            return period, max_(0,
                        rev_cat )#+ f6gh + (self.sum_by_entity(nbic_impm_holder) + nacc_pvce) * (1 + cga) - deficit_ante)


    # class csg_deduc(Reform.Variable):
    #     reference = ir.csg_deduc
    #     def function(self, simulation, period):
    #         ''' Revenu net global (total 20) '''
    #         period = period.this_month
    #         rbg = simulation.calculate('rbg', period)
    #         csg_deduc = simulation.calculate('csg_deduc', period)
    #         charges_deduc = simulation.calculate('charges_deduc', period)
    #
    #         return period, max_(0, rbg - csg_deduc - charges_deduc)

    class rng(Reform.Variable):
        reference = ir.rng
        label = 'rng'
        def function(self, simulation, period):
            ''' Revenu net global (total 20) '''
            period = period.this_month
            rbg = simulation.calculate('rbg', period)
          #  csg_deduc = simulation.calculate('csg_deduc', period)
          #  charges_deduc = simulation.calculate('charges_deduc', period)

            return period, max_(0, rbg )#- csg_deduc - charges_deduc)

    class rni(Reform.Variable):
        reference = ir.rni
        label = 'revenu net imposable'

        def function(self, simulation, period):
            ''' Revenu net imposable ou déficit à reporter'''
            period = period.this_month
            rng = simulation.calculate('rng', period)
            #abat_spe = simulation.calculate('abat_spe', period)

            return period, rng #- abat_spe


    class ir_brut(Reform.Variable):
        reference = ir.rni
        label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"

        def function(self, simulation, period):
            #period = period.start.offset('first-of', 'month').period('year')
            period = period.this_month
            nbptr = simulation.calculate('nbptr', period.this_year) #TODO : change to monthly ?
           # taux_effectif = simulation.calculate('taux_effectif', period)
            rni = simulation.calculate('rni', period)
            bareme = simulation.legislation_at(period.start).ir.bareme

            return period, nbptr * ((bareme.calc(rni*12 / nbptr))/12)
            #(taux_effectif == 0) * nbptr * ((bareme.calc(rni*12 / nbptr))/12) #+ taux_effectif * rni



    class ir_ss_qf(Reform.Variable):
        reference = ir.ir_ss_qf
        label = u"ir_ss_qf"

        def function(self, simulation, period):
            '''
            Impôt sans quotient familial
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut', period)
            rni = simulation.calculate('rni', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year) #TODO: think how to mensualize
            bareme = simulation.legislation_at(period.start).ir.bareme

            A = bareme.calc(rni / nb_adult)
            return period, nb_adult * A


    reform = Reform()
    return reform