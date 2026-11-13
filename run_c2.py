import csv
import json
import re
import site
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

mage_exe = (
    Path(site.getuserbase())
    / f"Python{sys.version_info.major}{sys.version_info.minor}"
    / "Scripts"
    / "mage.exe"
)

if not mage_exe.exists():
    raise SystemExit(f"Mage executable not found: {mage_exe}")

results = []

for depth in range(1, 6):
    print("\n" + "=" * 55)
    print(f"RUNNING MAX DEPTH: {depth}")
    print("=" * 55)

    output_file = ROOT / "iris_predictions.csv"
    if output_file.exists():
        output_file.unlink()

    # Build JSON and pass it directly through Python subprocess.
    runtime_json = json.dumps({"max_depth": depth})

    command = [
        str(mage_exe),
        "run",
        "iris_project",
        "iris_classifier",
        "--test",
        "--runtime-vars",
        runtime_json,
    ]

    process = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (process.stdout or "") + "\n" + (process.stderr or "")
    print(output)

    # Extract actual depth used by the model.
    depth_match = re.search(
        r"Maximum tree depth:\s*(\d+)", output
    )

    accuracy_match = re.search(
        r"Test accuracy:\s*([0-9.]+)", output
    )

    actual_depth = (
        int(depth_match.group(1))
        if depth_match else None
    )

    accuracy = (
        float(accuracy_match.group(1))
        if accuracy_match else None
    )

    # Stop instead of recording misleading results.
    if actual_depth != depth:
        print(
            f"\nERROR: Requested depth {depth}, "
            f"but model used {actual_depth}."
        )
        raise SystemExit(2)

    test_passed = (
        process.returncode == 0
        and "Pipeline run completed." in output
    )

    csv_created = output_file.exists()

    results.append({
        "Max_Depth": depth,
        "Actual_Depth": actual_depth,
        "Accuracy": accuracy,
        "Test_Passed": test_passed,
        "CSV_Created": csv_created,
    })

    (ROOT / f"c2_depth_{depth}.log").write_text(
        output, encoding="utf-8"
    )

# Save results.
with (ROOT / "c2_results.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.DictWriter(file, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print("\n" + "=" * 65)
print("FINAL C2 RESULTS")
print("=" * 65)

for row in results:
    print(
        f"Depth: {row['Max_Depth']} | "
        f"Accuracy: {row['Accuracy']} | "
        f"Test passed: {row['Test_Passed']} | "
        f"CSV created: {row['CSV_Created']}"
    )

print("\nSaved: c2_results.csv")