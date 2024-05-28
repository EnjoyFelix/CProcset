import tracemalloc
import gc

import procset


# liste des filtres pour enlever les traces parasites
filters = [
    tracemalloc.Filter(False, tracemalloc.__file__),
    tracemalloc.Filter(False, '<frozen importlib._bootstrap>'),
    tracemalloc.Filter(False, '<unknown>'),
    tracemalloc.Filter(False, '/usr/lib/python'),  # Ignorer les bibliothèques Python standard
    tracemalloc.Filter(False, '/usr/local/lib/python'),  # Ignorer les bibliothèques Python installées localement
]

# Debut du flicage 
tracemalloc.start(2)

# snapshot de l'état initial de la mémoire
snapshot1 = tracemalloc.take_snapshot()

p = procset.ProcSet()
p1 = procset.ProcSet((1,2), (5,7), (11,12), (14,15), (18,22), 25)

# snapshot aprés avoir faire des trucs
snapshot2 = tracemalloc.take_snapshot()

del(p1)
del(p)
gc.collect()

# snapshot de l'état final
snapshot3 = tracemalloc.take_snapshot()


# J'applique les filtres
snapshot1 = snapshot1.filter_traces(filters)
snapshot2 = snapshot2.filter_traces(filters)
snapshot3 = snapshot3.filter_traces(filters)
    
# Comparer les instantanés pour voir les allocations supplémentaires
stats_alloc = snapshot2.compare_to(snapshot1, 'lineno', False)
print("[ Statistiques d'allocations ]")
for stat in stats_alloc:
    print(stat)

# Comparer les instantanés pour voir les libérations
stats_free = snapshot3.compare_to(snapshot2, 'lineno', False)
print("\n[ Statistiques de libérations ]")
for stat in stats_free:
    print(stat)

# Afficher les allocations restantes après libération
top_stats = snapshot3.statistics('traceback')
print("\n[ Allocations restantes après libération: %i ]" % len(top_stats))
for stat in top_stats[:10]:
    print("\n", "==="*30, "\n", stat)
    print(f"Traceback (most recent call last):")
    for line in stat.traceback.format():
        print(line)

# Arrêter tracemalloc
tracemalloc.stop()