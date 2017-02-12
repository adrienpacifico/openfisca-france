# -*- coding: utf-8 -*-

from __future__ import division
import numpy as np
from numpy import (datetime64, logical_and as and_, logical_not as not_, logical_or as or_, logical_xor as xor_,
    maximum as max_, minimum as min_, round)
from openfisca_core import columns, formulas, reforms
from openfisca_core import simulations, periods

from ... import entities
from ...model.base import QUIFOY
from ...model.prelevements_obligatoires.impot_revenu import ir
from ...model.prestations import minima_sociaux
from ...model import mesures
from ... import model
from ...model.base import *

from ...model.prestations.minima_sociaux import rsa as rsa_ref


## Mensualisaton ou on rend indépendante toutes les variables mensuelles (pas d'é
##crasement des références


## On met tout ce qui semble devoir être taxé en annuel en calculate_add_divide sur l'année.














### Technique, faire d'amont en aval sur une simulation simple inputant du salaire_de_base
## MP pour month proof

##TODO: Finalement plus logique de bypasser l'ir avec un ir mensuel, puis de mensualiser les variables de mesures.py en créant revdisp_mensuel etc





def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'mensualisation_impot_revenu',
        name = u"Mensualisation de l'ir",
        reference = tax_benefit_system,
        )





    ####Neutralisations pour plus tard
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['abat_spe']))
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['ars']))
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['aeeh']))
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['rmi']))


