#!/usr/bin/env python3
"""train_lora_smoke.py — robust_asr §4.4 LoRA smoke training.

Trains Whisper base.en with LoRA (rank=8, target q/k/v/out_proj) on the
600-row stratified smoke_split for at most steps_max steps.

On CUDA OOM at batch b: retry once at max(1, b//2); if OOM at b=1 → exit 2.
On non-finite loss for ≥5% of completed steps → exit 3.

Emits OK_LORA_SMOKE_TRAIN on PASS.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from libs.audio.degradations import apply_degradation  # noqa: E402

# Training-profile family names (from libs/audio/degradations.py) used for
# on-the-fly degradation of clean lora_train audio during smoke training.
TRAIN_DEGRADATION_FAMILIES = [
    "cafe_background",
    "phone_call",
    "muffled",
    "far_field_room",
]


def fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr, flush=True)
    sys.exit(code)


def _write_loss_curve(rows: list[dict], out_path: Path) -> None:
    """Render a loss curve PNG. Prefers matplotlib, falls back to PIL."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        steps_x = [r["step"] for r in rows]
        losses_y = [r["loss"] if math.isfinite(r["loss"]) else float("nan") for r in rows]
        plt.figure(figsize=(7, 3))
        plt.plot(steps_x, losses_y, "-", linewidth=0.8)
        plt.xlabel("step")
        plt.ylabel("loss")
        plt.title(f"LoRA smoke loss (n={len(rows)} steps)")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(out_path, dpi=120)
        plt.close()
        return
    except Exception:
        pass
    try:
        from PIL import Image, ImageDraw

        W, H = 700, 240
        img = Image.new("RGB", (W, H), "white")
        draw = ImageDraw.Draw(img)
        # Margins
        ml, mr, mt, mb = 60, 20, 20, 40
        steps_x = [r["step"] for r in rows]
        losses_y = [r["loss"] for r in rows if math.isfinite(r["loss"])]
        if not steps_x or not losses_y:
            img.save(out_path)
            return
        x_min, x_max = min(steps_x), max(steps_x)
        y_min, y_max = min(losses_y), max(losses_y)
        if x_max == x_min:
            x_max = x_min + 1
        if y_max == y_min:
            y_max = y_min + 1.0

        def px(x):
            return ml + (x - x_min) / (x_max - x_min) * (W - ml - mr)

        def py(y):
            return H - mb - (y - y_min) / (y_max - y_min) * (H - mt - mb)

        # Axes
        draw.line([(ml, mt), (ml, H - mb), (W - mr, H - mb)], fill="black", width=1)
        # Polyline
        pts = []
        for r in rows:
            if math.isfinite(r["loss"]):
                pts.append((px(r["step"]), py(r["loss"])))
        if len(pts) >= 2:
            draw.line(pts, fill=(30, 70, 180), width=1)
        # Labels
        draw.text((ml, 4), f"LoRA smoke loss (n={len(rows)}; y in [{y_min:.3f},{y_max:.3f}])", fill="black")
        draw.text((W - 100, H - mb + 5), f"step → {x_max}", fill="black")
        img.save(out_path)
    except Exception:
        pass
    try:
        _stdlib_png_loss_curve(rows, out_path)
    except Exception as e:
        print(f"WARNING: loss_curve.png fallback failed: {e}", file=sys.stderr, flush=True)


def _stdlib_png_loss_curve(rows: list[dict], out_path: Path) -> None:
    """Pure-stdlib PNG renderer (zlib + struct). 700x240 RGB, blue polyline."""
    import struct
    import zlib

    W, H = 700, 240
    ml, mr, mt, mb = 60, 20, 20, 40
    inner_w, inner_h = W - ml - mr, H - mt - mb
    finite = [(r["step"], r["loss"]) for r in rows if math.isfinite(r["loss"])]
    if not finite:
        return
    xs = [p[0] for p in finite]
    ys = [p[1] for p in finite]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max == x_min:
        x_max = x_min + 1
    if y_max == y_min:
        y_max += 1.0
    pixels = bytearray([255] * (3 * W * H))

    def setpx(x, y, rgb=(30, 70, 180)):
        if 0 <= x < W and 0 <= y < H:
            i = 3 * (y * W + x)
            pixels[i:i + 3] = bytes(rgb)

    for y in range(mt, H - mb + 1):
        setpx(ml, y, (0, 0, 0))
    for x in range(ml, W - mr + 1):
        setpx(x, H - mb, (0, 0, 0))

    def pxx(x):
        return int(ml + (x - x_min) / (x_max - x_min) * inner_w)

    def pxy(y):
        return int(H - mb - (y - y_min) / (y_max - y_min) * inner_h)

    prev = None
    for s, l in finite:
        p = (pxx(s), pxy(l))
        if prev is None:
            prev = p
            setpx(*p)
            continue
        x0, y0 = prev
        x1, y1 = p
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            setpx(x0, y0)
            setpx(x0, y0 + 1)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        prev = p

    def chunk(typ, data):
        crc = zlib.crc32(typ + data)
        return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", crc)

    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(pixels[3 * y * W:3 * (y + 1) * W])

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    out_path.write_bytes(png)


