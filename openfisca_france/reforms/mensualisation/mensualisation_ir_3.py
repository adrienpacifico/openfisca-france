# -*- coding: utf-8 -*-

from __future__ import division

from numpy import (datetime64, logical_and as and_, logical_not as not_, logical_or as or_, logical_xor as xor_,
    maximum as max_, minimum as min_, round)
from openfisca_core import columns, formulas, reforms

from ... import entities
from ...model.base import QUIFOY
from ...model.prelevements_obligatoires.impot_revenu import ir
from ...model.base import *

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

            return period, salaire_imposable*12 #+ cho


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
            abatfor = round(min_(max_(abatpro.taux * rev_sal, abattement_minimum), abatpro.max))
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

            return period, 1 * nbptr * bareme.calc(rni / nbptr)
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

    class ir_plaf_qf(Reform.Variable):
        label = u"ir_plaf_qf"
        reference = ir.ir_plaf_qf

        def function(self, simulation, period):
            '''
            Impôt après plafonnement du quotient familial et réduction complémentaire
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut', period)
            ir_ss_qf = simulation.calculate('ir_ss_qf', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year)
            nb_pac = simulation.calculate('nb_pac', period.this_year)
            nbptr = simulation.calculate('nbptr', period.this_year)
            marpac = simulation.calculate('marpac', period)
            veuf = simulation.calculate('veuf', period)
            jveuf = simulation.calculate('jveuf', period)
            celdiv = simulation.calculate('celdiv', period)
            caseE = simulation.calculate('caseE', period.this_year)
            caseF = simulation.calculate('caseF', period.this_year)
            caseG = simulation.calculate('caseG', period.this_year)
            caseH = simulation.calculate('caseH', period.this_year)
            caseK = simulation.calculate('caseK', period.this_year)
            caseN = simulation.calculate('caseN', period.this_year)
            caseP = simulation.calculate('caseP', period.this_year)
            caseS = simulation.calculate('caseS', period.this_year)
            caseT = simulation.calculate('caseT', period.this_year)
            caseW = simulation.calculate('caseW', period.this_year)
            nbF = simulation.calculate('nbF', period)
            nbG = simulation.calculate('nbG', period)
            nbH = simulation.calculate('nbH', period)
            nbI = simulation.calculate('nbI', period)
            nbR = simulation.calculate('nbR', period)
            plafond_qf = simulation.legislation_at(period.start).ir.plafond_qf

            A = ir_ss_qf
            I = ir_brut

            aa0 = (nbptr - nb_adult) * 2  # nombre de demi part excédant nbadult
            # on dirait que les impôts font une erreur sur aa1 (je suis obligé de
            # diviser par 2)
            aa1 = min_((nbptr - 1) * 2, 2) / 2  # deux première demi part excédants une part
            aa2 = max_((nbptr - 2) * 2, 0)  # nombre de demi part restantes
            # celdiv parents isolés
            condition61 = celdiv & caseT
            B1 = plafond_qf.celib_enf * aa1 + plafond_qf.marpac * aa2
            # tous les autres
            B2 = plafond_qf.marpac * aa0  # si autre
            # celdiv, veufs (non jveuf) vivants seuls et autres conditions
            # TODO: année en dur... pour caseH
            condition63 = (celdiv | (veuf & not_(jveuf))) & not_(caseN) & (nb_pac == 0) & (caseK | caseE) & (caseH < 1981)
            B3 = plafond_qf.celib

            B = B1 * condition61 + \
                B2 * (not_(condition61 | condition63)) + \
                B3 * (condition63 & not_(condition61))
            C = max_(0, A - B)
            # Impôt après plafonnement
            IP0 = max_(I, C)

            # 6.2 réduction d'impôt pratiquée sur l'impot après plafonnement et le cas particulier des DOM
            # pas de réduction complémentaire
            condition62a = (I >= C)
            # réduction complémentaire
            condition62b = (I < C)
            # celdiv veuf
            condition62caa0 = (celdiv | (veuf & not_(jveuf)))
            condition62caa1 = (nb_pac == 0) & (caseP | caseG | caseF | caseW)
            condition62caa2 = caseP & ((nbF - nbG > 0) | (nbH - nbI > 0))
            condition62caa3 = not_(caseN) & (caseE | caseK) & (caseH >= 1981)
            condition62caa = condition62caa0 & (condition62caa1 | condition62caa2 | condition62caa3)
            # marié pacs
            condition62cab = (marpac | jveuf) & caseS & not_(caseP | caseF)
            condition62ca = (condition62caa | condition62cab)

            # plus de 590 euros si on a des plus de
            condition62cb = ((nbG + nbR + nbI) > 0) | caseP | caseF
            D = plafond_qf.reduc_postplafond * (condition62ca + ~condition62ca * condition62cb * (
                1 * caseP + 1 * caseF + nbG + nbR + nbI / 2))

            E = max_(0, A - I - B)
            Fo = D * (D <= E) + E * (E < D)
            IP1 = IP0 - Fo

            # TODO: 6.3 Cas particulier: Contribuables domiciliés dans les DOM.
            # conditionGuadMarReu =
            # conditionGuyane=
            # conitionDOM = conditionGuadMarReu | conditionGuyane
            # postplafGuadMarReu = 5100
            # postplafGuyane = 6700
            # IP2 = IP1 - conditionGuadMarReu*min( postplafGuadMarReu,.3*IP1)  - conditionGuyane*min(postplafGuyane,.4*IP1)

            # Récapitulatif

            return period, condition62a * IP0 + condition62b * IP1  # IP2 si DOM

    class ip_net_mensuel(Reform.Variable):
        reference = ir.ip_net
        label = u"ip_net"

        def function(self, simulation, period):
            '''
            irpp après décote
            '''
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            cncn_info_holder = simulation.compute('cncn_info', period)
            decote = simulation.calculate('decote', period)
            taux = simulation.legislation_at(period.start).ir.rpns.taux16

            return period, (max_(0, ir_plaf_qf + self.sum_by_entity(cncn_info_holder) * taux - decote))/12




    class decote(Reform.DatedVariable): #Ne marche pas je modifie dans en dur...
        reference = ir.decote
        label = u"décote"

        @dated_function(start = date(2001, 1, 1), stop = date(2013, 12, 31))
        def function_2001_2013(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            decote = simulation.legislation_at(period.start).ir.decote

            return period, (ir_plaf_qf < decote.seuil) * (decote.seuil - ir_plaf_qf) * 0.5

        @dated_function(start = date(2014, 1, 1))
        def function_2014__(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year)
            decote_seuil_celib = simulation.legislation_at(period.start).ir.decote.seuil_celib
            decote_seuil_couple = simulation.legislation_at(period.start).ir.decote.seuil_couple
            decote_celib = (ir_plaf_qf < decote_seuil_celib) * (decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < decote_seuil_couple) * (decote_seuil_couple - ir_plaf_qf)

            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple

#FIN

    class iaidrdi(Reform.Variable):
        reference= ir.iaidrdi
        label = u"iaidrdi"

        def function(self, simulation, period):
            '''
            Impôt après imputation des réductions d'impôt
            '''
            period = period.this_year
            ip_net = simulation.calculate_add('ip_net_mensuel', period)
           # reductions = simulation.calculate('reductions', period)

            return period, ip_net #- reductions

    reform = Reform()
    return reform
