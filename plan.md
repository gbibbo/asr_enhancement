# ASR Enhancement — Branch Entry Point

## Active profile and plans on this branch

Branch: `feature/robust-asr-lora-router-datamove1-v1`.

The active profile for this branch is `ROBUST_ASR_PROFILE`, declared in
`CLAUDE.md` between the `BEGIN ROBUST_ASR_PROFILE` and
`END ROBUST_ASR_PROFILE` delimiters. The robust_asr profile is the
normative source of execution rules for this branch.

- Active orchestrator plan:
  `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md`
- Active agent plan:
  `docs/plans/robust_asr_agent_plan_v3_4_7.md`
- Active schemas:
  `docs/plans/state_packet_schemas_v1.yaml`
- Active trackers:
  `docs/progress/robust_asr_progress.yaml`
  `docs/progress/robust_asr_progress.md`
  `docs/progress/robust_asr_state_capsule.md`

## Legacy references (read-only)

The legacy training/datamove1 plan was archived. The canonical path
`docs/plans/training_datamove1_plan.md` is intentionally absent from the
live tree and must not be restored. The read-only archived copy lives at:

- `docs/plans/archive/legacy_reference_plans/20260507T223435Z/training_datamove1_plan.md`

The legacy training/datamove1 trackers also remain in the tree as
read-only historical artifacts:

- `docs/progress/training_datamove1_progress.yaml`
- `docs/progress/training_datamove1_progress.md`

These legacy trackers must not be used to determine `current_task`,
markers, gates, or claims for the robust_asr project. The robust_asr
tracker (`docs/progress/robust_asr_progress.yaml`) is the only live
source of truth for this branch.

The original platform MVP state is preserved under the git tag
`platform-mvp-v0` and is unaffected by this entry-point refresh.
