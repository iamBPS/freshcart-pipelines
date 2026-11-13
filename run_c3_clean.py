import subprocess
import sys
import site
from pathlib import Path

root = Path(__file__).resolve().parent
mage = (
    Path(site.getuserbase())
    / f"Python{sys.version_info.major}{sys.version_info.minor}"
    / "Scripts" / "mage.exe"
)

command = [
    str(mage), "run", "iris_project",
    "iris_classifier", "--test"
]

result = subprocess.run(
    command,
    cwd=root,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace"
)

output = (result.stdout or "") + "\n" + (result.stderr or "")

(root / "c3_full_log.txt").write_text(output, encoding="utf-8")

print("\n========== C3 PIPELINE RESULTS ==========\n")

for line in output.splitlines():
    if any(term in line for term in [
        "tests passed",
        "Maximum tree depth:",
        "Test accuracy:",
        "CONFUSION MATRIX",
        "CLASSIFICATION METRICS",
        "Predictions saved to:",
        "Total predictions:",
        "Pipeline run completed",
        "FAIL:",
        "AssertionError",
        "Exception:"
    ]):
        print(line)

if result.returncode != 0:
    print("\nPIPELINE FAILED. Full error saved in c3_full_log.txt")
    sys.exit(result.returncode)

print("\nC3 PIPELINE SUCCESSFUL")
