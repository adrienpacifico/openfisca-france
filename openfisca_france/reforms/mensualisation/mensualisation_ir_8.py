# -*- coding: utf-8 -*-

from __future__ import division

from numpy import (datetime64, logical_and as and_, logical_not as not_, logical_or as or_, logical_xor as xor_,
    maximum as max_, minimum as min_, round)
from openfisca_core import columns, formulas, reforms
from openfisca_core import simulations, periods

from ... import entities
from ...model.base import QUIFOY
from ...model.prelevements_obligatoires.impot_revenu import ir
from ...model import mesures
from ... import model
from ...model.base import *



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



            lambda_compensation = ((impot_annuel == 0) & (impot_mensuel == 0)) * 0 + ~((impot_annuel == 0) & (impot_mensuel == 0)) * lambda_compensation


            ## traiter le cas ou irpp annuel = 0

            return period, ((impot_mensuel*12)/impot_annuel) - 12
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
            print period
            impot_mensuel = -simulation.calculate_add("irpp_mensuel", period)
            impot_annuel = -simulation.calculate_add("irpp", period.this_year)
            lambda_compensation = -simulation.calculate("irpp", period.this_year)



            compensated_irpp = impot_mensuel/(12 + lambda_compensation)


            ## traiter le cas ou irpp annuel = 0

            return period, compensated_irpp


    class impo(Reform.Variable):
        reference = mesures.impo
        label = u"Impôts directs"
        url = "http://fr.wikipedia.org/wiki/Imp%C3%B4t_direct"

        def function(self, simulation, period):
            '''
            Impôts directs
            '''
            period = period.this_month
            irpp_holder = simulation.compute_add('irpp_mensuel', period)
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

    class rev_trav(Reform.Variable):
        reference = mesures.rev_trav
        label = u"Revenus du travail (salariés et non salariés)"
        url = "http://fr.wikipedia.org/wiki/Revenu_du_travail"

        def function(self, simulation, period):
            '''
            Revenu du travail
            '''
            period = period.this_month
            rev_sal = simulation.calculate('rev_sal', period.this_month)
            #rag = simulation.calculate('rag', period)
            #ric = simulation.calculate('ric', period)
            #rnc = simulation.calculate('rnc', period)

            return period, rev_sal #+ rag + ric + rnc

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




#ARS  TODO: Mettre l'ARS en mensualisé sur toute l'année ?

    from ...model.prestations.prestations_familiales.base_ressource import nb_enf

    class ars(Reform.Variable):  #TODO: Pourquoi en encotobre et pas en aout ?
        reference = model.prestations.prestations_familiales.ars.ars
        label = u"Allocation de rentrée scolaire"
        url = "http://vosdroits.service-public.fr/particuliers/F1878.xhtml"

        def function(self, simulation, period):
            '''
            Allocation de rentrée scolaire brute de CRDS
            '''
            period_br = period.this_year
            period = period.start.offset('first-of', 'year').offset(9, 'month').period('month')
            age_holder = simulation.compute('age', period)
            af_nbenf = simulation.calculate('af_nbenf', period)
            smic55_holder = simulation.compute('smic55', period)
            br_pf = simulation.calculate('br_pf', period_br.start.offset('first-of', 'month').period('month'))
            P = simulation.legislation_at(period.start).fam
            # TODO: convention sur la mensualisation
            # On tient compte du fait qu'en cas de léger dépassement du plafond, une allocation dégressive
            # (appelée allocation différentielle), calculée en fonction des revenus, peut être versée.
            age = self.split_by_roles(age_holder, roles = ENFS)
            smic55 = self.split_by_roles(smic55_holder, roles = ENFS)

            bmaf = P.af.bmaf
            # On doit prendre l'âge en septembre
            enf_05 = nb_enf(age, smic55, P.ars.agep - 1, P.ars.agep - 1)  # 5 ans et 6 ans avant le 31 décembre
            # enf_05 = 0
            # Un enfant scolarisé qui n'a pas encore atteint l'âge de 6 ans
            # avant le 1er février 2012 peut donner droit à l'ARS à condition qu'il
            # soit inscrit à l'école primaire. Il faudra alors présenter un
            # certificat de scolarité.
            enf_primaire = enf_05 + nb_enf(age, smic55, P.ars.agep, P.ars.agec - 1)
            enf_college = nb_enf(age, smic55, P.ars.agec, P.ars.agel - 1)
            enf_lycee = nb_enf(age, smic55, P.ars.agel, P.ars.ages)

            arsnbenf = enf_primaire + enf_college + enf_lycee

            # Plafond en fonction du nb d'enfants A CHARGE (Cf. article R543)
            ars_plaf_res = P.ars.plaf * (1 + af_nbenf * P.ars.plaf_enf_supp)
            arsbase = bmaf * (P.ars.tx0610 * enf_primaire +
                             P.ars.tx1114 * enf_college +
                             P.ars.tx1518 * enf_lycee)
            # Forme de l'ARS  en fonction des enfants a*n - (rev-plaf)/n
            # ars_diff = (ars_plaf_res + arsbase - br_pf) / arsnbenf
            ars = (arsnbenf > 0) * max_(0, arsbase - max_(0, (br_pf - ars_plaf_res) / max_(1, arsnbenf)))
            # Calcul net de crds : ars_net = (P.ars.enf0610 * enf_primaire + P.ars.enf1114 * enf_college + P.ars.enf1518 * enf_lycee)

            return period, ars * (ars >= P.ars.seuil_nv) #previously period_br instead

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
            #aeeh = simulation.calculate('aeeh', period.this_year)  #paiement mensuel pourquoi en annuel dans les presta ?
            paje = simulation.calculate_add('paje', period)
            asf = simulation.calculate_add('asf', period)
            crds_pfam = simulation.calculate('crds_pfam', period)

            return period, af + cf + ars + paje + asf + crds_pfam #+ aeeh





