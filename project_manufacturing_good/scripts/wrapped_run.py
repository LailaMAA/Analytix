import subprocess
import sys

with open("run_log.txt", "w", encoding="utf-8") as f:
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_batch_predictions.py"],
            cwd=".",
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
    except Exception as e:
        f.write(f"Wrapper Error: {e}")

print("Done. Log saved to run_log.txt")