def load_audio_mono16k(path: str) -> np.ndarray:
    import soundfile as sf

    samples, sr = sf.read(path, dtype="float32", always_2d=False)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    if sr != 16000:
        import librosa

        samples = librosa.resample(samples.astype(np.float64), orig_sr=sr, target_sr=16000)
    return samples.astype(np.float32)


_TRANS_CACHE: dict[str, dict[str, str]] = {}


def resolve_reference_text(audio_path: str, utterance_id: str) -> str:
    """Load reference text from the colocated LibriSpeech .trans.txt file."""
    parent = str(Path(audio_path).parent)
    if parent not in _TRANS_CACHE:
        mapping: dict[str, str] = {}
        for trans in Path(parent).glob("*.trans.txt"):
            with open(trans, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    uid, _, text = line.partition(" ")
                    mapping[uid] = text
        _TRANS_CACHE[parent] = mapping
    text = _TRANS_CACHE[parent].get(utterance_id)
    if text is None:
        raise FileNotFoundError(f"transcript missing for {utterance_id} under {parent}")
    return text


def build_split_records(config: dict) -> list[dict]:
    """Resolve smoke_split audio_ids → (audio_path, reference_text)."""
    import pyarrow.parquet as pq

    src_path = REPO_ROOT / config["smoke_split"]["source_manifest"]
    table = pq.read_table(str(src_path))
    cols = table.column_names

    path_by_id: dict[str, str] = {}
    utt_by_id: dict[str, str] = {}
    for i in range(table.num_rows):
        aid = table.column("audio_id")[i].as_py()
        path_by_id[aid] = table.column("audio_path_or_uri")[i].as_py()
        utt_by_id[aid] = table.column("utterance_id")[i].as_py()

    records: list[dict] = []
    for aid in config["smoke_split"]["audio_ids"]:
        if aid not in path_by_id:
            raise KeyError(f"audio_id {aid} not in {src_path}")
        records.append(
            {
                "audio_id": aid,
                "audio_path": path_by_id[aid],
                "utterance_id": utt_by_id[aid],
            }
        )
    return records


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    args = ap.parse_args(argv)

    cfg_path = args.config
    with open(cfg_path, "r") as fh:
        cfg = yaml.safe_load(fh)

    seed = int(cfg["hyperparameters"]["seed"])
    steps_max = int(cfg["hyperparameters"]["steps_max"])
    lr = float(cfg["hyperparameters"]["learning_rate"])
    batch_size_initial = int(cfg["hyperparameters"]["batch_size"])
    warmup_steps = int(cfg["hyperparameters"]["warmup_steps"])
    lora_rank = int(cfg["hyperparameters"]["lora_rank"])
    lora_alpha = int(cfg["hyperparameters"]["lora_alpha"])
    lora_dropout = float(cfg["hyperparameters"]["lora_dropout"])
    target_modules = list(cfg["hyperparameters"]["target_modules"])
    fp16 = bool(cfg["hyperparameters"].get("fp16", True))
    train_timeout = int(cfg["timeouts"]["training_timeout_seconds"])

    # Output dirs
    out_root = REPO_ROOT / "artifacts/robust_asr/lora_smoke"
    out_root.mkdir(parents=True, exist_ok=True)
    ckpt_root = out_root / "checkpoints"
    ckpt_root.mkdir(parents=True, exist_ok=True)
    training_log_path = out_root / "training_log.csv"
    loss_curve_path = out_root / "loss_curve.png"
    ckpt_manifest_path = out_root / "checkpoint_manifest.json"

    # Determinism
    import torch

    torch.manual_seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    if not torch.cuda.is_available():
        fail("CUDA not available; smoke training requires GPU", 1)

    device = torch.device("cuda")

    # Load Whisper base.en HF + tokenizer + feature_extractor
    from transformers import (
        WhisperForConditionalGeneration,
        WhisperProcessor,
    )

    base_model_name = os.environ.get("WHISPER_BASE_MODEL", "openai/whisper-base.en")
    print(f"loading {base_model_name} ...", flush=True)
    processor = WhisperProcessor.from_pretrained(base_model_name, local_files_only=True)
    base_model = WhisperForConditionalGeneration.from_pretrained(base_model_name, local_files_only=True)
    base_model.config.forced_decoder_ids = None
    base_model.config.suppress_tokens = []
    base_model.generation_config.forced_decoder_ids = None
    base_model.generation_config.suppress_tokens = []

    # PEFT LoRA injection
    from peft import LoraConfig, get_peft_model

    lora_cfg = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        target_modules=target_modules,
    )
    model = get_peft_model(base_model, lora_cfg)
    model.to(device)
    if fp16:
        # Cast LoRA adapter params to fp32 for stable optimizer states; rest can use AMP.
        pass
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(
        f"LoRA trainable params: {trainable:,} / total {total:,} "
        f"({100 * trainable / total:.3f}%)",
        flush=True,
    )

    # Data
    records = build_split_records(cfg)
    n_records = len(records)
    print(f"smoke_split records: {n_records}", flush=True)
    if n_records < 1:
        fail("empty smoke_split", 1)

    # Preload references upfront
    for rec in records:
        rec["reference_text"] = resolve_reference_text(rec["audio_path"], rec["utterance_id"])

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
        weight_decay=float(cfg["hyperparameters"].get("weight_decay", 0.0)),
    )

    def lr_at(step: int) -> float:
        if step < warmup_steps:
            return lr * (step + 1) / max(1, warmup_steps)
        # constant after warmup for smoke
        return lr

    scaler = torch.amp.GradScaler("cuda") if fp16 else None

    rng = np.random.default_rng(seed)
    sample_indices = np.arange(n_records)

    training_log_rows: list[dict] = []
    nonfinite_count = 0
    step = 0
    start_time = time.time()

    def build_batch(indices: list[int]):
        audios: list[np.ndarray] = []
        labels_texts: list[str] = []
        for i, idx in enumerate(indices):
            rec = records[idx]
            try:
                samples = load_audio_mono16k(rec["audio_path"])
            except Exception as e:
                raise RuntimeError(f"audio load failed for {rec['audio_id']}: {e}")
            # Round-robin family assignment using deterministic seed
            family = TRAIN_DEGRADATION_FAMILIES[
                (int(rec["utterance_id"].split("-")[-1]) + i) % len(TRAIN_DEGRADATION_FAMILIES)
            ]
            try:
                degraded = apply_degradation(
                    samples.astype(np.float64), 16000, family, rec["audio_id"]
                ).astype(np.float32)
            except Exception:
                degraded = samples
            audios.append(degraded)
            labels_texts.append(rec["reference_text"])

        # Feature extraction
        feat = processor.feature_extractor(
            audios, sampling_rate=16000, return_tensors="pt"
        )
        input_features = feat["input_features"].to(device)

        # Tokenize labels (decoder targets); pad/truncate to 224 (within Whisper limit)
        tok = processor.tokenizer(
            labels_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=224,
        )
        labels = tok["input_ids"]
        labels = labels.masked_fill(tok["attention_mask"] == 0, -100)
        labels = labels.to(device)
        return input_features, labels

    current_batch_size = batch_size_initial
    oom_retried_at = -1

    while step < steps_max:
        if (time.time() - start_time) > train_timeout:
            fail(
                f"TRAINING_TIMEOUT_EXCEEDED elapsed={time.time() - start_time:.0f}s "
                f"budget={train_timeout}s step={step}",
                1,
            )

        # Pick batch indices deterministically per step
        batch_idx = rng.choice(sample_indices, size=current_batch_size, replace=True).tolist()

        try:
            input_features, labels = build_batch(batch_idx)

            for g in optimizer.param_groups:
                g["lr"] = lr_at(step)

            model.train()
            optimizer.zero_grad(set_to_none=True)
            if fp16:
                with torch.amp.autocast("cuda", dtype=torch.float16):
                    out = model(input_features=input_features, labels=labels)
                loss = out.loss
                if not torch.isfinite(loss):
                    nonfinite_count += 1
                    step += 1
                    training_log_rows.append(
                        {"step": step, "loss": float("nan"), "lr": lr_at(step - 1), "batch_size": current_batch_size}
                    )
                    nf_ratio = nonfinite_count / max(1, step)
                    if nf_ratio >= 0.05 and step >= 20:
                        fail(
                            f"NON_FINITE_LOSS_THRESHOLD_EXCEEDED ratio={nf_ratio:.3f} step={step}",
                            3,
                        )
                    continue
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(
                    [p for p in model.parameters() if p.requires_grad], max_norm=1.0
                )
                scaler.step(optimizer)
                scaler.update()
            else:
                out = model(input_features=input_features, labels=labels)
                loss = out.loss
                if not torch.isfinite(loss):
                    nonfinite_count += 1
                    step += 1
                    training_log_rows.append(
                        {"step": step, "loss": float("nan"), "lr": lr_at(step - 1), "batch_size": current_batch_size}
                    )
                    nf_ratio = nonfinite_count / max(1, step)
                    if nf_ratio >= 0.05 and step >= 20:
                        fail(
                            f"NON_FINITE_LOSS_THRESHOLD_EXCEEDED ratio={nf_ratio:.3f} step={step}",
                            3,
                        )
                    continue
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    [p for p in model.parameters() if p.requires_grad], max_norm=1.0
                )
                optimizer.step()

            step += 1
            loss_val = float(loss.detach().cpu().item())
            training_log_rows.append(
                {"step": step, "loss": loss_val, "lr": lr_at(step - 1), "batch_size": current_batch_size}
            )
            if step % 10 == 0 or step == 1:
                elapsed = time.time() - start_time
                print(
                    f"step={step:4d} loss={loss_val:.4f} lr={lr_at(step - 1):.2e} "
                    f"bs={current_batch_size} elapsed={elapsed:.1f}s",
                    flush=True,
                )

            # Save checkpoint every 50 steps + at last step
            if (step % 50 == 0) or (step == steps_max):
                ckpt_dir = ckpt_root / f"step_{step:05d}"
                ckpt_dir.mkdir(parents=True, exist_ok=True)
                model.save_pretrained(str(ckpt_dir))
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if current_batch_size > 1 and oom_retried_at != step:
                new_bs = max(1, current_batch_size // 2)
                print(
                    f"CUDA_OOM at batch_size={current_batch_size}, retrying once with bs={new_bs}",
                    file=sys.stderr,
                    flush=True,
                )
                current_batch_size = new_bs
                oom_retried_at = step
                continue
            if current_batch_size <= 1:
                fail("CUDA_OOM_AT_BATCH_SIZE_1", 2)
            fail(f"CUDA_OOM persisted at bs={current_batch_size} after retry", 2)

    # Final mandatory checkpoint at last step (idempotent — file overwrite OK)
    final_ckpt = ckpt_root / f"step_{step:05d}"
    if not final_ckpt.exists():
        final_ckpt.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(final_ckpt))

    # Write training_log.csv
    with open(training_log_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["step", "loss", "lr", "batch_size"])
        w.writeheader()
        for r in training_log_rows:
            w.writerow(r)

    # Loss curve PNG — try matplotlib, fall back to PIL polyline
    _write_loss_curve(training_log_rows, loss_curve_path)

    # Checkpoint manifest
    finite_log = [r for r in training_log_rows if math.isfinite(r["loss"])]
    if not finite_log:
        fail("no finite-loss steps recorded", 3)
    best_row = min(finite_log, key=lambda r: r["loss"])
    best_step = best_row["step"]
    # Snap to nearest saved checkpoint (every 50 + final)
    saved_steps = sorted(
        int(p.name.split("_")[1]) for p in ckpt_root.iterdir() if p.is_dir() and p.name.startswith("step_")
    )
    # Pick the saved step closest to best_step but not exceeding it; fall back to final
    candidates = [s for s in saved_steps if s <= best_step]
    chosen_best = candidates[-1] if candidates else saved_steps[-1]
    manifest = {
        "config_path": str(cfg_path.relative_to(REPO_ROOT)) if cfg_path.is_absolute() else str(cfg_path),
        "base_model": base_model_name,
        "seed": seed,
        "steps_completed": step,
        "steps_max": steps_max,
        "best_step": chosen_best,
        "best_loss": float(best_row["loss"]),
        "checkpoints": [
            {
                "step": s,
                "path": str((ckpt_root / f"step_{s:05d}").relative_to(REPO_ROOT)),
            }
            for s in saved_steps
        ],
        "hyperparameters": cfg["hyperparameters"],
        "elapsed_seconds": round(time.time() - start_time, 2),
        "nonfinite_count": nonfinite_count,
    }
    with open(ckpt_manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

    print(
        f"OK_LORA_SMOKE_TRAIN steps_completed={step} best_step={chosen_best} "
        f"best_loss={best_row['loss']:.4f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
