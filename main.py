import procset

proc1 = procset.ProcSet("11-45 88-100")
print("repr : " + repr(proc1))
print("str  : " + str(proc1))
print(f"proc1 : {proc1}")

proc2 = procset.ProcSet("33-54 63-74 79-94")
print(f"proc2 : {proc2}")

procUnion = proc1.union(proc2)
print(f"union : {procUnion}")

procIntersection = proc1.intersection(proc2)
print(f"intersection : {procIntersection}")

procDifference = proc1.difference(proc2)
print(f"difference : {procDifference}")

procDiffSymmetric = proc1.symmetric_difference(proc2)
print(f"symmetric-difference : {procDiffSymmetric}")

procEmpty = procset.ProcSet()
print(f"empty : {procEmpty}")
