import procset

proc = procset.ProcSet("19789-376 5546-66534")
proc.show()

proc2 = procset.ProcSet("8-9")
proc2.show()

proc3 = proc.union(proc2)
proc3.show()