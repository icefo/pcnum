__author__ = 'adrien'
class DescriptionDeLObject:

    def afficher(self):

        print("La valeur actuelle est %s" % self.un_attribut)

    def modifier(self, valeur):

        self.un_attribut = valeur * 2


dict = {"genre":("truc","chose"), "machin":("chose",)}
for k, v in dict.items():
    for values in v:
        print(k,values)


#print(dict)