import procset
import tracemalloc

filters = [
    tracemalloc.Filter(False, tracemalloc.__file__),
    tracemalloc.Filter(False, '<frozen importlib._bootstrap>'),
    tracemalloc.Filter(False, '<unknown>'),
    tracemalloc.Filter(False, '/usr/lib/python'),  # Ignorer les bibliothèques Python standard
    tracemalloc.Filter(False, '/usr/local/lib/python'),  # Ignorer les bibliothèques Python installées localement
]


# imprime les infos des differences des snapshots
def print_diff(snapshot0, snapshot1):
    #snap_diff = snapshot1.compare_to(snapshot0, 'lineno', False)
    stats = snapshot1.statistics('traceback')
    print("\n[ Allocations restantes : %i ]" % len(stats))
    for stat in stats:
        print("\n", "==="*30, "\n", stat)
        print(f"Traceback (most recent call last):")
        for line in stat.traceback.format():
            print(line)

# tests sur la création de procset
def test_creation():
    snapshot0 = tracemalloc.take_snapshot()

    p = procset.ProcSet()
    p1 = procset.ProcSet(1)
    p2 = procset.ProcSet(1,2)
    p3 = procset.ProcSet(())
    p4 = procset.ProcSet((1,2))
    p5 = procset.ProcSet([])
    p6 = procset.ProcSet([1,2])
    p7 = procset.ProcSet({1,2})

    del(p)
    del(p1)
    del(p2)
    del(p3)
    del(p4)
    del(p5)
    del(p6)
    del(p7)
    snapshot1 = tracemalloc.take_snapshot()

    # application des filtres et affichage
    snapshot0 = snapshot0.filter_traces(filters)
    snapshot1 = snapshot1.filter_traces(filters)
    print_diff(snapshot0, snapshot1)

# tests sur des échecs lors de la création de procset
def test_creation_echec():
    return

# tests sur les unions:     
# les opérations ensemblistes possèdent toutes la même base, pas la peine de faire des tests pour tout les opérateurs 
def test_union():
    snapshot0 = tracemalloc.take_snapshot()

    p = procset.ProcSet()
    p1 = procset.ProcSet((1,2), (5,7), (11,12), (14,15), (18,22), 25)
    p2 = procset.ProcSet((3,4), 8, (10,11), (15,16), 19, (21,24))

    pu = p | p
    pu1 = p | p1
    pu2 = p | p2

    pu3 = p2.union((1,2))
    pu4 = p2.union([1,2])
    pu5 = p2.union({1,2})

    pi = procset.ProcSet()
    pi1 = procset.ProcSet((1,2), (5,7), (11,12), (14,15), (18,22), 25)
    pi2 = procset.ProcSet((3,4), 8, (10,11), (15,16), 19, (21,24))

    pi |= pi
    pi1 |= p
    pi1 |= p2

    pi2.update([])
    pi2.update([1,2])
    pi2.update(50)

    del(p)
    del(p1)
    del(p2)
    del(pu)
    del(pu1)
    del(pu2)
    del(pu3)
    del(pu4)
    del(pu5)
    del(pi)   
    del(pi1)
    del(pi2)
    
    snapshot1 = tracemalloc.take_snapshot()

    # application des filtres et affichage
    snapshot0 = snapshot0.filter_traces(filters)
    snapshot1 = snapshot1.filter_traces(filters)
    print_diff(snapshot0, snapshot1)



if __name__ == '__main__':
    # debut tracemalloc
    tracemalloc.start()

    test_creation()

    tracemalloc.clear_traces()

    test_creation_echec()
    test_union()

    # fin tracemalloc
    tracemalloc.stop()