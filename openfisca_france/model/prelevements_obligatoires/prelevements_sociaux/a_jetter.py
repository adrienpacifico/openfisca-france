print simulation.legislation_at(period.start).ir.decote.seuil_celib

OUT : 1135

print simulation.legislation_at(period.start).ir.bareme

OUT :

bareme ir MarginalRateTaxScale: bareme
- 0.0  0.0
- 9690.0  0.14
- 26764.0  0.3
- 71754.0  0.41
- 151956.0  0.45

reform_simulation.change_legislation_at(start = 2012, stop = 2015).decote.seuil_celib(value = 2056)
print imulation.legislation_at(period.start).ir.decote.seuil_celib

OUT : 20156

reform_simulation.change_legislation_at(start = 2012, stop = 2015).ir.bareme(bareme = [(0,0),
                                                                                        (9650, 36),
                                                                                        (10000000,75),
                                                                            )
print simulation.legislation_at(period.start).ir.bareme


OUT :
bareme ir MarginalRateTaxScale: bareme
- 0.0  0.0
- 9650.0  0.36
- 10000000 0.75