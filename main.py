import procset

proc = procset.ProcSet("1356")
proc.show()

proc2 = procset.ProcSet("89")
proc2.show()

proc3 = proc.union(proc2)
proc3.show()