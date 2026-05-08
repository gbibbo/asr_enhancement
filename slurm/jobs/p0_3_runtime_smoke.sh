#!/usr/bin/env bash
#SBATCH --job-name=robust_asr_p0_3_runtime_smoke
#SBATCH --output=/mnt/fast/nobackup/users/gb0048/asr_enhancement/artifacts/robust_asr/runtime_smoke/p0_3_runtime_smoke_%j.out
#SBATCH --error=/mnt/fast/nobackup/users/gb0048/asr_enhancement/artifacts/robust_asr/runtime_smoke/p0_3_runtime_smoke_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -euo pipefail

REPO="/mnt/fast/nobackup/users/gb0048/asr_enhancement"
CONTAINER="/mnt/fast/nobackup/users/gb0048/opro2/pytorch_2.1_cuda12.sif"

cd "$REPO"

apptainer exec \
  --env ASR_REPO_ROOT="$REPO" \
  "$CONTAINER" \
  python3 - <<'PYEOF'
import json, platform, socket, sys

results = {
    "python_version": sys.version.split()[0],
    "host": socket.gethostname(),
    "platform": platform.platform(),
    "imports": {},
}

ok_py311 = sys.version_info[:2] == (3, 11)
results["python_3_11_ok"] = ok_py311
print(f"PYTHON_VERSION={results['python_version']}")
print(f"HOST={results['host']}")

required = [
    "torch", "transformers", "peft", "ctranslate2",
    "faster_whisper", "librosa", "numpy", "pandas",
    "pyarrow", "yaml", "pytest",
]
for mod in required:
    try:
        m = __import__(mod)
        v = getattr(m, "__version__", "unknown")
        results["imports"][mod] = {"ok": True, "version": v}
        print(f"IMPORT_OK {mod} {v}")
    except Exception as e:
        results["imports"][mod] = {"ok": False, "error": repr(e)}
        print(f"IMPORT_FAIL {mod} {e!r}")

try:
    import torch
    results["torch_cuda_available"] = bool(torch.cuda.is_available())
    print(f"TORCH_CUDA_AVAILABLE={results['torch_cuda_available']}")
except Exception as e:
    results["torch_cuda_available"] = None
    print(f"TORCH_CUDA_PROBE_FAIL {e!r}")

router_pick, router_fallback = None, False
for cand in ["lightgbm", "xgboost"]:
    try:
        __import__(cand)
        router_pick = cand
        break
    except Exception:
        continue
if router_pick is None:
    try:
        from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: F401
        router_pick = "sklearn.HistGradientBoostingRegressor"
        router_fallback = True
    except Exception as e:
        results["router_pick_error"] = repr(e)
results["router_pick"] = router_pick
results["router_fallback_sklearn"] = router_fallback
print(f"ROUTER_PICK={router_pick} FALLBACK_SKLEARN={router_fallback}")

all_required_ok = all(results["imports"][m]["ok"] for m in required)
results["all_required_imports_ok"] = all_required_ok
results["smoke_ok"] = ok_py311 and all_required_ok and (router_pick is not None)

print("RUNTIME_SMOKE_RESULTS_BEGIN")
print(json.dumps(results, sort_keys=True, indent=2))
print("RUNTIME_SMOKE_RESULTS_END")

if not results["smoke_ok"]:
    sys.exit(1)
print("OK_RUNTIME_SMOKE")
PYEOF
