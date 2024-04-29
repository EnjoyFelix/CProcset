import procset

print("Creating procset")

# création d'un proceset
p = procset.ProcSet((1,2), (5,7), (11,12), (14,15), (18,22), 25)

# Affichage du procset
print(p)

# On autorise le procset a se faire GC
p = 0
