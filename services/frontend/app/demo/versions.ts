// Frozen TS mirror of libs/common/versions.py for the /demo UI.
//
// Pinned by tests/demo/test_b11_1c_versions_drift.py — any future Python-side
// bump must be reflected here in the same change. DEFAULT_ENHANCER_VERSION is
// NOT a synonym for "bypass"; bypass detection in page.tsx uses the literal
// string equality enhancer_version === "bypass" (matches BYPASS_ENHANCER_VERSION
// in libs/audio/enhancement.py).

export const DEGRADATION_VERSION = "degradation_v1";
export const METRICS_VERSION = "1.0";
export const DEFAULT_ENHANCER_VERSION = "1.0";
