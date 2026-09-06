// Frozen list of the 5 degradation IDs registered in
// libs/audio/degradations.py::DEGRADATION_REGISTRY. The matching backend test
// tests/demo/test_b11_1a_degradation_id_drift.py asserts these stay in sync.

export const DEGRADATION_IDS = [
  "far_field_room",
  "cafe_background",
  "phone_call",
  "muffled",
  "broadband_hiss",
] as const;

export type DegradationId = (typeof DEGRADATION_IDS)[number];

export const DEGRADATION_LABELS: Record<DegradationId, string> = {
  far_field_room: "Far-field room",
  cafe_background: "Cafe background noise",
  phone_call: "Phone call (300–3400 Hz)",
  muffled: "Muffled (low-pass 1 kHz)",
  broadband_hiss: "Broadband hiss",
};
