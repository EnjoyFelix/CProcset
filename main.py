import procset

proc = procset.ProcSet("11-45 88-189")
print(proc)

proc2 = procset.ProcSet("33-67 79-103")
print(repr(proc))

proc3 = proc.union(proc2)
print(proc3)