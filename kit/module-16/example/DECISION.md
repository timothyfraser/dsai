# Decision: the next job for the small model

## Next job
Make test_kpa_to_psi pass in convert.py, the reverse of the job we already ran. It is one function, one test file and one check command, so the contract below bounds it.

## Rejected
- Add a new unit converter with its own tests. The model would have to write the tests as well as the code, and the contract cannot say what a correct test is, so nothing bounds it yet.
- Rename convert.py across the whole toy project. The edit touches many files, and the contract allows one file to edit, so it cannot bound the job yet.

## Reason
The job has one failing test, one file to edit and a check command that exits 0 when it is done. The model can tell for itself when to stop, and we can tell from the check whether it worked.

## Evidence
run 1: PASS, 38 s
run 2: PASS, 41 s
run 3: PASS, 36 s
without TASK block: FAIL, 95 s
Three runs with the contract passed. The run without it wandered and did not finish.

## Local or cloud
Choice: local
Because: the job is small and bounded, and the check runs on our own machine in under a minute.

## TASK

- GOAL: make tests/test_convert.py::test_kpa_to_psi pass
- FILE YOU MAY EDIT: convert.py
- FILES YOU MAY READ: convert.py and tests/test_convert.py, nothing else
- CHECK COMMAND: python3 -m unittest tests.test_convert
- DONE WHEN: the CHECK COMMAND exits 0.
