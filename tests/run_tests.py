#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_tests.py — proves the auditor CATCHES problems, not just that it passes
clean rounds. Runs pft_round_audit against the clean fixtures (expected
CONSISTENT) and against each deliberately-broken fixture in tests/broken/
(expected INCONSISTENT, with the specific check that must FAIL).

A verifier is only trustworthy if it fails when it should. Run:

    python3 tests/run_tests.py

Exits 0 only if every case behaves exactly as expected.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AUDIT = os.path.join(ROOT, "pft_round_audit.py")

# case dir -> (expected verdict, check that must be FAIL or None)
CASES = {
    "../fixtures":                 ("CONSISTENT",   None),
    "broken/churn_violation":      ("INCONSISTENT", "C5c_churn_gap"),
    "broken/eligibility_breach":   ("INCONSISTENT", "C5b_eligibility"),
    "broken/wrong_unl_size":       ("INCONSISTENT", "C5a_unl_size"),
    "broken/out_of_range":         ("INCONSISTENT", "C7_component_bounds"),
    "broken/missing_artifact":     ("INCONSISTENT", "C1_artifacts_present"),
    "broken/duplicate_entry":      ("INCONSISTENT", "C6_no_duplicates"),
    "broken/key_mismatch":         ("INCONSISTENT", "C8_evidence_keys_match"),
}

def run_case(rel):
    d = os.path.join(HERE, rel)
    out = subprocess.run(
        [sys.executable, AUDIT, "--round", "12", "--from-dir", d, "--out-dir", "/tmp"],
        capture_output=True, text=True)
    obj = json.load(open("/tmp/round-12-audit.json"))
    return obj

def main():
    passed = 0
    for rel, (want_verdict, want_fail) in CASES.items():
        obj = run_case(rel)
        verdict = obj["verdict"]
        checks = {c["id"]: c["status"] for c in obj["checks"]}
        ok = verdict == want_verdict
        detail = f"verdict={verdict}"
        if want_fail:
            fail_ok = checks.get(want_fail) == "FAIL"
            ok = ok and fail_ok
            detail += f", {want_fail}={checks.get(want_fail)}"
        mark = "PASS" if ok else "XXXX"
        name = rel.replace("broken/", "").replace("../", "")
        print(f"[{mark}] {name:22} expected {want_verdict:12} | {detail}")
        passed += ok
    total = len(CASES)
    print(f"\n{passed}/{total} test cases behaved as expected.")
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