####Neutralisations pour plus tard
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['abat_spe']))
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['ars']))
    Reform.add_column(formulas.neutralize_column(tax_benefit_system.column_by_name['aeeh']))





    class psoc(Reform.Variable):
        reference = mesures.psoc
        label = u"Total des prestations sociales"
        url = "http://fr.wikipedia.org/wiki/Prestation_sociale"

        def function(self, simulation, period):
            '''
            Prestations sociales
            '''
            period = period.this_month
            pfam = simulation.calculate('pfam', period)
            mini = simulation.calculate('mini', period)
            aides_logement = simulation.calculate_add_divide('aides_logement', period)

            return period, pfam + mini + aides_logement


    class revdisp(Reform.Variable):
        reference = mesures.revdisp
        label = u"Revenu disponible du ménage"
        url = "http://fr.wikipedia.org/wiki/Revenu_disponible"

        def function(self, simulation, period):
            '''
            Revenu disponible - ménage
            'men'
            '''
            period = period.start.period('year').offset('first-of')
            rev_trav_holder = simulation.compute_add('rev_trav', period)
            pen_holder = simulation.compute('pen', period)
            rev_cap_holder = simulation.compute('rev_cap', period)
            psoc_holder = simulation.compute_add_divide('psoc', period) #to change !
            ppe_holder = simulation.compute_add_divide('ppe', period)
            impo = simulation.calculate('impo', period)

            pen = self.sum_by_entity(pen_holder)
            ppe = self.cast_from_entity_to_role(ppe_holder, role = VOUS)
            ppe = self.sum_by_entity(ppe)
            psoc = self.cast_from_entity_to_role(psoc_holder, role = CHEF)
            psoc = self.sum_by_entity(psoc)
            rev_cap = self.sum_by_entity(rev_cap_holder)
            rev_trav = self.sum_by_entity(rev_trav_holder)

            return period, rev_trav + pen + rev_cap + psoc + ppe + impo




    class mini(Reform.Variable):
        reference = mesures.mini
        label = u"Minima sociaux"
        url = "http://fr.wikipedia.org/wiki/Minima_sociaux"

        def function(self, simulation, period):
            '''
            Minima sociaux
            '''
            period = period.this_month
            aspa = simulation.calculate_add('aspa', period)
            aah_holder = simulation.compute_add('aah', period)
            caah_holder = simulation.compute_add('caah', period)
            asi = simulation.calculate_add('asi', period)
            rsa = simulation.calculate_add('rsa', period)
            #aefa = simulation.calculate('aefa', period)
            api = simulation.calculate('api', period)
            ass = simulation.calculate_add('ass', period)
            psa = simulation.calculate_add('psa', period)

            aah = self.sum_by_entity(aah_holder)
            caah = self.sum_by_entity(caah_holder)

            return period, aspa + aah + caah + asi + rsa  + api + ass + psa #+ aefa



    reform = Reform()
    return reform