##### Dans l'ordre du revenu rev_sal à l'ir
    class rev_sal_mensuel_times_12(Reform.Variable):
        reference = ir.rev_sal
        label = u"Nouveau revenu brut global intégrant les allocations familiales"
        def function(self, simulation, period):
            period = period.this_month
            salaire_imposable_mensuel =  simulation.calculate('salaire_imposable', period)
            cho = simulation.calculate('chomage_imposable', period)

            return period, salaire_imposable_mensuel*12 + cho *12


    class salcho_imp_mensuel_times_12(Reform.Variable):
        label = u"Salaires et chômage imposables après abattements"
        reference = ir.salcho_imp

        def function(self, simulation, period):
            period = period.this_month
            rev_sal = simulation.calculate('rev_sal_mensuel_times_12', period)
            chomeur_longue_duree = simulation.calculate('chomeur_longue_duree', period.this_year) #MP #TODO : mensualiser ?
            frais_reels = simulation.calculate('frais_reels', period.this_year) #MP
            abatpro = simulation.legislation_at(period.start).ir.tspr.abatpro #TODO: check if need to multiply threshold---> No because already multiplied by 12 !

            abattement_minimum = abatpro.min * not_(chomeur_longue_duree) + abatpro.min2 * chomeur_longue_duree
            abatfor = round(min_(max_(abatpro.taux * rev_sal, abattement_minimum), abatpro.max))

            return period, (frais_reels > abatfor) * (rev_sal - frais_reels) + (frais_reels <= abatfor) * max_(0, rev_sal - abatfor)





    class rev_pen_mensuel_times_12(Reform.Variable):
        label = u"Revenu imposé comme des pensions (retraites, pensions alimentaires, etc.)"
        reference = ir.rev_pen

        def function(self, simulation, period):
            period = period.this_month
            pensions_alimentaires_percues = simulation.calculate_add('pensions_alimentaires_percues', period)
            pensions_alimentaires_percues_decl = simulation.calculate_add('pensions_alimentaires_percues_decl', period) #TODO : mensualiser les pensions si possible
            retraite_imposable = simulation.calculate('retraite_imposable', period.this_month)

            return period, pensions_alimentaires_percues * pensions_alimentaires_percues_decl + retraite_imposable * 12


    class pen_net_mensuel_times_12(Reform.Variable):
        label = u"Pensions après abattements"
        reference = ir.pen_net

        def function(self, simulation, period):
            period = period.this_month
            rev_pen = simulation.calculate('rev_pen_mensuel_times_12', period.this_month)
            abatpen = simulation.legislation_at(period.start).ir.tspr.abatpen

            #    TODO: problème car les pensions sont majorées au niveau du foyer
        #    d11 = ( AS + BS + CS + DS + ES +
        #            AO + BO + CO + DO + EO )
        #    penv2 = (d11-f11> abatpen.max)*(penv + (d11-f11-abatpen.max)) + (d11-f11<= abatpen.max)*penv
        #    Plus d'abatement de 20% en 2006
            return period, max_(0, rev_pen - round(max_(abatpen.taux * rev_pen , abatpen.min)))





    class sal_pen_net_mensuel_times_12(Reform.Variable):
        reference = ir.sal_pen_net
        label = u"Salaires et chômage imposables après abattements"

        def function(self, simulation, period):
            period = period.this_month
            salcho_imp = simulation.calculate('salcho_imp_mensuel_times_12', period)
            pen_net = simulation.calculate('pen_net_mensuel_times_12', period)
            abat_sal_pen = simulation.calculate('abat_sal_pen', period)

            return period, salcho_imp + pen_net - abat_sal_pen











        # def function(self, simulation, period):
        #     period = period.this_month
        #     salcho_imp = simulation.calculate('salcho_imp_mensuel_times_12', period)  #NMP
        #    # pen_net = simulation.calculate('pen_net', period.this_year)    #NMP #TODO: mensualize pen_net --> pas l'info en mensuel sauf si retraité
        #
        #
        #     ##### Tweak pour avoir les retraites imposables, on prend les pen_net,
        #     #####  on soustrait les retraites imposable, on rajoute la retraite imposable mensuelle.
        #
        #     retraite_imposable = simulation.calculate('retraite_imposable', period) * 12
        #     pen_net = simulation.calculate('pen_net', period.this_year) \
        #               - simulation.calculate_add('retraite_imposable', period.this_year)  # Vu qu'on est en *12 sur la retraite imposable, on a comme
        #                                                                                   # si on repartissait le reste des pensions chaque mois sur l'année !
        #     pen_net = simulation.calculate('pen_net', period.this_year) + retraite_imposable  #on rajoute la retraite du mois
        #
        #     #####
        #
        #     abat_sal_pen = simulation.calculate('abat_sal_pen', period.this_year) #MP # TODO : mensualiser en ajoutant la formule et en modifiant le calcul, pour l'instant on prend le résultat annuel en le mensualisant


            return period, salcho_imp + pen_net - abat_sal_pen

    class tspr_mensuel_times_12(Reform.Variable):
        reference = ir.tspr
        label = u"Traitements salaires pensions et rentes individuelles"

        def function(self, simulation, period):
            period = period.this_month
            sal_pen_net = simulation.calculate('sal_pen_net_mensuel_times_12', period)
            # Quand tspr est calculé sur une année glissante, rto_net_declarant1 est calculé sur l'année légale
            # correspondante.
            rto_net_declarant1 = simulation.calculate('rto_net_declarant1', period.this_year) #period.offset('first-of')) #TODO: Mensualiser, Done ?

            return period, sal_pen_net + rto_net_declarant1

    class rev_cat_tspr_mensuel_times_12(Reform.Variable):
        reference = ir.rev_cat_tspr
        label = u"Revenu catégoriel - Traitements, salaires, pensions et rentes"

        def function(self, simulation, period):
            period = period.this_month
            tspr_holder = simulation.compute('tspr_mensuel_times_12', period)
            indu_plaf_abat_pen = simulation.calculate('indu_plaf_abat_pen', period.this_year) #NMP #TODO : check

            tspr = self.sum_by_entity(tspr_holder)

            return period, tspr + indu_plaf_abat_pen


    class rev_cat_mensuel_times_12(Reform.Variable):
        reference = ir.rev_cat
        label = u"Revenu catégoriel "
        def function(self, simulation, period):
            '''
            Revenus Categoriels
            '''
            period = period.this_month
            rev_cat_tspr = simulation.calculate('rev_cat_tspr_mensuel_times_12', period)
            rev_cat_rvcm = simulation.calculate('rev_cat_rvcm', period.this_year)
            rev_cat_rfon = simulation.calculate('rev_cat_rfon', period.this_year)  #TODO : Bien checker http://bofip.impots.gouv.fr/bofip/6448-PGP , pour l'instant mis en annuel à l'arrache
            rev_cat_rpns = simulation.calculate('rev_cat_rpns', period.this_year)
            rev_cat_pv = simulation.calculate('rev_cat_pv', period.this_year)

            return period, rev_cat_tspr + rev_cat_rvcm + rev_cat_rfon + rev_cat_rpns + rev_cat_pv

    class rbg_mensuel_times_12(Reform.Variable):
        reference = ir.rbg
        label = "revenu brut global"
        def function(self, simulation, period):
            '''Revenu brut global
            '''
            period = period.this_month
            rev_cat = simulation.calculate('rev_cat_mensuel_times_12', period)
            deficit_ante = simulation.calculate('deficit_ante', period.this_year) # TODO : check
            f6gh = simulation.calculate('f6gh', period.this_year) # TODO : check
            nbic_impm_holder = simulation.compute('nbic_impm', period.this_year) # TODO : check
            nacc_pvce_holder = simulation.compute('nacc_pvce', period.this_year)
            cga = simulation.legislation_at(period.start).ir.rpns.cga_taux2

            # (Total 17)
            # sans les revenus au quotient
            nacc_pvce = self.sum_by_entity(nacc_pvce_holder)
            return period, max_(0,rev_cat ) \
                + f6gh + (self.sum_by_entity(nbic_impm_holder) + nacc_pvce) * (1 + cga) - deficit_ante


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

    class rng_mensuel_times_12(Reform.Variable):
        reference = ir.rng
        label = u"Revenu net global"
        url = "http://impotsurlerevenu.org/definitions/114-revenu-net-global.php"

        def function(self, simulation, period):
            ''' Revenu net global (total 20) '''
            period = period.this_month
            rbg = simulation.calculate('rbg_mensuel_times_12', period)
            csg_deduc = simulation.calculate('csg_deduc', period.this_year) #TODO : modify properly --> concerns only revenu du patrimoine, reste annuel
            charges_deduc = simulation.calculate('charges_deduc', period.this_year) #TODO : modify properly

            return period, max_(0, rbg - csg_deduc - charges_deduc)

    class rni_mensuel_times_12(Reform.Variable):
        reference = ir.rni
        label = 'revenu net imposable'

        def function(self, simulation, period):
            ''' Revenu net imposable ou déficit à reporter'''
            period = period.this_month
            rng = simulation.calculate('rng_mensuel_times_12', period)
            abat_spe = simulation.calculate('abat_spe', period.this_year)

            return period, rng - abat_spe


    class ir_brut_mensuel_times_12(Reform.Variable):
        reference = ir.ir_brut
        label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"

        def function(self, simulation, period):
            #period = period.start.offset('first-of', 'month').period('year')
            period = period.this_month
            nbptr = simulation.calculate('nbptr', period.this_year) #TODO : change to monthly ?
            taux_effectif = simulation.calculate('taux_effectif', period.this_year) #TODO : check
            rni = simulation.calculate('rni_mensuel_times_12', period)
            bareme = simulation.legislation_at(period.start).ir.bareme

            return period, (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni #TODO : check fait augmenter le % de mensuel inférieur à l'annuel de 2%
            #return period, 1 * nbptr * bareme.calc(rni / nbptr)

            ########
            #(taux_effectif == 0) * nbptr * ((bareme.calc(rni*12 / nbptr))/12) #+ taux_effectif * rni



    class ir_ss_qf_mensuel_times_12(Reform.Variable):
        reference = ir.ir_ss_qf
        label = u"ir_ss_qf"

        def function(self, simulation, period):
            '''
            Impôt sans quotient familial
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut_mensuel_times_12', period)
            rni = simulation.calculate('rni_mensuel_times_12', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year) #TODO: think how to mensualize
            bareme = simulation.legislation_at(period.start).ir.bareme

            A = bareme.calc(rni / nb_adult)
            return period, nb_adult * A

    class ir_plaf_qf_mensuel_times_12(Reform.Variable):
        label = u"ir_plaf_qf"
        reference = ir.ir_plaf_qf

        def function(self, simulation, period):
            '''
            Impôt après plafonnement du quotient familial et réduction complémentaire
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut_mensuel_times_12', period)
            ir_ss_qf = simulation.calculate('ir_ss_qf_mensuel_times_12', period)
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


    class decote_mensuel_times_12(Reform.DatedVariable): #Ne marche pas je modifie dans en dur...
        reference = ir.decote
        label = u"décote"

        @dated_function(start = date(2001, 1, 1), stop = date(2013, 12, 31))
        def function_2001_2013(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_mensuel_times_12', period)
            decote = simulation.legislation_at(period.start).ir.decote

            return period, (ir_plaf_qf < decote.seuil) * (decote.seuil - ir_plaf_qf) * 0.5

        @dated_function(start = date(2014, 1, 1))
        def function_2014__(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_mensuel_times_12', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year)
            decote_seuil_celib = simulation.legislation_at(period.start).ir.decote.seuil_celib
            decote_seuil_couple = simulation.legislation_at(period.start).ir.decote.seuil_couple
            decote_celib = (ir_plaf_qf < decote_seuil_celib) * (decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < decote_seuil_couple) * (decote_seuil_couple - ir_plaf_qf)

            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple

    class decote_gain_fiscal_mensuel_times_12(Reform.Variable): #Ne marche pas je modifie dans en dur...
        reference = ir.decote_gain_fiscal
        label = u"décote_gain_fiscal"

        def function(self, simulation, period):
            '''
            Renvoie le gain fiscal du à la décote
            '''
            period = period.this_month
            decote = simulation.calculate('decote_mensuel_times_12', period)
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_mensuel_times_12', period)

            return period, min_(decote, ir_plaf_qf)

    class ip_net_mensuel(Reform.Variable):
        reference = ir.ip_net
        label = u"ip_net"

        def function(self, simulation, period):
            '''
            irpp après décote
            '''
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_mensuel_times_12', period)
            cncn_info_holder = simulation.compute('cncn_info', period)
            decote = simulation.calculate('decote_mensuel_times_12', period)
            taux = simulation.legislation_at(period.start).ir.rpns.taux16

            return period, (max_(0, ir_plaf_qf + self.sum_by_entity(cncn_info_holder) * taux - decote))/12 # Todo : divise ici par 12




    #
    # class rfr_mensuel(Reform.Variable):  #utile pour la base ressource, que si on veut mensualiser le rsa
    #     reference = ir.rfr
    #     label = u"Revenu fiscal de référence"
    #
    #     def function(self, simulation, period):
    #         '''
    #         Revenu fiscal de référence
    #         f3vg -> rev_cat_pv -> ... -> rni
    #         '''
    #         period = period.this_month
    #         rni = simulation.calculate('rni_mensuel_times_12', period)
    #         f3va_holder = simulation.compute('f3va', period.this_year)
    #         f3vi_holder = simulation.compute('f3vi', period.this_year)
    #         rfr_cd = simulation.calculate('rfr_cd', period.this_year)
    #         rfr_rvcm = simulation.calculate('rfr_rvcm', period.this_year)
    #         rpns_exon_holder = simulation.compute('rpns_exon', period.this_year)
    #         rpns_pvce_holder = simulation.compute('rpns_pvce', period.this_year)
    #         rev_cap_lib = simulation.calculate_add('rev_cap_lib', period.this_year)
    #         f3vz = simulation.calculate('f3vz', period.this_year)
    #         microentreprise = simulation.calculate('microentreprise', period.this_year)
    #
    #         f3va = self.sum_by_entity(f3va_holder)
    #         f3vi = self.sum_by_entity(f3vi_holder)
    #         rpns_exon = self.sum_by_entity(rpns_exon_holder)
    #         rpns_pvce = self.sum_by_entity(rpns_pvce_holder)
    #         return period, (max_(0, rni) + rfr_cd + rfr_rvcm + rev_cap_lib + f3vi + rpns_exon + rpns_pvce + f3va +
    #                 f3vz + microentreprise)




    class iai_mensuel(Reform.Variable):
        reference = ir.iai
        label = u"Impôt avant imputations"
        url = "http://forum-juridique.net-iris.fr/finances-fiscalite-assurance/43963-declaration-impots.html"

        def function(self, simulation, period):
            '''
            impôt avant imputation de l'irpp
            '''
            period = period.this_month
            iaidrdi = simulation.calculate('iaidrdi_mensuel', period)
            plus_values = simulation.calculate('plus_values', period.this_year)/12
            cont_rev_loc = simulation.calculate('cont_rev_loc', period.this_year)/12
            teicaa = simulation.calculate('teicaa', period.this_year)/12

            return period, iaidrdi + plus_values + cont_rev_loc + teicaa




#######FIN


    class irpp_mensuel(Reform.Variable):
        column = FloatCol(default = 0)
        reference = ir.irpp
        label = u"Impôt sur le revenu des personnes physiques"
        url = "http://www.impots.gouv.fr/portal/dgi/public/particuliers.impot?pageId=part_impot_revenu&espId=1&impot=IR&sfid=50"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_month
            iai = simulation.calculate('iai_mensuel', period)
            credits_impot = simulation.calculate('credits_impot', period.this_year)/12
            cehr = simulation.calculate('cehr', period.this_year)/12 #TODO : mensualiser
            P = simulation.legislation_at(period.start).ir.recouvrement

            pre_result = iai - credits_impot + cehr
            return period, -pre_result ### Suppression des seuils de non recouvrements

                #
                #    # (
                # (iai > P.seuil) * ( #Cas si l'impot est en dessus du seuil de recouvrement
                #     (pre_result < P.min/12) * (pre_result > 0) * iai * 0 +
                #     ((pre_result <= 0) + (pre_result >= P.min/12)) * (- pre_result)
                #     ) +
                # (iai <= P.seuil) * ( #Cas si l'impot est en dessous du seuil de recouvrement
                #     (pre_result < 0) * (-pre_result) + (pre_result >= 0) * 0 * iai) #on rend le crédit d'impot
                # )


    class lambda_compensation(Reform.Variable):
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"Impôt sur le revenu des personnes physiques"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_year
            impot_mensuel = -simulation.calculate_add("irpp_mensuel", period)
            impot_annuel = -simulation.calculate("irpp", period)
            lambda_compensation = ((impot_mensuel*12)/impot_annuel) - 12  #En fait impot mensuel est égal à G(y_T)/T il faut monter plus haut pour prendre le lambda

            #lambda_compensation = ((impot_annuel == 0) & (impot_mensuel == 0)) * 0 + ~((impot_annuel == 0) & (impot_mensuel == 0)) * lambda_compensation
            import numpy as np
            lambda_compensation = (impot_annuel == 0) * 0 + ~(impot_annuel == 0) * lambda_compensation #empèche d'avoir des + l'infiny

            #import numpy as np
            #assert np.all(np.isfinite(lambda_compensation))
            ## traiter le cas ou irpp annuel = 0

            return period, lambda_compensation
            #return period, (impot_mensuel/impot_annuel)# - 12  #réfléchir à ça plutôt que l'autre lambda


    class compensated_irpp_mensuel(Reform.Variable):
        column = FloatCol(default = 0)
        entity_class = FoyersFiscaux
        label = u"Impôt sur le revenu des personnes physiques"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_month

            impot_mensuel_times_12 = simulation.calculate("irpp_mensuel", period)*12
            lambda_compensation = simulation.calculate("lambda_compensation", period.this_year)

            compensated_irpp = impot_mensuel_times_12/(12 + lambda_compensation)
            compensated_irpp = (simulation.calculate("irpp", period.this_year) == 0) * 0 + \
                ~(simulation.calculate("irpp", period.this_year) == 0) * np.nan_to_num(compensated_irpp)
            compensated_irpp = (
                            (simulation.calculate_add("irpp_mensuel", period.this_year) == 0) * #Condition
                            (simulation.calculate("irpp", period.this_year)/12) # on répartit sur l'année
                        ) + ~(simulation.calculate_add("irpp_mensuel", period.this_year) == 0) * compensated_irpp #condition opposée

            #print compensated_irpp[[4,743]]
            return period, compensated_irpp





    class impo_mensuel(Reform.Variable):
        reference = mesures.impo
        label = u"Impôts directs"
        url = "http://fr.wikipedia.org/wiki/Imp%C3%B4t_direct"

        def function(self, simulation, period):
            '''
            Impôts directs
            '''
            period = period.this_month
            irpp_holder = simulation.compute('irpp_mensuel', period)
            taxe_habitation = simulation.calculate('taxe_habitation', period.this_year)/12

            irpp = self.cast_from_entity_to_role(irpp_holder, role = VOUS)
            irpp = self.sum_by_entity(irpp)

            return period, irpp + taxe_habitation

    class compensated_impo_mensuel(Reform.Variable):
        reference = mesures.impo
        label = u"Impôts directs"
        url = "http://fr.wikipedia.org/wiki/Imp%C3%B4t_direct"

        def function(self, simulation, period):
            '''
            Impôts directs
            '''
            period = period.this_month
            irpp_holder = simulation.compute('compensated_irpp_mensuel', period)
            taxe_habitation = simulation.calculate('taxe_habitation', period.this_year)/12

            irpp = self.cast_from_entity_to_role(irpp_holder, role = VOUS)
            irpp = self.sum_by_entity(irpp)

            return period, irpp + taxe_habitation



    class iaidrdi_mensuel(Reform.Variable):
        reference= ir.iaidrdi
        label = u"iaidrdi"

        def function(self, simulation, period):
            '''
            Impôt après imputation des réductions d'impôt
            '''
            period = period.this_month
            ip_net = simulation.calculate('ip_net_mensuel', period)
            reductions = simulation.calculate('reductions', period.this_year)/12 #Ne pas supprimer, réfléchi

            return period, ip_net - reductions

    class rev_trav_mensuel(Reform.Variable):
        reference = mesures.rev_trav
        label = u"Revenus du travail (salariés et non salariés)"
        url = "http://fr.wikipedia.org/wiki/Revenu_du_travail"

        def function(self, simulation, period):
            '''
            Revenu du travail
            '''
            period = period.this_month
            rev_sal = simulation.calculate('rev_sal_mensuel_times_12', period.this_month)/12
            rag = simulation.calculate_add('rag', period.this_year)/12 #TODO : non mensualisé
            ric = simulation.calculate_add('ric', period.this_year)/12
            rnc = simulation.calculate_add('rnc', period.this_year)/12

            return period, rev_sal + rag + ric + rnc

##### Ensuite les variables transversales

    class br_pf_i(Reform.Variable):
        reference = model.prestations.prestations_familiales.base_ressource.br_pf_i
        label = u"Base ressource individuelle des prestations familiales"

        def function(self, simulation, period):
            period = period.this_month
            annee_fiscale_n_2 = period.n_2

            tspr = simulation.calculate_add('tspr_mensuel_times_12', period) #annee_fiscale_n_2)
            hsup = simulation.calculate_add('hsup', period.this_year) #annee_fiscale_n_2)
            rpns = simulation.calculate_add('rpns', period.this_year) #annee_fiscale_n_2)

            return period, tspr + hsup + rpns




# #ARS  TODO: Mettre l'ARS en mensualisé sur toute l'année ?
#
#     from ...model.prestations.prestations_familiales.base_ressource import nb_enf
#
#     class ars(Reform.Variable):  #TODO: Pourquoi en encotobre et pas en aout ?
#         reference = model.prestations.prestations_familiales.ars.ars
#         label = u"Allocation de rentrée scolaire"
#         url = "http://vosdroits.service-public.fr/particuliers/F1878.xhtml"
#
#         def function(self, simulation, period):
#             '''
#             Allocation de rentrée scolaire brute de CRDS
#             '''
#             period_br = period.this_year
#             period = period.start.offset('first-of', 'year').offset(9, 'month').period('month')
#             age_holder = simulation.compute('age', period)
#             af_nbenf = simulation.calculate('af_nbenf', period)
#             smic55_holder = simulation.compute('smic55', period)
#             br_pf = simulation.calculate('br_pf', period_br.start.offset('first-of', 'month').period('month'))
#             P = simulation.legislation_at(period.start).fam
#             # TODO: convention sur la mensualisation
#             # On tient compte du fait qu'en cas de léger dépassement du plafond, une allocation dégressive
#             # (appelée allocation différentielle), calculée en fonction des revenus, peut être versée.
#             age = self.split_by_roles(age_holder, roles = ENFS)
#             smic55 = self.split_by_roles(smic55_holder, roles = ENFS)
#
#             bmaf = P.af.bmaf
#             # On doit prendre l'âge en septembre
#             enf_05 = nb_enf(age, smic55, P.ars.agep - 1, P.ars.agep - 1)  # 5 ans et 6 ans avant le 31 décembre
#             # enf_05 = 0
#             # Un enfant scolarisé qui n'a pas encore atteint l'âge de 6 ans
#             # avant le 1er février 2012 peut donner droit à l'ARS à condition qu'il
#             # soit inscrit à l'école primaire. Il faudra alors présenter un
#             # certificat de scolarité.
#             enf_primaire = enf_05 + nb_enf(age, smic55, P.ars.agep, P.ars.agec - 1)
#             enf_college = nb_enf(age, smic55, P.ars.agec, P.ars.agel - 1)
#             enf_lycee = nb_enf(age, smic55, P.ars.agel, P.ars.ages)
#
#             arsnbenf = enf_primaire + enf_college + enf_lycee
#
#             # Plafond en fonction du nb d'enfants A CHARGE (Cf. article R543)
#             ars_plaf_res = P.ars.plaf * (1 + af_nbenf * P.ars.plaf_enf_supp)
#             arsbase = bmaf * (P.ars.tx0610 * enf_primaire +
#                              P.ars.tx1114 * enf_college +
#                              P.ars.tx1518 * enf_lycee)
#             # Forme de l'ARS  en fonction des enfants a*n - (rev-plaf)/n
#             # ars_diff = (ars_plaf_res + arsbase - br_pf) / arsnbenf
#             ars = (arsnbenf > 0) * max_(0, arsbase - max_(0, (br_pf - ars_plaf_res) / max_(1, arsnbenf)))
#             # Calcul net de crds : ars_net = (P.ars.enf0610 * enf_primaire + P.ars.enf1114 * enf_college + P.ars.enf1518 * enf_lycee)
#
#             return period, ars * (ars >= P.ars.seuil_nv) #previously period_br instead



    class pfam(Reform.Variable):
        reference = mesures.pfam
        label = u"Total des prestations familiales"
        url = "http://www.social-sante.gouv.fr/informations-pratiques,89/fiches-pratiques,91/prestations-familiales,1885/les-prestations-familiales,12626.html"

        def function(self, simulation, period):
            '''
            Prestations familiales
            '''
            period = period.this_month
            af = simulation.calculate('af', period)
            cf = simulation.calculate('cf', period)
            ars = simulation.calculate('ars', period)
            aeeh = simulation.calculate('aeeh', period.this_year)/12  #paiement mensuel pourquoi en annuel dans les presta ? #TODO : !
            paje = simulation.calculate_add('paje', period)
            asf = simulation.calculate_add('asf', period)
            crds_pfam = simulation.calculate('crds_pfam', period)

            return period, af + cf + ars + paje + asf + crds_pfam + aeeh













    #
    #  Marche, mais on verra plus tard, déjà mensualisé par dessein.
    #
    # class rsa_mensuel(Reform.DatedVariable):
    #     #calculate_output = calculate_output_add #TODO : uncomment ? Warning !
    #     column = FloatCol
    #     label = u"Revenu de solidarité active"
    #     entity_class = Familles
    #
    #     @dated_function(start = date(2009, 06, 1))
    #     def function(self, simulation, period):
    #         period = period.this_month
    #         rsa_majore = simulation.calculate_add('rsa_majore', period)
    #         rsa_non_majore = simulation.calculate_add('rsa_non_majore', period)
    #         rsa_non_calculable = simulation.calculate_add('rsa_non_calculable', period)
    #
    #         rsa = (1 - rsa_non_calculable) * max_(rsa_majore, rsa_non_majore)
    #
    #         return period, rsa
    #
    # class rsa_act_mensuel(Reform.DatedVariable):
    #     base_function = requested_period_added_value
    #     column = FloatCol
    #     entity_class = Familles
    #     label = u"Revenu de solidarité active - activité"
    #     start_date = date(2009, 6, 1)
    #
    #     @dated_function(start = date(2009, 6, 1))
    #     def function_2009(self, simulation, period):
    #         '''
    #         Calcule le montant du RSA activité
    #         Note: le partage en moitié est un point de législation, pas un choix arbitraire
    #         '''
    #         period = period
    #         rsa = simulation.calculate_add('rsa', period)
    #         rmi = simulation.calculate_add('rmi', period)
    #
    #         return period, max_(rsa - rmi, 0)




    class mini_mensuel(Reform.Variable): # Mini mensuel non mensualized
        reference = mesures.mini
        label = u"Minima sociaux"
        url = "http://fr.wikipedia.org/wiki/Minima_sociaux"

        def function(self, simulation, period):
            '''
            Minima sociaux
            '''
            period = period.this_month
            aspa = simulation.calculate_add('aspa', period.this_year)/12  # TODO: put on monthly basis
            aah_holder = simulation.compute_add('aah', period.this_month)  # TODO: put on monthly basis
            caah_holder = simulation.compute_add('caah', period.this_month)  # TODO: put on monthly basis
            asi = simulation.calculate_add('asi', period.this_month)  # TODO: put on monthly basis
            rsa = simulation.calculate_add('rsa', period.this_month) # TODO: put on monthly basis
            aefa = simulation.calculate('aefa', period.this_year)/12 #TODO : put on monthly basis
            api = simulation.calculate_add('api', period.this_month)  # TODO: put on monthly basis
            ass = simulation.calculate_add('ass', period.this_month)  # TODO: put on monthly basis
            psa = simulation.calculate_add('psa', period.this_month)  # TODO: put on monthly basis

            aah = self.sum_by_entity(aah_holder)
            aah = aah/12
            caah = self.sum_by_entity(caah_holder)
            caah = caah/12
            return period, aspa + aah + caah + asi + rsa  + api + ass + psa + aefa



    class psoc_mensuel(Reform.Variable):
        reference = mesures.psoc
        label = u"Total des prestations sociales"
        url = "http://fr.wikipedia.org/wiki/Prestation_sociale"

        def function(self, simulation, period):
            '''
            Prestations sociales
            '''
            period = period.this_month
            pfam = simulation.calculate('pfam', period)
            mini = simulation.calculate('mini_mensuel', period)
            aides_logement = simulation.calculate_add_divide('aides_logement', period)

            return period, pfam + mini + aides_logement

    class mini_mensuel_rsa_mensuel(Reform.Variable): # Mini mensuel non mensualized
        reference = mesures.mini
        label = u"Minima sociaux"
        url = "http://fr.wikipedia.org/wiki/Minima_sociaux"

        def function(self, simulation, period):
            '''
            Minima sociaux
            '''
            period = period.this_month
            aspa = simulation.calculate_add('aspa', period.this_year)/12  # TODO: put on monthly basis
            aah_holder = simulation.compute_add('aah', period.this_month)  # TODO: put on monthly basis
            caah_holder = simulation.compute_add('caah', period.this_month)  # TODO: put on monthly basis
            asi = simulation.calculate_add('asi', period.this_month)  # TODO: put on monthly basis
            rsa = simulation.calculate_add('rsa_mensuel', period.this_month) # TODO: put on monthly basis
            aefa = simulation.calculate('aefa', period.this_year)/12 #TODO : put on monthly basis
            api = simulation.calculate_add('api', period.this_month)  # TODO: put on monthly basis
            ass = simulation.calculate_add('ass', period.this_month)  # TODO: put on monthly basis
            psa = simulation.calculate_add('psa', period.this_month)  # TODO: put on monthly basis

            aah = self.sum_by_entity(aah_holder)
            aah = aah/12
            caah = self.sum_by_entity(caah_holder)
            caah = caah/12
            return period, aspa + aah + caah + asi + rsa  + api + ass + psa + aefa

    class psoc_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.psoc
        label = u"Total des prestations sociales"
        url = "http://fr.wikipedia.org/wiki/Prestation_sociale"

        def function(self, simulation, period):
            '''
            Prestations sociales
            '''
            period = period.this_month
            pfam = simulation.calculate('pfam', period)
            mini = simulation.calculate('mini_mensuel_rsa_mensuel', period)
            aides_logement = simulation.calculate_add_divide('aides_logement', period)

            return period, pfam + mini + aides_logement

    class pen_mensuel(Reform.Variable):
        column = FloatCol(default = 0)
        entity_class = Individus
        label = u"Total des pensions et revenus de remplacement"
        url = "http://fr.wikipedia.org/wiki/Rente"

        def function(self, simulation, period):
            '''
            Pensions
            '''
            period = period.this_month
            chomage_net = (simulation.calculate('chomage_imposable', period) +  simulation.calculate('csg_imposable_chomage', period)
                           + simulation.calculate('crds_chomage', period))
            retraite_nette = (simulation.calculate('retraite_imposable', period) +  simulation.calculate('csg_imposable_retraite', period)
                           + simulation.calculate('crds_retraite', period))
            pensions_alimentaires_percues = simulation.calculate('pensions_alimentaires_percues', period)
            pensions_alimentaires_versees_declarant1 = simulation.calculate_add( #TODO : mensualize
                'pensions_alimentaires_versees_declarant1', period.this_year
                )
            rto_declarant1 = simulation.calculate_add('rto_declarant1', period)

            return period, (chomage_net + retraite_nette + pensions_alimentaires_percues + pensions_alimentaires_versees_declarant1 +
                        rto_declarant1)

    class revdisp_mensuel_annuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate_add('impo', period.this_year)/12

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 neative disposable income.
            revdisp = (revdisp>0) * revdisp

            return period, revdisp

    class revdisp_mensuel_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute_add('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('impo_mensuel', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 negative disposable income.
            revdisp = (revdisp>0) * revdisp


            return period, revdisp


    class revdisp_mensuel_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute_add('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('compensated_impo_mensuel', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 negative disposable income.
            revdisp = (revdisp>0) * revdisp


            return period, revdisp

    class revdisp_mensuel_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute_add('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('compensated_impo_mensuel', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 negative disposable income.
            revdisp = (revdisp>0) * revdisp

            return period, revdisp



    class revdisp_mensuel_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute_add('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel_rsa_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('impo_mensuel', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 negative disposable income.
            revdisp = (revdisp>0) * revdisp


            return period, revdisp

    class revdisp_mensuel_compensated_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute_add('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel_rsa_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('compensated_impo_mensuel', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + impo # TODO: Tweak for the 860 negative disposable income.
            revdisp = (revdisp>0) * revdisp


            return period, revdisp






    class utility_ir_annuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_annuel', period)
            utility = -(((revdisp + 500)*12) **-0.89)/12 #on ajoute 5000 pour pas avoir les familles à 0 de revdisp qui font - inf

            return period, utility

    class utility_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_ir_mensuel', period)
            utility = (-((revdisp + 500)*12) **-0.89)/12

            return period, utility

    class utility_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_compensated_ir_mensuel', period)
            utility = (-((revdisp + 500)*12) **-0.89)/12

            return period, utility





    class inverted_utility_ir_annuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month

            utility = simulation.calculate('utility_ir_annuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12


    class inverted_utility_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_ir_mensuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12

    class inverted_utility_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_compensated_ir_mensuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12

#### Equivalent scale utility
####

    class utility_es_ir_annuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            uc = simulation.calculate('uc', period.this_year)
            revdisp = simulation.calculate('revdisp_mensuel_annuel', period)
            utility = -((revdisp + 500)*12/uc) **-0.89 #on ajoute 5000 pour pas avoir les familles à 0 de revdisp qui font - inf

            return period, utility

    class utility_es_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_ir_mensuel', period)
            uc = simulation.calculate('uc', period.this_year)
            utility = -(((revdisp + 500)*12)/uc) **-0.89

            return period, utility

    class utility_es_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_compensated_ir_mensuel', period)
            uc = simulation.calculate('uc', period.this_year)
            utility = (-(((revdisp + 500)*12)/uc) **-0.89)

            return period, utility

    class inverted_es_utility_ir_annuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month

            utility = simulation.calculate('utility_ir_annuel', period)
            uc = simulation.calculate('uc', period.this_year)


            return period, (np.exp(
                (np.log(-utility*12))/-.89) * uc)/12


    class inverted_es_utility_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_ir_mensuel', period)
            uc = simulation.calculate('uc', period.this_year)


            return period, (np.exp(
                (np.log(-utility*12))/-.89) * uc)/12

    class inverted_es_utility_compensated_ir_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_compensated_ir_mensuel', period)
            uc = simulation.calculate('uc', period.this_year)


            return period, np.exp(
                (np.log(-utility))/-.89) * uc


###RSA utility
###


    class utility_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_ir_mensuel_rsa_mensuel', period)
            utility = -(revdisp + 5000) ** -0.89

            return period, utility
    class inverted_utility_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_ir_mensuel_rsa_mensuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12

    class utility_compensated_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_mensuel_compensated_ir_mensuel_rsa_mensuel', period)
            utility = (-(((revdisp + 500)*12)/uc) **-0.89)/12

            return period, utility
    class inverted_utility_compenstaed_ir_mensuel_rsa_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_compensated_ir_mensuel_rsa_mensuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12























##### Annalyse ####
    #
    # class utility_function_foyer(Reform.Variable):
    #     column = FloatCol(default = 0)
    #     entity_class = Individus
    #
    #     def function(self, simulation, period):
    #         period = period.this_month
    #         tspr_holder = simulation.compute('tspr', period)
    #         tspr = self.sum_by_entity(tspr_holder)
    #
    #
    #         tspr = self.sum_by_entity(tspr_holder)
    #
    #         revdisp =
    #
    #     return





#### RSA 2009 sur toute l'année 2009

#     Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['rmi']))
#
#
#
#
#     class rsa(Reform.DatedVariable):
#         column = FloatCol
#         reference = rsa_ref.rsa
#         start_date = date(2009, 1, 1) #Changed
#
#         @dated_function(start = date(2009, 1, 1))
#         def function(self, simulation, period):
#             period = period.this_month
#             rsa_majore = simulation.calculate('rsa_majore', period)
#             rsa_non_majore = simulation.calculate('rsa_non_majore', period)
#             rsa_non_calculable = simulation.calculate('rsa_non_calculable', period)
#
#             rsa = (1 - rsa_non_calculable) * max_(rsa_majore, rsa_non_majore)
#
#             return period, rsa
#
#
# class br_rmi_pf(DatedVariable):
#     column = FloatCol
#     entity_class = Familles
#     label = u"Prestations familiales inclues dans la base ressource RSA/RMI"
#
#
#     @dated_function(start = date(2004, 1, 1), stop = date(2014, 3, 31))
#     def function_2003(self, simulation, period):
#         period = period.this_month
#         af_base = simulation.calculate('af_base', period)
#         cf = simulation.calculate('cf', period)
#         asf = simulation.calculate('asf', period)
#         paje_base = simulation.calculate('paje_base', period)
#         paje_clca = simulation.calculate('paje_clca', period)
#         paje_prepare = simulation.calculate('paje_prepare', period)
#         paje_colca = simulation.calculate('paje_colca', period)
#         P = simulation.legislation_at(period.start).minim
#
#         return period, P.rmi.pfInBRrmi * (af_base + cf + asf + paje_base + paje_clca + paje_prepare + paje_colca)
#
# class crds_mini(DatedVariable):
#     column = FloatCol
#     entity_class = Familles
#     label = u"CRDS versée sur les minimas sociaux"
#
#     @dated_function(start = date(2009, 6, 1))
#     def function_2009_(self, simulation, period):
#         """
#         CRDS sur les minima sociaux
#         """
#         period = period.this_month
#         rsa_act = simulation.calculate('rsa_act', period)
#         taux_crds = simulation.legislation_at(period.start).fam.af.crds
#
#         return period, - taux_crds * rsa_act
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


    class crds_mini(Reform.DatedVariable):
        column = FloatCol
        reference = rsa_ref.crds_mini
        label = u"CRDS versée sur les minimas sociaux"

        @dated_function(start = date(2009, 1, 1))
        def function_2009_(self, simulation, period):
            """
            CRDS sur les minima sociaux
            """
            period = period.this_month
            rsa_act = simulation.calculate('rsa_act', period)
            taux_crds = simulation.legislation_at(period.start).fam.af.crds

            return period, - taux_crds * rsa_act


    class rsa(Reform.DatedVariable):
        calculate_output = calculate_output_add
        reference = rsa_ref.rsa
        label = u"Revenu de solidarité active"


        @dated_function(start = date(2009, 01, 1))
        def function(self, simulation, period):
            period = period.this_month
            rsa_majore = simulation.calculate('rsa_majore', period)
            rsa_non_majore = simulation.calculate('rsa_non_majore', period)
            rsa_non_calculable = simulation.calculate('rsa_non_calculable', period)
            #print period, rsa_majore,rsa_non_majore,rsa_non_calculable
            rsa = (1 - rsa_non_calculable) * max_(rsa_majore, rsa_non_majore)

            return period, rsa

    class rsa_act(Reform.DatedVariable):
        #base_function = requested_period_added_value
        reference = rsa_ref.rsa_act
        label = u"Revenu de solidarité active - activité"
        start_date = date(2009, 1, 1)

        @dated_function(start = date(2009, 1, 1))
        def function_2009(self, simulation, period):
            '''
            Calcule le montant du RSA activité
            Note: le partage en moitié est un point de législation, pas un choix arbitraire
            '''
            period = period
            rsa = simulation.calculate_add('rsa', period)
            rmi = simulation.calculate_add('rmi', period)

            return period, max_(rsa - rmi, 0)


    class br_rmi(Reform.DatedVariable):
        column = FloatCol
        label = u"Base ressources du Rmi ou du Rsa"
        reference = rsa_ref.br_rmi

        @dated_function(stop = date(2008, 12, 31)) #MODIFIED
        def function_rmi(self, simulation, period):
            period = period.this_month
            br_rmi_pf = simulation.calculate('br_rmi_pf', period)
            br_rmi_ms = simulation.calculate('br_rmi_ms', period)
            br_rmi_i_holder = simulation.compute('br_rmi_i', period)

            br_rmi_i_total = self.sum_by_entity(br_rmi_i_holder)
            return period, br_rmi_pf + br_rmi_ms + br_rmi_i_total

        @dated_function(start = date(2009, 1, 1))
        def function_rsa(self, simulation, period):
            period = period.this_month
            br_rmi_pf = simulation.calculate('br_rmi_pf', period)
            br_rmi_ms = simulation.calculate('br_rmi_ms', period)
            br_rmi_i_holder = simulation.compute('br_rmi_i', period)
            ra_rsa_i_holder = simulation.compute('ra_rsa_i', period)

            br_rmi_i_total = self.sum_by_entity(br_rmi_i_holder)
            ra_rsa_i_total = self.sum_by_entity(ra_rsa_i_holder)
            return period, br_rmi_pf + br_rmi_ms + br_rmi_i_total + ra_rsa_i_total



    class rsa_majore(Reform.DatedVariable):
        label = u"Revenu de solidarité active - majoré"
        reference = rsa_ref.rsa_majore

        @dated_function(start = date(2009, 01, 1))
        def function(self, simulation, period):
            period = period.this_month
            rsa_socle_majore = simulation.calculate('rsa_socle_majore', period)
            ra_rsa = simulation.calculate('ra_rsa', period)
            rsa_forfait_logement = simulation.calculate('rsa_forfait_logement', period)
            br_rmi = simulation.calculate('br_rmi', period)
            P = simulation.legislation_at(period.start).minim.rmi

            base_normalise = max_(rsa_socle_majore - rsa_forfait_logement - br_rmi + P.pente * ra_rsa, 0)

            return period, base_normalise * (base_normalise >= P.rsa_nv)

    class rsa_non_majore(Reform.DatedVariable):
        column = FloatCol
        label = u"Revenu de solidarité active - non majoré"
        reference = rsa_ref.rsa_non_majore

        @dated_function(start = date(2009, 01, 1))
        def function(self, simulation, period):
            period = period.this_month
            rsa_socle = simulation.calculate('rsa_socle', period)
            ra_rsa = simulation.calculate('ra_rsa', period)
            rsa_forfait_logement = simulation.calculate('rsa_forfait_logement', period)
            br_rmi = simulation.calculate('br_rmi', period)
            P = simulation.legislation_at(period.start).minim.rmi

            base_normalise = max_(rsa_socle - rsa_forfait_logement - br_rmi + P.pente * ra_rsa, 0)

            return period, base_normalise * (base_normalise >= P.rsa_nv)


    class ra_rsa(Reform.Variable):
        column = FloatCol
        reference = rsa_ref.ra_rsa
        start_date = date(2009, 1, 1) #Changed

        def function(self, simulation, period):
            period = period.this_month
            ra_rsa_i_holder = simulation.compute('ra_rsa_i', period)

            ra_rsa = self.sum_by_entity(ra_rsa_i_holder)
            return period, ra_rsa




    class ra_rsa_i(Reform.Variable):
        reference = rsa_ref.ra_rsa_i
        label = u"Revenus d'activité du Rsa - Individuel"
        start_date = date(2009, 1, 1)

        def function(self, simulation, period):
            period = period.this_month

            r = rsa_ressource_calculator(simulation, period)

            salaire_net = r.calcule_ressource('salaire_net', revenu_pro = True)
            indemnites_journalieres = r.calcule_ressource('indemnites_journalieres', revenu_pro = True)
            indemnites_chomage_partiel = r.calcule_ressource('indemnites_chomage_partiel', revenu_pro = True)
            indemnites_volontariat = r.calcule_ressource('indemnites_volontariat', revenu_pro = True)
            revenus_stage_formation_pro = r.calcule_ressource('revenus_stage_formation_pro', revenu_pro = True)
            indemnites_stage = r.calcule_ressource('indemnites_stage', revenu_pro = True)
            bourse_recherche = r.calcule_ressource('bourse_recherche', revenu_pro = True)
            hsup = r.calcule_ressource('hsup', revenu_pro = True)
            etr = r.calcule_ressource('etr', revenu_pro = True)

            # Ressources TNS

            # WARNING : D'après les caisses, le revenu pris en compte pour les AE pour le RSA ne prend en compte que
            # l'abattement standard sur le CA, mais pas les cotisations pour charges sociales. Dans l'attente d'une
            # éventuelle correction, nous implémentons selon leurs instructions. Si changement, il suffira de remplacer le
            # tns_auto_entrepreneur_benefice par tns_auto_entrepreneur_revenus_net
            tns_auto_entrepreneur_revenus_rsa = r.calcule_ressource('tns_auto_entrepreneur_benefice', revenu_pro = True)

            result = (
                salaire_net + indemnites_journalieres + indemnites_chomage_partiel + indemnites_volontariat +
                revenus_stage_formation_pro + indemnites_stage + bourse_recherche + hsup + etr +
                tns_auto_entrepreneur_revenus_rsa
            ) / 3

            return period, result



    class rsa_base_ressources_patrimoine_i(Reform.DatedVariable):
        reference = rsa_ref.rsa_base_ressources_patrimoine_i
        label = u"Base de ressources des revenus du patrimoine du RSA"
        start_date = date(2009, 1, 1)

        @dated_function(start = date(2009, 1, 1))
        def function_2009_(self, simulation, period):
            period = period.this_month
            interets_epargne_sur_livrets = simulation.calculate('interets_epargne_sur_livrets', period)
            epargne_non_remuneree = simulation.calculate('epargne_non_remuneree', period)
            revenus_capital = simulation.calculate('revenus_capital', period)
            valeur_locative_immo_non_loue = simulation.calculate('valeur_locative_immo_non_loue', period)
            valeur_locative_terrains_non_loue = simulation.calculate('valeur_locative_terrains_non_loue', period)
            revenus_locatifs = simulation.calculate('revenus_locatifs', period)
            rsa = simulation.legislation_at(period.start).minim.rmi

            return period, (
                interets_epargne_sur_livrets / 12 +
                epargne_non_remuneree * rsa.patrimoine.taux_interet_forfaitaire_epargne_non_remunere / 12 +
                revenus_capital +
                valeur_locative_immo_non_loue * rsa.patrimoine.abattement_valeur_locative_immo_non_loue +
                valeur_locative_terrains_non_loue * rsa.patrimoine.abattement_valeur_locative_terrains_non_loue +
                revenus_locatifs
                )




    class rsa_socle_majore(Reform.Variable):
        reference = rsa_ref.rsa_socle_majore
        label = u"Majoration pour parent isolé du Revenu de solidarité active socle"
        start_date = date(2009, 1, 1)

        def function(self, simulation, period):
            period = period.this_month
            rmi = simulation.legislation_at(period.start).minim.rmi
            eligib = simulation.calculate('rsa_majore_eligibilite', period)
            nbenf = simulation.calculate('nb_enfant_rsa', period)
            taux = rmi.majo_rsa.pac0 + rmi.majo_rsa.pac_enf_sup * nbenf
            return period, eligib * rmi.rmi * taux


    class rsa_ressource_calculator:

        def __init__(self, simulation, period):
            self.period = period
            self.simulation = simulation
            self.three_previous_months = self.period.start.period('month', 3).offset(-3)
            self.last_month = period.start.period('month').offset(-1)
            self.has_ressources_substitution = (
                simulation.calculate('chomage_net', period) +
                simulation.calculate('indemnites_journalieres', period) +
                simulation.calculate('retraite_nette', period)  # +
                # simulation.calculate('ass', last_month)
            ) > 0
            self.neutral_max_forfaitaire = 3 * simulation.legislation_at(period.start).minim.rmi.rmi

        def calcule_ressource(self, variable_name, revenu_pro = False):
            ressource_trois_derniers_mois = self.simulation.calculate_add(variable_name, self.three_previous_months)
            ressource_mois_courant = self.simulation.calculate(variable_name, self.period)
            ressource_last_month = self.simulation.calculate(variable_name, self.last_month)

            if revenu_pro:
                condition = (
                    (ressource_mois_courant == 0) *
                    (ressource_last_month > 0) *
                    not_(self.has_ressources_substitution)
                )
                return (1 - condition) * ressource_trois_derniers_mois
            else:
                condition = (
                    (ressource_mois_courant == 0) *
                    (ressource_last_month > 0)
                )
                return max_(0,
                    ressource_trois_derniers_mois - condition * self.neutral_max_forfaitaire)




###### On essaye de mensualiser toutes les aides sociales.




    class ra_rsa_mensualise(Reform.Variable): #####Rsa mensuel au lieu de trimestriel
        column = FloatCol
        reference = rsa_ref.ra_rsa
        start_date = date(2009, 1, 1) #Changed

        def function(self, simulation, period):
            period = period.this_month
            ra_rsa_i_holder = simulation.compute('ra_rsa_i_mensualise', period)

            ra_rsa = self.sum_by_entity(ra_rsa_i_holder)
            return period, ra_rsa




    class ra_rsa_i_mensualise(Reform.Variable):
        reference = rsa_ref.ra_rsa_i
        label = u"Revenus d'activité du Rsa - Individuel"
        start_date = date(2009, 1, 1)

        def function(self, simulation, period):
            period = period.this_month

            r = rsa_ressource_calculator_mensualise(simulation, period)

            salaire_net = r.calcule_ressource('salaire_net', revenu_pro = True)
            indemnites_journalieres = r.calcule_ressource('indemnites_journalieres', revenu_pro = True)
            indemnites_chomage_partiel = r.calcule_ressource('indemnites_chomage_partiel', revenu_pro = True)
            indemnites_volontariat = r.calcule_ressource('indemnites_volontariat', revenu_pro = True)
            revenus_stage_formation_pro = r.calcule_ressource('revenus_stage_formation_pro', revenu_pro = True)
            indemnites_stage = r.calcule_ressource('indemnites_stage', revenu_pro = True)
            bourse_recherche = r.calcule_ressource('bourse_recherche', revenu_pro = True)
            hsup = r.calcule_ressource('hsup', revenu_pro = True)
            etr = r.calcule_ressource('etr', revenu_pro = True)

            # Ressources TNS

            # WARNING : D'après les caisses, le revenu pris en compte pour les AE pour le RSA ne prend en compte que
            # l'abattement standard sur le CA, mais pas les cotisations pour charges sociales. Dans l'attente d'une
            # éventuelle correction, nous implémentons selon leurs instructions. Si changement, il suffira de remplacer le
            # tns_auto_entrepreneur_benefice par tns_auto_entrepreneur_revenus_net
            tns_auto_entrepreneur_revenus_rsa = r.calcule_ressource('tns_auto_entrepreneur_benefice', revenu_pro = True)

            result = (
                salaire_net + indemnites_journalieres + indemnites_chomage_partiel + indemnites_volontariat +
                revenus_stage_formation_pro + indemnites_stage + bourse_recherche + hsup + etr +
                tns_auto_entrepreneur_revenus_rsa
            ) #/ 3

            return period, result



    class rsa_base_ressources_patrimoine_i_mensualise(Reform.DatedVariable):
        reference = rsa_ref.rsa_base_ressources_patrimoine_i
        label = u"Base de ressources des revenus du patrimoine du RSA"
        start_date = date(2009, 1, 1)

        @dated_function(start = date(2009, 1, 1))
        def function_2009_(self, simulation, period):
            period = period.this_month
            interets_epargne_sur_livrets = simulation.calculate('interets_epargne_sur_livrets', period)
            epargne_non_remuneree = simulation.calculate('epargne_non_remuneree', period)
            revenus_capital = simulation.calculate('revenus_capital', period)
            valeur_locative_immo_non_loue = simulation.calculate('valeur_locative_immo_non_loue', period)
            valeur_locative_terrains_non_loue = simulation.calculate('valeur_locative_terrains_non_loue', period)
            revenus_locatifs = simulation.calculate('revenus_locatifs', period)
            rsa = simulation.legislation_at(period.start).minim.rmi

            return period, (
                interets_epargne_sur_livrets / 12 +
                epargne_non_remuneree * rsa.patrimoine.taux_interet_forfaitaire_epargne_non_remunere / 12 +
                revenus_capital +
                valeur_locative_immo_non_loue * rsa.patrimoine.abattement_valeur_locative_immo_non_loue +
                valeur_locative_terrains_non_loue * rsa.patrimoine.abattement_valeur_locative_terrains_non_loue +
                revenus_locatifs
                )




    class rsa_non_majore_mensualise(Reform.DatedVariable):
        reference = rsa_ref.rsa_non_majore
        label = u"Revenu de solidarité active - non majoré"
        entity_class = Familles

        @dated_function(start = date(2009, 01, 1))
        def function(self, simulation, period):
            period = period.this_month
            rsa_socle = simulation.calculate('rsa_socle', period) #already on monthly basis
            ra_rsa = simulation.calculate('ra_rsa_mensualise', period)
            rsa_forfait_logement = simulation.calculate('rsa_forfait_logement', period) #TODO : mensualize
            br_rmi = simulation.calculate('br_rmi', period)
            P = simulation.legislation_at(period.start).minim.rmi

            base_normalise = max_(rsa_socle - rsa_forfait_logement - br_rmi + P.pente * ra_rsa, 0)

            return period, base_normalise * (base_normalise >= P.rsa_nv)




    class rsa_socle_majore_mensualise(Reform.Variable):
        reference = rsa_ref.rsa_socle_majore
        label = u"Majoration pour parent isolé du Revenu de solidarité active socle"
        start_date = date(2009, 1, 1)

        def function(self, simulation, period):
            period = period.this_month
            rmi = simulation.legislation_at(period.start).minim.rmi
            eligib = simulation.calculate('rsa_majore_eligibilite', period) #already on monthly basis
            nbenf = simulation.calculate('nb_enfant_rsa', period.this_year.this_month)
            taux = rmi.majo_rsa.pac0 + rmi.majo_rsa.pac_enf_sup * nbenf
            return period, eligib * rmi.rmi * taux

    class rsa_majore_mensualise(Reform.DatedVariable):
        column = FloatCol
        label = u"Revenu de solidarité active - majoré"
        reference = rsa_ref.rsa_majore

        @dated_function(start = date(2009, 01, 1))
        def function(self, simulation, period):
            period = period.this_month
            rsa_socle_majore = simulation.calculate('rsa_socle_majore_mensualise', period)
            ra_rsa = simulation.calculate('ra_rsa_mensualise', period)
            rsa_forfait_logement = simulation.calculate('rsa_forfait_logement', period) #TODO: mensualize
            br_rmi = simulation.calculate('br_rmi', period)
            P = simulation.legislation_at(period.start).minim.rmi

            base_normalise = max_(rsa_socle_majore - rsa_forfait_logement - br_rmi + P.pente * ra_rsa, 0)

            return period, base_normalise * (base_normalise >= P.rsa_nv)


    class rsa_mensuel(Reform.DatedVariable):
     #calculate_output = calculate_output_add #TODO : uncomment ? Warning !
     column = FloatCol
     label = u"Revenu de solidarité active"
     entity_class = Familles

     @dated_function(start = date(2009, 01, 1))
     def function(self, simulation, period):
         period = period.this_month
         rsa_majore = simulation.calculate_add('rsa_majore_mensualise', period) #TODO: mensualize
         rsa_non_majore = simulation.calculate_add('rsa_non_majore_mensualise', period)
         #rsa_non_calculable = simulation.calculate_add('rsa_non_calculable_mensualise', period)

         rsa = max_(rsa_majore, rsa_non_majore) #rsa_non_calculable égal à zero

         return period, rsa


    class rsa_ressource_calculator_mensualise:

        def __init__(self, simulation, period):
            self.period = period.this_month
            self.simulation = simulation
            self.three_previous_months = self.period.start.period('month', 3).offset(-3)
            self.last_month = period.start.period('month').offset(-1)
            self.has_ressources_substitution = (
                simulation.calculate('chomage_net', period) +
                simulation.calculate('indemnites_journalieres', period) +
                simulation.calculate('retraite_nette', period)  # +
                # simulation.calculate('ass', last_month)
            ) > 0
            self.neutral_max_forfaitaire =  simulation.legislation_at(period.start).minim.rmi.rmi # 3 *

        def calcule_ressource(self, variable_name, revenu_pro = False):
            ressource_trois_derniers_mois = self.simulation.calculate_add(variable_name, self.three_previous_months)
            ressource_mois_courant = self.simulation.calculate(variable_name, self.period)
            ressource_last_month = self.simulation.calculate(variable_name, self.last_month)

            if revenu_pro:
                condition = (
                    (ressource_mois_courant == 0) *
                    (ressource_last_month > 0) *
                    not_(self.has_ressources_substitution)
                )
                return ressource_mois_courant ##
            else:
                condition = (
                    (ressource_mois_courant == 0) *
                    (ressource_last_month > 0)
                )
                return max_(0,
                    ressource_trois_derniers_mois - condition * self.neutral_max_forfaitaire)






    class rsa_lambda_compensation(Reform.Variable):
        column = FloatCol(default = 0)
        entity_class = Familles
        label = u"Impôt sur le revenu des personnes physiques"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_year
            rsa_annuel = simulation.calculate_add("rsa", period)
            rsa_mensuel = simulation.calculate_add("rsa_mensuel", period)
            lambda_compensation = ((rsa_mensuel*12)/rsa_annuel) - 12  #En fait impot mensuel est égal à G(y_T)/T il faut monter plus haut pour prendre le lambda

            #lambda_compensation = ((impot_annuel == 0) & (impot_mensuel == 0)) * 0 + ~((impot_annuel == 0) & (impot_mensuel == 0)) * lambda_compensation
            import numpy as np
            rsa_lambda_compensation = (rsa_annuel == 0) * 0 + ~(rsa_annuel == 0) * lambda_compensation #empèche d'avoir des + l'infiny

            #import numpy as np
            #assert np.all(np.isfinite(lambda_compensation))
            ## traiter le cas ou irpp annuel = 0

            return period, rsa_lambda_compensation


    class rsa_compensated_annual(Reform.Variable):
        column = FloatCol(default = 0)
        entity_class = Familles
        label = u"Impôt sur le revenu des personnes physiques"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_month

            rsa_mensuel_times_12 = simulation.calculate("rsa_mensuel", period)*12
            rsa_lambda_compensation = simulation.calculate("rsa_lambda_compensation", period.this_year)

            rsa_compensated_annual = rsa_mensuel_times_12/(12 + rsa_lambda_compensation)
            rsa_compensated_annual = (simulation.calculate("irpp", period.this_year) == 0) * 0 + \
                ~(simulation.calculate("irpp", period.this_year) == 0) * np.nan_to_num(rsa_compensated_annual)
            rsa_compensated_annual = (
                            (simulation.calculate_add("rsa_mensuel", period.this_year) == 0) * #Condition
                            (simulation.calculate_add("rsa", period.this_year)/12) # on répartit sur l'année
                        ) + ~(simulation.calculate_add("rsa_mensuel", period.this_year) == 0) * rsa_compensated_annual #condition opposée

            #print compensated_irpp[[4,743]]
            return period, compensated_irpp









#### Outils ####

    class decote_menage(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_year
            decote_holder = simulation.compute('decote_gain_fiscal', period)
            decote = self.cast_from_entity_to_role(decote_holder, role = VOUS)
            decote = self.sum_by_entity(decote)

            return period, decote
    class decote_mensuel_menage(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            decote_holder = simulation.compute('decote_gain_fiscal_mensuel_times_12', period)
            decote = self.cast_from_entity_to_role(decote_holder, role = VOUS)
            decote = self.sum_by_entity(decote)/12

            return period, decote








############################################################################################################################################################
###########            ########################
############Vickrey tax########################
############           ########################
############################################################################################################################################################





##### Dans l'ordre du revenu rev_sal à l'ir
    class rev_sal_vickrey(Reform.Variable):
        reference = ir.rev_sal
        label = u"Nouveau revenu brut global intégrant les allocations familiales"
        def function(self, simulation, period):

            period = period.this_month

            month_number = period.start.date.month
            vickrey_period = period.this_month.start.period("month", month_number).offset(-(month_number-1))
            print vickrey_period

            salaire_imposable_mensuel =  simulation.calculate_add('salaire_imposable', vickrey_period)
            cho = simulation.calculate_add('chomage_imposable', vickrey_period)

            return period, salaire_imposable_mensuel/month_number * 12 + cho/month_number * 12


    class salcho_imp_vickrey(Reform.Variable):
        label = u"Salaires et chômage imposables après abattements"
        reference = ir.salcho_imp

        def function(self, simulation, period):
            period = period.this_month
            rev_sal = simulation.calculate('rev_sal_vickrey', period)
            chomeur_longue_duree = simulation.calculate('chomeur_longue_duree', period.this_year) #MP #TODO : mensualiser ?
            frais_reels = simulation.calculate('frais_reels', period.this_year) #MP
            abatpro = simulation.legislation_at(period.start).ir.tspr.abatpro #TODO: check if need to multiply threshold---> No because already multiplied by 12 !

            abattement_minimum = abatpro.min * not_(chomeur_longue_duree) + abatpro.min2 * chomeur_longue_duree
            abatfor = round(min_(max_(abatpro.taux * rev_sal, abattement_minimum), abatpro.max))

            return period, (frais_reels > abatfor) * (rev_sal - frais_reels) + (frais_reels <= abatfor) * max_(0, rev_sal - abatfor)





    class rev_pen_mensuel_vickrey(Reform.Variable):
        label = u"Revenu imposé comme des pensions (retraites, pensions alimentaires, etc.)"
        reference = ir.rev_pen

        def function(self, simulation, period):
            period = period.this_month


            month_number = period.start.date.month
            vickrey_period = period.this_month.start.period("month", month_number).offset(-(month_number-1))


            pensions_alimentaires_percues = simulation.calculate_add('pensions_alimentaires_percues', period)
            pensions_alimentaires_percues_decl = simulation.calculate_add('pensions_alimentaires_percues_decl', period) #TODO : mensualiser les pensions si possible
            retraite_imposable = simulation.calculate('retraite_imposable', vickrey_period)

            return period, pensions_alimentaires_percues * pensions_alimentaires_percues_decl + retraite_imposable/month_number * 12


    class pen_net_mensuel_vickrey(Reform.Variable):
        label = u"Pensions après abattements"
        reference = ir.pen_net

        def function(self, simulation, period):
            period = period.this_month
            rev_pen = simulation.calculate('rev_pen_mensuel_vickrey', period.this_month)
            abatpen = simulation.legislation_at(period.start).ir.tspr.abatpen

            #    TODO: problème car les pensions sont majorées au niveau du foyer
        #    d11 = ( AS + BS + CS + DS + ES +
        #            AO + BO + CO + DO + EO )
        #    penv2 = (d11-f11> abatpen.max)*(penv + (d11-f11-abatpen.max)) + (d11-f11<= abatpen.max)*penv
        #    Plus d'abatement de 20% en 2006
            return period, max_(0, rev_pen - round(max_(abatpen.taux * rev_pen, abatpen.min)))





    class sal_pen_net_vicrkey_mensuel(Reform.Variable):
        reference = ir.sal_pen_net
        label = u"Salaires et chômage imposables après abattements"

        def function(self, simulation, period):
            period = period.this_month
            salcho_imp = simulation.calculate('salcho_imp_vickrey', period)
            pen_net = simulation.calculate('pen_net_mensuel_vickrey', period)
            abat_sal_pen = simulation.calculate('abat_sal_pen', period)

            return period, salcho_imp + pen_net - abat_sal_pen











        # def function(self, simulation, period):
        #     period = period.this_month
        #     salcho_imp = simulation.calculate('salcho_imp_mensuel_times_12', period)  #NMP
        #    # pen_net = simulation.calculate('pen_net', period.this_year)    #NMP #TODO: mensualize pen_net --> pas l'info en mensuel sauf si retraité
        #
        #
        #     ##### Tweak pour avoir les retraites imposables, on prend les pen_net,
        #     #####  on soustrait les retraites imposable, on rajoute la retraite imposable mensuelle.
        #
        #     retraite_imposable = simulation.calculate('retraite_imposable', period) * 12
        #     pen_net = simulation.calculate('pen_net', period.this_year) \
        #               - simulation.calculate_add('retraite_imposable', period.this_year)  # Vu qu'on est en *12 sur la retraite imposable, on a comme
        #                                                                                   # si on repartissait le reste des pensions chaque mois sur l'année !
        #     pen_net = simulation.calculate('pen_net', period.this_year) + retraite_imposable  #on rajoute la retraite du mois
        #
        #     #####
        #
        #     abat_sal_pen = simulation.calculate('abat_sal_pen', period.this_year) #MP # TODO : mensualiser en ajoutant la formule et en modifiant le calcul, pour l'instant on prend le résultat annuel en le mensualisant



    class tspr_vickrey_mensuel(Reform.Variable):
        reference = ir.tspr
        label = u"Traitements salaires pensions et rentes individuelles"

        def function(self, simulation, period):
            period = period.this_month
            sal_pen_net = simulation.calculate('sal_pen_net_vicrkey_mensuel', period)
            # Quand tspr est calculé sur une année glissante, rto_net_declarant1 est calculé sur l'année légale
            # correspondante.
            rto_net_declarant1 = simulation.calculate('rto_net_declarant1', period.this_year) #period.offset('first-of')) #TODO: Mensualiser, Done ?

            return period, sal_pen_net + rto_net_declarant1

    class rev_cat_tspr_vickrey_mensuel(Reform.Variable):
        reference = ir.rev_cat_tspr
        label = u"Revenu catégoriel - Traitements, salaires, pensions et rentes"

        def function(self, simulation, period):
            period = period.this_month
            tspr_holder = simulation.compute('tspr_vickrey_mensuel', period)
            indu_plaf_abat_pen = simulation.calculate('indu_plaf_abat_pen', period.this_year) #NMP #TODO : check

            tspr = self.sum_by_entity(tspr_holder)

            return period, tspr + indu_plaf_abat_pen


    class rev_cat_vickrey_mensuel(Reform.Variable):
        reference = ir.rev_cat
        label = u"Revenu catégoriel "
        def function(self, simulation, period):
            '''
            Revenus Categoriels
            '''
            period = period.this_month
            rev_cat_tspr = simulation.calculate('rev_cat_tspr_vickrey_mensuel', period)
            rev_cat_rvcm = simulation.calculate('rev_cat_rvcm', period.this_year)
            rev_cat_rfon = simulation.calculate('rev_cat_rfon', period.this_year)  #TODO : Bien checker http://bofip.impots.gouv.fr/bofip/6448-PGP , pour l'instant mis en annuel à l'arrache
            rev_cat_rpns = simulation.calculate('rev_cat_rpns', period.this_year)
            rev_cat_pv = simulation.calculate('rev_cat_pv', period.this_year)

            return period, rev_cat_tspr + rev_cat_rvcm + rev_cat_rfon + rev_cat_rpns + rev_cat_pv

    class rbg_vickrey_mensuel(Reform.Variable):
        reference = ir.rbg
        label = "revenu brut global"
        def function(self, simulation, period):
            '''Revenu brut global
            '''
            period = period.this_month
            rev_cat = simulation.calculate('rev_cat_vickrey_mensuel', period)
            deficit_ante = simulation.calculate('deficit_ante', period.this_year) # TODO : check
            f6gh = simulation.calculate('f6gh', period.this_year) # TODO : check
            nbic_impm_holder = simulation.compute('nbic_impm', period.this_year) # TODO : check
            nacc_pvce_holder = simulation.compute('nacc_pvce', period.this_year)
            cga = simulation.legislation_at(period.start).ir.rpns.cga_taux2

            # (Total 17)
            # sans les revenus au quotient
            nacc_pvce = self.sum_by_entity(nacc_pvce_holder)
            return period, max_(0,rev_cat ) \
                + f6gh + (self.sum_by_entity(nbic_impm_holder) + nacc_pvce) * (1 + cga) - deficit_ante


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

    class rng_vickrey_mensuel(Reform.Variable):
        reference = ir.rng
        label = u"Revenu net global"
        url = "http://impotsurlerevenu.org/definitions/114-revenu-net-global.php"

        def function(self, simulation, period):
            ''' Revenu net global (total 20) '''
            period = period.this_month
            rbg = simulation.calculate('rbg_vickrey_mensuel', period)
            csg_deduc = simulation.calculate('csg_deduc', period.this_year) #TODO : modify properly --> concerns only revenu du patrimoine, reste annuel
            charges_deduc = simulation.calculate('charges_deduc', period.this_year) #TODO : modify properly

            return period, max_(0, rbg - csg_deduc - charges_deduc)

    class rni_vickrey_mensuel(Reform.Variable):
        reference = ir.rni
        label = 'revenu net imposable'

        def function(self, simulation, period):
            ''' Revenu net imposable ou déficit à reporter'''
            period = period.this_month
            rng = simulation.calculate('rng_vickrey_mensuel', period)
            abat_spe = simulation.calculate('abat_spe', period.this_year)

            return period, rng - abat_spe

###

    class ir_brut_vickrey_mensuel(Reform.Variable):
        reference = ir.ir_brut
        label = u"Impot sur le revenu brut avant non imposabilité et plafonnement du quotient"

        def function(self, simulation, period):
            #period = period.start.offset('first-of', 'month').period('year')
            period = period.this_month
            nbptr = simulation.calculate('nbptr', period.this_year) #TODO : change to monthly ?
            taux_effectif = simulation.calculate('taux_effectif', period.this_year) #TODO : check

            rni = simulation.calculate('rni_vickrey_mensuel', period)
            bareme = simulation.legislation_at(period.start).ir.bareme

            return period, (taux_effectif == 0) * nbptr * bareme.calc(rni / nbptr) + taux_effectif * rni #TODO : check fait augmenter le % de mensuel inférieur à l'annuel de 2%
            #return period, 1 * nbptr * bareme.calc(rni / nbptr)

            ########
            #(taux_effectif == 0) * nbptr * ((bareme.calc(rni*12 / nbptr))/12) #+ taux_effectif * rni



    class ir_ss_qf_vickrey_mensuel(Reform.Variable):
        reference = ir.ir_ss_qf
        label = u"ir_ss_qf"

        def function(self, simulation, period):
            '''
            Impôt sans quotient familial
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut_vickrey_mensuel', period)
            rni = simulation.calculate('rni_vickrey_mensuel', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year) #TODO: think how to mensualize
            bareme = simulation.legislation_at(period.start).ir.bareme

            A = bareme.calc(rni / nb_adult)
            return period, nb_adult * A

    class ir_plaf_qf_vickrey_mensuel(Reform.Variable):
        label = u"ir_plaf_qf"
        reference = ir.ir_plaf_qf

        def function(self, simulation, period):
            '''
            Impôt après plafonnement du quotient familial et réduction complémentaire
            '''
            period = period.this_month
            ir_brut = simulation.calculate('ir_brut_vickrey_mensuel', period)
            ir_ss_qf = simulation.calculate('ir_ss_qf_vickrey_mensuel', period)
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


    class decote_vickrey_mensuel(Reform.DatedVariable): #Ne marche pas je modifie dans en dur...
        reference = ir.decote
        label = u"décote"

        @dated_function(start = date(2001, 1, 1), stop = date(2013, 12, 31))
        def function_2001_2013(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_vickrey_mensuel', period)
            decote = simulation.legislation_at(period.start).ir.decote

            return period, (ir_plaf_qf < decote.seuil) * (decote.seuil - ir_plaf_qf) * 0.5

        @dated_function(start = date(2014, 1, 1))
        def function_2014__(self, simulation, period):
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_vickrey_mensuel', period)
            nb_adult = simulation.calculate('nb_adult', period.this_year)
            decote_seuil_celib = simulation.legislation_at(period.start).ir.decote.seuil_celib
            decote_seuil_couple = simulation.legislation_at(period.start).ir.decote.seuil_couple
            decote_celib = (ir_plaf_qf < decote_seuil_celib) * (decote_seuil_celib - ir_plaf_qf)
            decote_couple = (ir_plaf_qf < decote_seuil_couple) * (decote_seuil_couple - ir_plaf_qf)

            return period, (nb_adult == 1) * decote_celib + (nb_adult == 2) * decote_couple

    class decote_gain_fiscal_vickrey_mensuel(Reform.Variable): #Ne marche pas je modifie dans en dur...
        reference = ir.decote_gain_fiscal
        label = u"décote_gain_fiscal"

        def function(self, simulation, period):
            '''
            Renvoie le gain fiscal du à la décote
            '''
            period = period.this_month
            decote = simulation.calculate('decote_vickrey_mensuel', period)
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_mensuel_times_12', period)

            return period, min_(decote, ir_plaf_qf)

    class ip_net_vickrey_mensuel(Reform.Variable):
        reference = ir.ip_net
        label = u"ip_net"

        def function(self, simulation, period):
            '''
            irpp après décote
            '''
            period = period.this_month
            ir_plaf_qf = simulation.calculate('ir_plaf_qf_vickrey_mensuel', period)
            cncn_info_holder = simulation.compute('cncn_info', period)
            decote = simulation.calculate('decote_vickrey_mensuel', period)
            taux = simulation.legislation_at(period.start).ir.rpns.taux16
            month_number = period.start.date.month

            return period, (max_(0, ir_plaf_qf + self.sum_by_entity(cncn_info_holder) * taux - decote))/12 # Todo : divise ici par 12


#
#
#     #
#     # class rfr_mensuel(Reform.Variable):  #utile pour la base ressource, que si on veut mensualiser le rsa
#     #     reference = ir.rfr
#     #     label = u"Revenu fiscal de référence"
#     #
#     #     def function(self, simulation, period):
#     #         '''
#     #         Revenu fiscal de référence
#     #         f3vg -> rev_cat_pv -> ... -> rni
#     #         '''
#     #         period = period.this_month
#     #         rni = simulation.calculate('rni_mensuel_times_12', period)
#     #         f3va_holder = simulation.compute('f3va', period.this_year)
#     #         f3vi_holder = simulation.compute('f3vi', period.this_year)
#     #         rfr_cd = simulation.calculate('rfr_cd', period.this_year)
#     #         rfr_rvcm = simulation.calculate('rfr_rvcm', period.this_year)
#     #         rpns_exon_holder = simulation.compute('rpns_exon', period.this_year)
#     #         rpns_pvce_holder = simulation.compute('rpns_pvce', period.this_year)
#     #         rev_cap_lib = simulation.calculate_add('rev_cap_lib', period.this_year)
#     #         f3vz = simulation.calculate('f3vz', period.this_year)
#     #         microentreprise = simulation.calculate('microentreprise', period.this_year)
#     #
#     #         f3va = self.sum_by_entity(f3va_holder)
#     #         f3vi = self.sum_by_entity(f3vi_holder)
#     #         rpns_exon = self.sum_by_entity(rpns_exon_holder)
#     #         rpns_pvce = self.sum_by_entity(rpns_pvce_holder)
#     #         return period, (max_(0, rni) + rfr_cd + rfr_rvcm + rev_cap_lib + f3vi + rpns_exon + rpns_pvce + f3va +
#     #                 f3vz + microentreprise)




    class iai_vickrey_mensuel(Reform.Variable):
        reference = ir.iai
        label = u"Impôt avant imputations"
        url = "http://forum-juridique.net-iris.fr/finances-fiscalite-assurance/43963-declaration-impots.html"

        def function(self, simulation, period):
            '''
            impôt avant imputation de l'irpp
            '''
            period = period.this_month
            iaidrdi = simulation.calculate('iaidrdi_vickrey_mensuel', period)
            plus_values = simulation.calculate('plus_values', period.this_year)/12
            cont_rev_loc = simulation.calculate('cont_rev_loc', period.this_year)/12
            teicaa = simulation.calculate('teicaa', period.this_year)/12

            return period, iaidrdi + plus_values + cont_rev_loc + teicaa

    class iaidrdi_vickrey_mensuel(Reform.Variable):
        reference= ir.iaidrdi
        label = u"iaidrdi"

        def function(self, simulation, period):
            '''
            Impôt après imputation des réductions d'impôt
            '''
            period = period.this_month
            ip_net = simulation.calculate('ip_net_vickrey_mensuel', period)
            reductions = simulation.calculate('reductions', period.this_year)/12 #Ne pas supprimer, réfléchi

            return period, ip_net - reductions

#
#
# #######FIN
#
#
    class irpp_vickrey_mensuel(Reform.Variable):
        column = FloatCol(default = 0)
        reference = ir.irpp
        label = u"Impôt sur le revenu des personnes physiques"
        url = "http://www.impots.gouv.fr/portal/dgi/public/particuliers.impot?pageId=part_impot_revenu&espId=1&impot=IR&sfid=50"

        def function(self, simulation, period):
            '''
            Montant après seuil de recouvrement (hors ppe)
            '''
            period = period.this_month
            iai = simulation.calculate('iai_vickrey_mensuel', period)
            credits_impot = simulation.calculate('credits_impot', period.this_year)/12
            cehr = simulation.calculate('cehr', period.this_year)/12 #TODO : mensualiser
            P = simulation.legislation_at(period.start).ir.recouvrement

            month_number = period.start.date.month

            pre_result = iai - credits_impot + cehr
            return period, -pre_result
                ### Suppression des seuils de non recouvrements
                #
                #    # (
                # (iai > P.seuil) * ( #Cas si l'impot est en dessus du seuil de recouvrement
                #     (pre_result < P.min/12) * (pre_result > 0) * iai * 0 +
                #     ((pre_result <= 0) + (pre_result >= P.min/12)) * (- pre_result)
                #     ) +
                # (iai <= P.seuil) * ( #Cas si l'impot est en dessous du seuil de recouvrement
                #     (pre_result < 0) * (-pre_result) + (pre_result >= 0) * 0 * iai) #on rend le crédit d'impot
                # )
    class virtual_vickrey(Reform.Variable):
        column = FloatCol(default = 0)
        reference = ir.irpp
        label = u""
        url = "http://www.impots.gouv.fr/portal/dgi/public/particuliers.impot?pageId=part_impot_revenu&espId=1&impot=IR&sfid=50"

        def function(self, simulation, period):
            period = period.this_month
            month_number = period.start.date.month
            virtual_vickrey = simulation.calculate('irpp_vickrey_mensuel', period) * month_number

            return period, virtual_vickrey

    class already_paid_vickrey(Reform.Variable):
        column = FloatCol(default = 0)
        reference = ir.irpp
        label = u""
        url = "http://www.impots.gouv.fr/portal/dgi/public/particuliers.impot?pageId=part_impot_revenu&espId=1&impot=IR&sfid=50"

        def function(self, simulation, period):
            period = period.this_month
            month_number = period.start.date.month

            already_paid = simulation.calculate('virtual_vickrey',period.offset(-1))*0
            if month_number>1 :
                already_paid = simulation.calculate('virtual_vickrey',period.offset(-1))
            return period, already_paid

    class vickrey_tax(Reform.Variable):
        column = FloatCol(default = 0)
        reference = ir.irpp
        label = u"Impôt sur le revenu des personnes physiques"
        url = "http://www.impots.gouv.fr/portal/dgi/public/particuliers.impot?pageId=part_impot_revenu&espId=1&impot=IR&sfid=50"

        def function(self, simulation, period):
            '''
            Vickrey tax amount to pay
            '''
            period = period.this_month
            virtual_vickrey = simulation.calculate('virtual_vickrey', period)
            already_paid = simulation.calculate('already_paid_vickrey', period)

            return period, virtual_vickrey - already_paid


    class revdisp_vickrey_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            rev_trav_holder = simulation.compute('rev_trav_mensuel', period)
            pen_holder = simulation.compute('pen_mensuel', period)
            rev_cap_holder = simulation.compute('rev_cap', period.this_year)
            psoc_holder = simulation.compute_add_divide('psoc_mensuel', period)
            ppe_holder = simulation.compute_add_divide('ppe', period)
            vickrey_tax_holder = simulation.compute_add('vickrey_tax', period.this_year)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder) /12
            rev_trav = self.sum_by_entity(rev_trav_holder)



            vickrey_tax = self.cast_from_entity_to_role(vickrey_tax_holder, role = VOUS)
            vickrey_tax = self.sum_by_entity(vickrey_tax)

            revdisp = rev_trav + pen + rev_cap + psoc + ppe + vickrey_tax # TODO: Tweak for the 860 neative disposable income.
            revdisp = (revdisp>0) * revdisp

            return period, revdisp



    class utility_ir_vickrey_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_vickrey_mensuel', period)
            utility = (-(((revdisp + 500)*12)) **-0.89)/12

            return period, utility



    class inverted_utility_ir_vickrey_mensuel(Reform.Variable):
        reference = mesures.revdisp
        label = u"utility_to_income"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            utility = simulation.calculate('utility_ir_vickrey_mensuel', period)


            return period, np.exp(
                (np.log(-utility*12))/-.89)/12


#### Equivalent scale utility
####

    class utility_es_ir_vickrey_mensuel(Reform.Variable):
        reference = mesures.revdisp
        #label = u"Revenu disponible du ménage"
        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.this_month
            revdisp = simulation.calculate('revdisp_vickrey_mensuel', period)
            uc = simulation.calculate('uc', period.this_year)
            utility = (-((12*(revdisp + 500))/uc) **-0.89)/12

            return period, utility


#
#     class impo_mensuel(Reform.Variable):
#         reference = mesures.impo
#         label = u"Impôts directs"
#         url = "http://fr.wikipedia.org/wiki/Imp%C3%B4t_direct"
#
#         def function(self, simulation, period):
#             '''
#             Impôts directs
#             '''
#             period = period.this_month
#             irpp_holder = simulation.compute('irpp_mensuel', period)
#             taxe_habitation = simulation.calculate('taxe_habitation', period.this_year)/12
#
#             irpp = self.cast_from_entity_to_role(irpp_holder, role = VOUS)
#             irpp = self.sum_by_entity(irpp)
#
#             return period, irpp + taxe_habitation
#



#
#     class utility_ir_mensuel(Reform.Variable):
#         reference = mesures.revdisp
#         #label = u"Revenu disponible du ménage"
#         def function(self, simulation, period):
#             '''
#             Revenu disponible - ménage
#             'men'
#             '''
#             period = period.this_month
#             revdisp = simulation.calculate('revdisp_mensuel_ir_mensuel', period)
#             utility = -(revdisp + 5000) **-0.89
#
#             return period, utility
#
#
#     class inverted_utility_ir_mensuel(Reform.Variable):
#         reference = mesures.revdisp
#         label = u"utility_to_income"
#         def function(self, simulation, period):
#             '''
#             Revenu disponible - ménage
#             'men'
#             '''
#             period = period.this_month
#             utility = simulation.calculate('utility_ir_mensuel', period)
#
#
#             return period, np.exp(
#                 (np.log(-utility))/-.87)
#
#
# #### Equivalent scale utility
# ####
#
#     class utility_es_ir_mensuel(Reform.Variable):
#         reference = mesures.revdisp
#         #label = u"Revenu disponible du ménage"
#         def function(self, simulation, period):
#             '''
#             Revenu disponible - ménage
#             'men'
#             '''
#             period = period.this_month
#             revdisp = simulation.calculate('revdisp_mensuel_ir_mensuel', period)
#             uc = simulation.calculate('uc', period.this_year)
#             utility = -((revdisp + 5000)/uc) **-0.89
#
#             return period, utility

    reform = Reform()
    return reform














