# V37.1 — Tests réels Linux

## test_openpdf_v371
```
test_collision (test_openpdf_v371.TestReservation371.test_collision) ... ok
test_diagnostics_read_only (test_openpdf_v371.TestReservation371.test_diagnostics_read_only) ... ok
test_invalid_json (test_openpdf_v371.TestReservation371.test_invalid_json) ... ok
test_legacy (test_openpdf_v371.TestReservation371.test_legacy) ... ok
test_modified_lock_preserved (test_openpdf_v371.TestReservation371.test_modified_lock_preserved) ... ok
test_owner_token (test_openpdf_v371.TestReservation371.test_owner_token) ... ok
test_remote_host_not_pid_checked (test_openpdf_v371.TestReservation371.test_remote_host_not_pid_checked) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.016s

OK

```
## test_openpdf_v370
```
test_absent (test_openpdf_v370.TestLockDiagnostics.test_absent) ... ok
test_existing_process (test_openpdf_v370.TestLockDiagnostics.test_existing_process) ... ok
test_invalid (test_openpdf_v370.TestLockDiagnostics.test_invalid) ... ok
test_no_lock_mutation (test_openpdf_v370.TestLockDiagnostics.test_no_lock_mutation) ... ok
test_pid_never_stolen (test_openpdf_v370.TestLockDiagnostics.test_pid_never_stolen) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.003s

OK

```
## test_openpdf_v367
```
test_concurrent_process_blocked (test_openpdf_v367.ReservationTests.test_concurrent_process_blocked) ... /usr/lib/python3.13/multiprocessing/popen_fork.py:67: DeprecationWarning: This process (pid=131813) is multi-threaded, use of fork() may lead to deadlocks in the child.
  self.pid = os.fork()
ok
test_existing_lock_not_removed (test_openpdf_v367.ReservationTests.test_existing_lock_not_removed) ... ok
test_release_after_failure (test_openpdf_v367.ReservationTests.test_release_after_failure) ... ok
test_release_after_success (test_openpdf_v367.ReservationTests.test_release_after_success) ... ok
test_split_collision_preserves_existing (test_openpdf_v367.ReservationTests.test_split_collision_preserves_existing) ... ok
test_split_lock_cleanup (test_openpdf_v367.ReservationTests.test_split_lock_cleanup) ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.063s

OK

```

Aucun test natif Windows ou GUI exécuté. Verrous conservés en cas de remplacement de métadonnées.
