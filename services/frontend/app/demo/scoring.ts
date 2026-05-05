// Frontend-only Word Accuracy / WER scoring for /demo (B11.1c).
//
// This module mirrors libs/audio/metrics.py so manual ground truth never has
// to leave the browser. Pure functions only — no fetch, XMLHttpRequest,
// localStorage/sessionStorage/indexedDB/cookies, no sendBeacon, no console.*.
//
// Algorithm parity with libs/audio/metrics.py:
//   normalize_text:  lowercase -> strip [^\w\s] -> collapse whitespace -> trim
//   word edit dist:  classic DP word-level Levenshtein
//   compute_metrics: empty/whitespace-only reference -> available=false
//                    wer = edit_distance / len(ref_tokens)
//                    word_accuracy = clamp(1 - wer, 0, 1)
//
// JS-side note on \w: Python 3 `\w` matches Unicode letters, digits, and
// underscore. We approximate that with /[^\p{L}\p{N}_\s]/gu which keeps
// letters/digits/underscore and strips punctuation including apostrophes —
// the same observable behavior as the Python regex on ASCII English speech,
// which is the demo's documented target language.

export type MetricsResult = {
  available: boolean;
  wer: number | null;
  wordAccuracy: number | null;
};

export function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}_\s]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function wordEditDistance(ref: string[], hyp: string[]): number {
  const r = ref.length;
  const h = hyp.length;
  let row: number[] = new Array(h + 1);
  for (let j = 0; j <= h; j += 1) row[j] = j;
  for (let i = 1; i <= r; i += 1) {
    const newRow: number[] = new Array(h + 1);
    newRow[0] = i;
    for (let j = 1; j <= h; j += 1) {
      if (ref[i - 1] === hyp[j - 1]) {
        newRow[j] = row[j - 1];
      } else {
        newRow[j] = 1 + Math.min(row[j - 1], row[j], newRow[j - 1]);
      }
    }
    row = newRow;
  }
  return row[h];
}

function tokenize(normalized: string): string[] {
  if (normalized === "") return [];
  return normalized.split(" ");
}

export function computeMetrics(
  hypothesis: string,
  reference: string | null,
): MetricsResult {
  if (reference === null) {
    return { available: false, wer: null, wordAccuracy: null };
  }
  const normRef = normalizeText(reference);
  if (normRef === "") {
    return { available: false, wer: null, wordAccuracy: null };
  }
  const refTokens = tokenize(normRef);
  const hypTokens = tokenize(normalizeText(hypothesis));
  const dist = wordEditDistance(refTokens, hypTokens);
  const wer = dist / refTokens.length;
  const wordAccuracy = Math.max(0, Math.min(1, 1 - wer));
  return { available: true, wer, wordAccuracy };
}
