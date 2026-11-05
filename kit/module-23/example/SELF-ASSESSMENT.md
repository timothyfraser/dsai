# Self-assessment: the four columns

| Column | The question | Our answer | Evidence |
|---|---|---|---|
| Build | Did an agent build it against a contract we wrote? | Yes, against SPEC.md, one box at a time | [contract](SPEC.md) |
| Verify | How do we know it works, and that it is the right thing? | Smoke test and error limit; the planner tried it on three streets | [check output](runs/check_output.txt) |
| Productionise | Where does it run, why there, and what happens when it sleeps or breaks? | Scale-to-zero API; the page says "waking up" | [cold start](runs/cold_start.txt) |
| Explain | Can we say what it is, why this architecture, what it costs, where it fails? | The stand-up, given with no laptop | [stand-up](STANDUP.md) |
