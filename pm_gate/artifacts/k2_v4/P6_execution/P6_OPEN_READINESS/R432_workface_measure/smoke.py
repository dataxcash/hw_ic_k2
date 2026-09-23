import time, json, os
from ortools.sat.python import cp_model
out={"python":os.sys.version.split()[0]}
import ortools
out["ortools"]=getattr(ortools,"__version__","?")
# --- SAT toy ---
m=cp_model.CpModel(); L=4; P=4
x={p:m.NewIntVar(0,L-1,f"lane_p{p}") for p in range(P)}
m.AddAllDifferent([x[p] for p in range(P)])
m.Add(x[0] < x[1])
s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=5.0
t0=time.time(); st=s.Solve(m); dt=(time.time()-t0)*1000
m.ExportToFile("sat_model.textproto")
out["SAT"]={"status":s.StatusName(st),"wall_ms":round(dt,1),
            "assign":{f"p{p}":s.Value(x[p]) for p in range(P)},
            "cert_model_file":"sat_model.textproto","cert_model_bytes":os.path.getsize("sat_model.textproto")}
# --- UNSAT via assumptions -> unsat core (machine-checkable certificate) ---
m2=cp_model.CpModel(); z=[m2.NewIntVar(0,L-1,f"z{i}") for i in range(P)]
m2.AddAllDifferent(z)
a1=m2.NewBoolVar("a_z0_eq_z1"); a2=m2.NewBoolVar("a_z2_eq_z3")
m2.Add(z[0]==z[1]).OnlyEnforceIf(a1)
m2.Add(z[2]==z[3]).OnlyEnforceIf(a2)
m2.AddAssumptions([a1,a2])
s2=cp_model.CpSolver(); s2.parameters.max_time_in_seconds=5.0
t0=time.time(); st2=s2.Solve(m2); dt=(time.time()-t0)*1000
m2.ExportToFile("unsat_model.textproto")
idx=s2.SufficientAssumptionsForInfeasibility() if st2==cp_model.INFEASIBLE else []
core=[m2.Proto().variables[i].name for i in idx] if st2==cp_model.INFEASIBLE else None
rp=s2.ResponseProto()
out["UNSAT"]={"status":s2.StatusName(st2),"wall_ms":round(dt,1),
  "is_proven_infeasible":st2==cp_model.INFEASIBLE,"unsat_core":core,
  "cert_model_file":"unsat_model.textproto",
  "proof_stats":{"num_conflicts":rp.num_conflicts,"num_branches":rp.num_branches,
                 "solve_log_lines":len(rp.solve_log.splitlines())}}
print(json.dumps(out,ensure_ascii=False,indent=1))
json.dump(out,open("smoke_result.json","w"),ensure_ascii=False,indent=1)
