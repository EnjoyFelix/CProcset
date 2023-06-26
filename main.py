import procset

proc1 = procset.ProcSet("11-45 88-100")
print("proc1 : \t\t\t" + repr(proc1))

proc2 = procset.ProcSet("33-54 63-74 79-94")
print("proc2 : \t\t\t" + repr(proc2))

procUnion = proc1.union(proc2)
print("union : \t\t\t" + repr(procUnion))

procIntersection = proc1.intersection(proc2)
print("intersection : \t\t\t" + repr(procIntersection))

procDifference = proc1.difference(proc2)
print("difference : \t\t\t" + repr(procDifference))

procDiffSymmetric = proc1.symmetric_difference(proc2)
print("symmetric difference : \t\t" + repr(procDiffSymmetric))


procEmpty = procset.ProcSet()
print("emptyProcset : " + repr(procEmpty))
