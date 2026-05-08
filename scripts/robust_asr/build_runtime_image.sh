#!/usr/bin/env bash
# robust_asr runtime image builder
#
# Builds the robust_asr Apptainer image at the path authorized by
# configs/robust_asr/reuse_policy_v1.yaml (P0.3 Option A scope-change).
#
# This script is intended to be invoked from inside a Slurm job on an
# aisurrey compute node by slurm/jobs/p0_3_build_runtime_image.sh.
# It also runs locally for non-build operations (sha256, inspect) but
# the actual `apptainer build` step typically requires a build host.
#
# Build attempt chain (deterministic, fall through on each failure):
#   1. apptainer build --fakeroot OUT RECIPE
#   2. apptainer build OUT RECIPE
#   3. apptainer build --sandbox SBX RECIPE  &&  apptainer build OUT SBX
#   4. exit 1 with marker BLOCKED_RUNTIME

set -euo pipefail

REPO="${ASR_REPO_ROOT:-/mnt/fast/nobackup/users/gb0048/asr_enhancement}"
RECIPE="${REPO}/configs/robust_asr/runtime/apptainer_robust_asr_v1.def"
RUNTIME_DIR="/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime"
OUT_SIF="${RUNTIME_DIR}/robust_asr_py311_cuda12.sif"
SBX_DIR="${RUNTIME_DIR}/build_cache/sandbox"
LOG_DIR="${RUNTIME_DIR}/build_logs"

mkdir -p "${RUNTIME_DIR}" "${LOG_DIR}" "${RUNTIME_DIR}/build_cache"

if [[ ! -f "${RECIPE}" ]]; then
    echo "ERROR: recipe not found: ${RECIPE}" >&2
    exit 2
fi

RECIPE_SHA256="$(sha256sum "${RECIPE}" | awk '{print $1}')"
BUILDER_VERSION="$(apptainer --version 2>&1 || echo 'apptainer not found')"
BUILD_HOST="$(hostname)"
BUILD_STARTED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "BUILD_HOST=${BUILD_HOST}"
echo "BUILDER_VERSION=${BUILDER_VERSION}"
echo "RECIPE=${RECIPE}"
echo "RECIPE_SHA256=${RECIPE_SHA256}"
echo "OUT_SIF=${OUT_SIF}"
echo "BUILD_STARTED_AT_UTC=${BUILD_STARTED_AT_UTC}"

if [[ -f "${OUT_SIF}" ]]; then
    echo "ERROR: output SIF already exists at ${OUT_SIF}." >&2
    echo "       reuse_policy classifies it as container_image/exec_only;" >&2
    echo "       refusing to overwrite. Remove explicitly if rebuild is intended." >&2
    exit 3
fi

build_attempt() {
    local label="$1"; shift
    echo "BUILD_ATTEMPT_BEGIN ${label}"
    local rc=0
    "$@" || rc=$?
    echo "BUILD_ATTEMPT_END ${label} rc=${rc}"
    return ${rc}
}

BUILD_RC=99
BUILD_METHOD="none"

if build_attempt fakeroot apptainer build --fakeroot "${OUT_SIF}" "${RECIPE}"; then
    BUILD_RC=0
    BUILD_METHOD="fakeroot"
elif build_attempt plain apptainer build "${OUT_SIF}" "${RECIPE}"; then
    BUILD_RC=0
    BUILD_METHOD="plain"
else
    rm -rf "${SBX_DIR}"
    if build_attempt sandbox apptainer build --sandbox "${SBX_DIR}" "${RECIPE}" \
       && build_attempt sandbox_pack apptainer build "${OUT_SIF}" "${SBX_DIR}"; then
        BUILD_RC=0
        BUILD_METHOD="sandbox"
    fi
fi

BUILD_COMPLETED_AT_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ ${BUILD_RC} -ne 0 ]]; then
    echo "BUILD_FAILED all attempts exhausted. marker=BLOCKED_RUNTIME" >&2
    exit 1
fi

if [[ ! -f "${OUT_SIF}" ]]; then
    echo "BUILD_OUTPUT_MISSING ${OUT_SIF} not found despite reported success." >&2
    exit 1
fi

OUT_SHA256="$(sha256sum "${OUT_SIF}" | awk '{print $1}')"
OUT_SIZE="$(stat -c '%s' "${OUT_SIF}")"

echo "BUILD_METHOD=${BUILD_METHOD}"
echo "OUT_SHA256=${OUT_SHA256}"
echo "OUT_SIZE_BYTES=${OUT_SIZE}"
echo "BUILD_STARTED_AT_UTC=${BUILD_STARTED_AT_UTC}"
echo "BUILD_COMPLETED_AT_UTC=${BUILD_COMPLETED_AT_UTC}"

echo "APPTAINER_INSPECT_BEGIN"
apptainer inspect "${OUT_SIF}" || {
    echo "APPTAINER_INSPECT_FAILED" >&2
    exit 1
}
echo "APPTAINER_INSPECT_END"
echo "OK_APPTAINER_INSPECT"

echo "BUILD_OK_${OUT_SHA256}"
