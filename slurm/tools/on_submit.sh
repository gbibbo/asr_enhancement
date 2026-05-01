#!/usr/bin/env bash
set -euo pipefail

SUBMIT_HOST="aisurrey-submit01.surrey.ac.uk"

usage() {
    echo "Usage: $0 <squeue|sbatch|scancel|sacct> <args...>" >&2
}

if [ "$#" -lt 1 ]; then
    usage
    exit 2
fi

cmd="$1"
shift

case "$cmd" in
    squeue|sbatch|scancel|sacct)
        ;;
    *)
        echo "ERROR: unsupported Slurm command: $cmd" >&2
        echo "Allowed commands: squeue, sbatch, scancel, sacct" >&2
        exit 2
        ;;
esac

exec ssh -o BatchMode=yes "$SUBMIT_HOST" "$cmd" "$@"