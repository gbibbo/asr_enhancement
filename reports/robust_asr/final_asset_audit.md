# Final asset audit — P10.2

PASS

## Audit scope

- artifact-root: `/mnt/fast/nobackup/users/gb0048/asr_enhancement/artifacts/robust_asr`
- report-root: `/mnt/fast/nobackup/users/gb0048/asr_enhancement/reports/robust_asr`
- report-root: `/mnt/fast/nobackup/users/gb0048/asr_enhancement/docs/reports/robust_asr`

## Assertion summary

- A1 (committed-artifact sha256 vs tracker): **PASS**
- A2 (large-artifact sha256 in tracker):     **PASS**
- A3 (no residual TODO_FILLED_IN for closed tasks): **PASS**
- A4 (no secret-like tokens outside .git):    **PASS**

## A1 — committed artifact sha256 vs tracker

| key | path | result | tracker_sha256 | on_disk_sha256 |
|---|---|---|---|---|
| state_capsule | `docs/progress/robust_asr_state_capsule.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| task_reports_root | `reports/robust_asr/task_reports` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| repository_inventory | `reports/robust_asr/repository_inventory.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| asset_inventory | `reports/robust_asr/asset_inventory.md` | PASS | `546cfcaa6ae7dbf6b1335f38fc98a267acdb9ea933921b16facf5cb582bed760` | `546cfcaa6ae7dbf6b1335f38fc98a267acdb9ea933921b16facf5cb582bed760` |
| repo_integration_policy | `reports/robust_asr/repo_integration_policy.md` | PASS | `f641018166c67e552f6de233fcd986d88f4646ed8d8c85436b5006c44bb20bba` | `f641018166c67e552f6de233fcd986d88f4646ed8d8c85436b5006c44bb20bba` |
| touch_policy | `reports/robust_asr/touch_policy.md` | PASS | `33243a494e3865dc7519008e75687bfcb232c27a5ec3dfd7cc6a8a00de0e80d7` | `33243a494e3865dc7519008e75687bfcb232c27a5ec3dfd7cc6a8a00de0e80d7` |
| reuse_policy_config | `configs/robust_asr/reuse_policy_v1.yaml` | PASS | `c9e187ecbdc24ba0503753934f32bf4bb08df0a4f5ca049b9200299fca851876` | `c9e187ecbdc24ba0503753934f32bf4bb08df0a4f5ca049b9200299fca851876` |
| validate_report_shape_script | `scripts/robust_asr/validate_report_shape.py` | PASS | `0db5e18dfe077a0ccfa3d7148e17ddabef8c8f742e88a67a8a9b2b97efabd977` | `0db5e18dfe077a0ccfa3d7148e17ddabef8c8f742e88a67a8a9b2b97efabd977` |
| report_shape_fixtures | `artifacts/robust_asr/state_packets/report_shape_fixtures` | SKIP_DIRECTORY | `704da3b3ce4f585e69a7fb310f95940dbfbd8d5da51e422c906a24a4427e67ab` | `` |
| runtime_smoke_report | `reports/robust_asr/runtime_smoke.md` | PASS | `0b286c9b2acf13cdc87b9d0301bc5c5dd60c51ac4e122b216cf82fb5b037ee25` | `0b286c9b2acf13cdc87b9d0301bc5c5dd60c51ac4e122b216cf82fb5b037ee25` |
| runtime_image_v1 | `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif` | PASS | `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713` | `8db5364c7610496a33f1d6aa5677a5196460c6907b992b04560efbb7e4ce8713` |
| runtime_image_rebuild_report | `reports/robust_asr/runtime_image_rebuild.md` | PASS | `0f1db37dd3e0e2d81ac5b6fa8c6635dced7d77510d02a01aadd0d7d43eedace4` | `0f1db37dd3e0e2d81ac5b6fa8c6635dced7d77510d02a01aadd0d7d43eedace4` |
| runtime_contract_fixture | `reports/robust_asr/runtime_contract_smoke.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| model_card_template | `docs/reports/robust_asr/model_card_lora.md` | PASS | `01fec571aea1d3f915ae635c1522d75b5254ffe4537c2d86ce9fae8cb66bc463` | `01fec571aea1d3f915ae635c1522d75b5254ffe4537c2d86ce9fae8cb66bc463` |
| router_card_template | `docs/reports/robust_asr/router_card.md` | PASS | `2587f5364a761bf8cef7bf4de111b9fe6af1bb3f51e0dc0aa8f0f07bd7882624` | `2587f5364a761bf8cef7bf4de111b9fe6af1bb3f51e0dc0aa8f0f07bd7882624` |
| eval_schema_yaml | `libs/common/eval_schema.yaml` | PASS | `f453cbff7c5ed0ed5c9b30599b775b540b776d56ad02ee0eaebf358e6a0124d9` | `f453cbff7c5ed0ed5c9b30599b775b540b776d56ad02ee0eaebf358e6a0124d9` |
| normalization_module | `libs/common/normalization.py` | PASS | `c65ec41f835fc5ec518238cb07dfe5f6d53cce44f1078fc6ce74533081630578` | `c65ec41f835fc5ec518238cb07dfe5f6d53cce44f1078fc6ce74533081630578` |
| metrics_module_robust_asr | `libs/common/metrics.py` | PASS | `96b45e4571383afcd4cc4efcf8115cf1b38cfb5a7e39966de7f758e5c263cb76` | `96b45e4571383afcd4cc4efcf8115cf1b38cfb5a7e39966de7f758e5c263cb76` |
| versions_module | `libs/common/versions.py` | PASS | `be0b136d4f910dd12481554405a5a0ec53091f8222b15ab622cedea0af0161f6` | `be0b136d4f910dd12481554405a5a0ec53091f8222b15ab622cedea0af0161f6` |
| validate_eval_schema_script | `scripts/robust_asr/validate_eval_schema.py` | PASS | `8ad31f3b59864c1bb812e26a318ac62299fb7ba843c7b740874de41e2f34206b` | `8ad31f3b59864c1bb812e26a318ac62299fb7ba843c7b740874de41e2f34206b` |
| test_eval_schema | `tests/robust_asr/test_eval_schema.py` | PASS | `c14fcbeb04780954c927bb524e9b34e66316af992916261de8facc03744dfc68` | `c14fcbeb04780954c927bb524e9b34e66316af992916261de8facc03744dfc68` |
| test_normalization_metrics | `tests/robust_asr/test_normalization_metrics.py` | PASS | `9f935e71c67d1aebf6c0b4769a41849e8dd8fec67a354890bc290b2dcca4b2ee` | `9f935e71c67d1aebf6c0b4769a41849e8dd8fec67a354890bc290b2dcca4b2ee` |
| test_leakage | `tests/robust_asr/test_leakage.py` | PASS | `a1b264593b5f6488e4fefdeff50336156f076fab638c0449b3b25e8995971d2c` | `a1b264593b5f6488e4fefdeff50336156f076fab638c0449b3b25e8995971d2c` |
| manifest_summary | `reports/robust_asr/manifest_summary.md` | PASS | `14c4a60261d9ee6f98e60c7fc63dd166567d58ea9a28843ed8c9b89e921a08ac` | `14c4a60261d9ee6f98e60c7fc63dd166567d58ea9a28843ed8c9b89e921a08ac` |
| degradations_module | `libs/audio/degradations.py` | PASS | `e8d145766cb4789d49d37ee300d53607a280e62076d0abb54f731173df1ebcff` | `e8d145766cb4789d49d37ee300d53607a280e62076d0abb54f731173df1ebcff` |
| degradation_v1_config | `configs/robust_asr/degradation_v1.yaml` | PASS | `82da2b09ed7888d5018ef2f539d65a702d7c55c9865ae88e81646d36bb176d3c` | `82da2b09ed7888d5018ef2f539d65a702d7c55c9865ae88e81646d36bb176d3c` |
| build_degradation_v1_script | `scripts/robust_asr/build_degradation_v1.py` | PASS | `69bc5f5c1481a15b59c1044d01b8536902efe9e0bc307f5299ebcd4396472f11` | `69bc5f5c1481a15b59c1044d01b8536902efe9e0bc307f5299ebcd4396472f11` |
| test_degradation_v1 | `tests/robust_asr/test_degradation_v1.py` | PASS | `c00b3123f55e2013bf907621a4ea265216f01aad99035b36bc15a5e3b6d052bc` | `c00b3123f55e2013bf907621a4ea265216f01aad99035b36bc15a5e3b6d052bc` |
| p1_4_slurm_job_script | `slurm/jobs/p1_4_build_degradation_v1.sh` | PASS | `0b4e45dff4698dfa340bacbd2d2810cb00fde312d596408f58e79861236bf91f` | `0b4e45dff4698dfa340bacbd2d2810cb00fde312d596408f58e79861236bf91f` |
| degradation_v1_id_eval_manifest | `artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet` | PASS | `cf0f0bce49cb0d2a813ce65ab764485ddc1cc7c5e5b9756f1668d0950a4d9a49` | `cf0f0bce49cb0d2a813ce65ab764485ddc1cc7c5e5b9756f1668d0950a4d9a49` |
| degradation_v1_ood_param_eval_manifest | `artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet` | PASS | `30684dc489bef980f02a2bc0c45cb4aa8bc8fc605e373de10dd97397b2308314` | `30684dc489bef980f02a2bc0c45cb4aa8bc8fc605e373de10dd97397b2308314` |
| degradation_v1_per_family.clean_id | `artifacts/robust_asr/manifests/degradation_v1_clean_id.parquet` | PASS | `fde856ea663fcbd67ee9a593511cdd1a85153f4917162b0042db2bb45a64028e` | `fde856ea663fcbd67ee9a593511cdd1a85153f4917162b0042db2bb45a64028e` |
| degradation_v1_per_family.clean_ood_param | `artifacts/robust_asr/manifests/degradation_v1_clean_ood_param.parquet` | PASS | `dc8d4101993937588e5568e85f70bfd5366c0179e5a47cc5557eed79d1312950` | `dc8d4101993937588e5568e85f70bfd5366c0179e5a47cc5557eed79d1312950` |
| degradation_v1_per_family.cafe_noise_id | `artifacts/robust_asr/manifests/degradation_v1_cafe_noise_id.parquet` | PASS | `bae18ae26c06d873ca7dd84ce1029bd2a409bb859133986d9a14a9a4be3af778` | `bae18ae26c06d873ca7dd84ce1029bd2a409bb859133986d9a14a9a4be3af778` |
| degradation_v1_per_family.cafe_noise_ood_param | `artifacts/robust_asr/manifests/degradation_v1_cafe_noise_ood_param.parquet` | PASS | `b958b37ce1bbf620d800087da6fe3a503b34b4bdc0aebe2ab0500830958e402e` | `b958b37ce1bbf620d800087da6fe3a503b34b4bdc0aebe2ab0500830958e402e` |
| degradation_v1_per_family.phone_band_id | `artifacts/robust_asr/manifests/degradation_v1_phone_band_id.parquet` | PASS | `b0e7cabe99c5a5843a05a2e25ab50f778822b247b29ad11a175134591c9d7f48` | `b0e7cabe99c5a5843a05a2e25ab50f778822b247b29ad11a175134591c9d7f48` |
| degradation_v1_per_family.phone_band_ood_param | `artifacts/robust_asr/manifests/degradation_v1_phone_band_ood_param.parquet` | PASS | `218e5bf894aa5dff3de16879d6999e00d96750ab8f96ae72848f9a45762beab5` | `218e5bf894aa5dff3de16879d6999e00d96750ab8f96ae72848f9a45762beab5` |
| degradation_v1_per_family.far_field_room_id | `artifacts/robust_asr/manifests/degradation_v1_far_field_room_id.parquet` | PASS | `ec1be39c6aea26f8dab58d941951066162cffb404491a9597f1237db972be354` | `ec1be39c6aea26f8dab58d941951066162cffb404491a9597f1237db972be354` |
| degradation_v1_per_family.far_field_room_ood_param | `artifacts/robust_asr/manifests/degradation_v1_far_field_room_ood_param.parquet` | PASS | `3ea8c734dce4cd902b4e47e3e6336b7b6f60927a861c133f4b9870f5d4e86892` | `3ea8c734dce4cd902b4e47e3e6336b7b6f60927a861c133f4b9870f5d4e86892` |
| degradation_v1_per_family.muffled_lowpass_id | `artifacts/robust_asr/manifests/degradation_v1_muffled_lowpass_id.parquet` | PASS | `742e25ab9a95a399c7e77ea1a81e8cc188da87488eaafbb9707df5788052d82a` | `742e25ab9a95a399c7e77ea1a81e8cc188da87488eaafbb9707df5788052d82a` |
| degradation_v1_per_family.muffled_lowpass_ood_param | `artifacts/robust_asr/manifests/degradation_v1_muffled_lowpass_ood_param.parquet` | PASS | `5c6c4dc1ac0d9e0553045254dde9ae9aac47ebb802b4722c3e58ab9edac8bae9` | `5c6c4dc1ac0d9e0553045254dde9ae9aac47ebb802b4722c3e58ab9edac8bae9` |
| degradation_v1_build_summary_json | `artifacts/robust_asr/manifests/degradation_v1_build_summary.json` | PASS | `678aeb1533aec191496247fd65105537f91dfa490269df21ee71961f78e4e7ef` | `678aeb1533aec191496247fd65105537f91dfa490269df21ee71961f78e4e7ef` |
| degradation_v1_summary | `reports/robust_asr/degradation_v1_summary.md` | PASS | `a1220ea2bf8546ed4d5284d040972016c816ec23c25c0eab250a6f9484b785e5` | `a1220ea2bf8546ed4d5284d040972016c816ec23c25c0eab250a6f9484b785e5` |
| build_public_manifests_script | `scripts/robust_asr/build_public_manifests.py` | PASS | `bd10c89095136cdaa33ca0775ed258daea27a5a896a36f6e7bdf640d3373fed9` | `bd10c89095136cdaa33ca0775ed258daea27a5a896a36f6e7bdf640d3373fed9` |
| summarize_manifests_script | `scripts/robust_asr/summarize_manifests.py` | PASS | `3203ec85df54eac6faeb49b10015b3ad85fe6a163031acc7828726d597617a27` | `3203ec85df54eac6faeb49b10015b3ad85fe6a163031acc7828726d597617a27` |
| public_manifests.librispeech_lora_train | `artifacts/robust_asr/manifests/librispeech_lora_train.parquet` | PASS | `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a` | `7896175ecf9631ef949e504ecc3f442d342a44ae53f8f28ef5a34949f3484d4a` |
| public_manifests.librispeech_router_train | `artifacts/robust_asr/manifests/librispeech_router_train.parquet` | PASS | `c3d281ab0a53304b8a04753e9042bf3e62ea5e1957dc6ef1c524a2f2bac812fc` | `c3d281ab0a53304b8a04753e9042bf3e62ea5e1957dc6ef1c524a2f2bac812fc` |
| public_manifests.librispeech_validation | `artifacts/robust_asr/manifests/librispeech_validation.parquet` | PASS | `977a6f01d72171e9cfb9ce8aee71d4961a99d66397784225c71efbcf1d53733f` | `977a6f01d72171e9cfb9ce8aee71d4961a99d66397784225c71efbcf1d53733f` |
| public_manifests.librispeech_locked_test | `artifacts/robust_asr/manifests/librispeech_locked_test.parquet` | PASS | `ad4f401e06e3c840aaa5d34e5cae22d1cdbb1fb34c7ea671dde0f8a712661da8` | `ad4f401e06e3c840aaa5d34e5cae22d1cdbb1fb34c7ea671dde0f8a712661da8` |
| baseline_table | `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` | PASS | `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6` | `0dc987362fd5d459946e854d85219692c687014901297a52da1a41abdfa7f4a6` |
| baseline_report | `reports/robust_asr/baseline_whisper_base.md` | PASS | `6e5e2f04337c3a0655a37c408c223c6017f5d162adbd3f4eb03b2eb331ca55e1` | `6e5e2f04337c3a0655a37c408c223c6017f5d162adbd3f4eb03b2eb331ca55e1` |
| lora_smoke_report | `reports/robust_asr/lora/lora_smoke_report.md` | PASS | `1369bc7ffdfff3f099d9423f76c643c0d716eef1a22e8b40f41835b870612942` | `1369bc7ffdfff3f099d9423f76c643c0d716eef1a22e8b40f41835b870612942` |
| lora_smoke_checkpoint_manifest | `artifacts/robust_asr/lora_smoke/checkpoint_manifest.json` | PASS | `21d519a5f24d5bc4a6e1b734966ef5b8eda0c41338ace3c58c6ee202b0201ce2` | `21d519a5f24d5bc4a6e1b734966ef5b8eda0c41338ace3c58c6ee202b0201ce2` |
| lora_smoke_training_log | `artifacts/robust_asr/lora_smoke/training_log.csv` | PASS | `d2fd4dca73e1948dbcdc4285262f921ce507aa0ea7289f24c48debd9f63faea8` | `d2fd4dca73e1948dbcdc4285262f921ce507aa0ea7289f24c48debd9f63faea8` |
| lora_smoke_loss_curve | `artifacts/robust_asr/lora_smoke/loss_curve.png` | PASS | `3426869e965866c5974659476b9d318ec7e9710221dec4eda545051bd8dab69c` | `3426869e965866c5974659476b9d318ec7e9710221dec4eda545051bd8dab69c` |
| lora_smoke_eval_result | `reports/robust_asr/lora/lora_smoke_result.json` | PASS | `c5eac79f73d966548562119391837091c490e6d76c29627603563df786e721be` | `c5eac79f73d966548562119391837091c490e6d76c29627603563df786e721be` |
| lora_smoke_export_result | `artifacts/robust_asr/lora_smoke/export_smoke_result.json` | PASS | `ca97450a1f901950b4a96ad3d53d97a6bee3b321c7b361a4c3bfe5b94cda33ad` | `ca97450a1f901950b4a96ad3d53d97a6bee3b321c7b361a4c3bfe5b94cda33ad` |
| lora_smoke_p3_1_report | `reports/robust_asr/task_reports/P3.1_lora_smoke.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| decision_a_report | `reports/robust_asr/lora/decision_a_smoke.md` | PASS | `298fc26791f2e66e99111fb0b4407182a5d6b6d06dfd6ee831ab47849243c1b0` | `298fc26791f2e66e99111fb0b4407182a5d6b6d06dfd6ee831ab47849243c1b0` |
| full_lora_table | `artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| full_lora_report | `reports/robust_asr/lora/full_lora_eval.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| lora_int8_table | `artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| preservation_report | `reports/robust_asr/lora/lora_ct2_int8_preservation.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| assemblyai_table | `None` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| oracle_table | `None` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| selector_evidence_table | `artifacts/robust_asr/router/selector_evidence.parquet` | PASS | `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7` | `c450a91a37c5967ca196dda0b23d5a2963d9b1e6f5eb07bd3f35084e6f9ae1e7` |
| router_v1_config | `configs/robust_asr/router_v1.yaml` | PASS | `ef9586c8e589436ae074d472d38bc12b417d2043d142d5f74d8d5d75f7de2f98` | `ef9586c8e589436ae074d472d38bc12b417d2043d142d5f74d8d5d75f7de2f98` |
| build_selector_evidence_script | `scripts/robust_asr/build_selector_evidence_table.py` | PASS | `226e428e84e1c0646922893d23456c64eef02511424d1c5e2dfef2f1b557735a` | `226e428e84e1c0646922893d23456c64eef02511424d1c5e2dfef2f1b557735a` |
| validate_selector_evidence_script | `scripts/robust_asr/validate_selector_evidence.py` | PASS | `68c39ca111b3ee8eaada8a13fd9b51ab9e282a35efefbb122d24925febe2c1d2` | `68c39ca111b3ee8eaada8a13fd9b51ab9e282a35efefbb122d24925febe2c1d2` |
| selector_evidence_summary | `reports/robust_asr/router/selector_evidence_summary.md` | PASS | `fab05394feb361bb0c1e24b15f32e53b651ea33a4f0e0e3c42affd3914c47d89` | `fab05394feb361bb0c1e24b15f32e53b651ea33a4f0e0e3c42affd3914c47d89` |
| P6_1_task_report | `reports/robust_asr/task_reports/P6.1_selector_evidence.md` | PASS | `28f1f7d6716f4ca190272544e96352f86607a9d00f062f66b3522e57fea423c0` | `28f1f7d6716f4ca190272544e96352f86607a9d00f062f66b3522e57fea423c0` |
| router_features | `artifacts/robust_asr/router/router_features.parquet` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| router_package | `artifacts/robust_asr/router/selected_router` | SKIP_DIRECTORY | `41d194218b52c13b795d782eb92c381ac3eaa696f56fd217cab43e6a059df3fd` | `` |
| package_deterministic_selector_script | `scripts/robust_asr/package_deterministic_selector.py` | PASS | `969c3af202407bbb686e6de83869173a8e8b06958afb2eae7f63c3a58c86ddf1` | `969c3af202407bbb686e6de83869173a8e8b06958afb2eae7f63c3a58c86ddf1` |
| evaluate_deterministic_selector_script | `scripts/robust_asr/evaluate_deterministic_selector.py` | PASS | `fa6e2623815c9e47b279aeaceb577fd24ed9b7e1da668945fc92bc735a4a10d2` | `fa6e2623815c9e47b279aeaceb577fd24ed9b7e1da668945fc92bc735a4a10d2` |
| test_router_runtime | `tests/robust_asr/test_router_runtime.py` | PASS | `fffed034964fecaeb3519ef65f8f963eeed4828c9ca311d712c985c710784514` | `fffed034964fecaeb3519ef65f8f963eeed4828c9ca311d712c985c710784514` |
| selector_final_eval | `reports/robust_asr/router/selector_final_eval.md` | PASS | `8a67872b64b28430576a719d4d7d9189aebda57ce88bb8e62ed625094c654ecf` | `8a67872b64b28430576a719d4d7d9189aebda57ce88bb8e62ed625094c654ecf` |
| P7_3_task_report | `reports/robust_asr/task_reports/P7.3_router_package.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| system_eval_report | `reports/robust_asr/system/system_eval.md` | PASS | `4bdf8f670749537320c55b54c7bc17767d40891cb70693917ec2d3f349fe93ff` | `4bdf8f670749537320c55b54c7bc17767d40891cb70693917ec2d3f349fe93ff` |
| evaluate_system_script | `scripts/robust_asr/evaluate_system.py` | PASS | `8735d888d45c6c92eab187fbb207b3da334b24d3115e88f7d9e2a3cd89a0802b` | `8735d888d45c6c92eab187fbb207b3da334b24d3115e88f7d9e2a3cd89a0802b` |
| p8_1_system_eval_job | `slurm/jobs/p8_1_system_eval.sh` | PASS | `85c3052f58fd78b9b63eabfedc8976e836e1b2c03161f57ff80f13a72868e8e5` | `85c3052f58fd78b9b63eabfedc8976e836e1b2c03161f57ff80f13a72868e8e5` |
| P8_1_task_report | `reports/robust_asr/task_reports/P8.1_system_eval.md` | PASS | `f51c5e8e5452e937411c31742e1dfa492be7556a43b4b32abd027d705c92075f` | `f51c5e8e5452e937411c31742e1dfa492be7556a43b4b32abd027d705c92075f` |
| demo_examples_manifest | `artifacts/robust_asr/demo/demo_examples_manifest.json` | PASS | `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba` | `850c02dbc612882fa7cc0f98e15321b6d4c923c2363351cb1d65a880844863ba` |
| demo_audio_dir | `artifacts/robust_asr/demo/audio` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| demo_provenance_audit | `reports/robust_asr/demo/provenance_audit.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| final_runtime_contract | `artifacts/robust_asr/runtime_contract/final_response_schema.json` | PASS | `c0162941182914b9a536b6ab86510fcb608a6e151d6c048a3a7470ed3b069c3d` | `c0162941182914b9a536b6ab86510fcb608a6e151d6c048a3a7470ed3b069c3d` |
| handoff_package | `artifacts/robust_asr/handoff` | SKIP_DIRECTORY | `cfde7d69601fce86e01ddcf54954752c399513d02bff0c7ef3fcb8cc40e77fa3` | `` |
| rp5_runtime_spec | `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | PASS | `bbcf912d69b15382631f9b92e0597e79ec95259d9a2a9a246e9a86d71dbac197` | `bbcf912d69b15382631f9b92e0597e79ec95259d9a2a9a246e9a86d71dbac197` |
| final_verification | `reports/robust_asr/final_verification.md` | PASS | `82ad07ecebbb33511b6712fb4a74ffb904995582d9a7fabc2d9b7196b1fc1378` | `82ad07ecebbb33511b6712fb4a74ffb904995582d9a7fabc2d9b7196b1fc1378` |
| final_asset_audit | `reports/robust_asr/final_asset_audit.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |
| plan_tracker_consistency | `reports/robust_asr/plan_tracker_consistency.md` | SKIP_NULL_SHA_OR_PATH | `` | `` |

## A2 — large artifact sha256 presence in tracker

| path | in_tracker_with_sha256 | result |
|---|---|---|
| `artifacts/robust_asr/eval_tables/whisper_base_ct2_int8.parquet` | True | PASS |
| `artifacts/robust_asr/router/selector_evidence.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_cafe_noise_id.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_cafe_noise_ood_param.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_clean_id.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_clean_ood_param.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_far_field_room_id.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_far_field_room_ood_param.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_id_eval.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_muffled_lowpass_id.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_muffled_lowpass_ood_param.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_ood_param_eval.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_phone_band_id.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/degradation_v1_phone_band_ood_param.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/librispeech_locked_test.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/librispeech_lora_train.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/librispeech_router_train.parquet` | True | PASS |
| `artifacts/robust_asr/manifests/librispeech_validation.parquet` | True | PASS |
| `/mnt/fast/nobackup/scratch4weeks/gb0048/asr_enhancement_training/runtime/robust_asr_py311_cuda12.sif` | True | PASS |
| `artifacts/robust_asr/oracle/oracle_table.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_OUTCOME_E (P6.2) |
| `artifacts/robust_asr/router/router_features.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_OUTCOME_E (P6.2) |
| `artifacts/robust_asr/router/router_train.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_OUTCOME_E (P6.2) |
| `artifacts/robust_asr/router/router_val.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_OUTCOME_E (P6.2) |
| `artifacts/robust_asr/router/router_test_locked.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_OUTCOME_E (P6.2) |
| `artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_DECISION_A (P4.2) |
| `artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet` | False | N/A_EXPECTED_ABSENT:SKIPPED_BY_DECISION_A (P4.3) |
| `artifacts/robust_asr/eval_tables/assemblyai.parquet` | False | N/A_EXPECTED_ABSENT:HALTED_BLOCKED_API (P5.1) |

## A3 — TODO_FILLED_IN scan over report roots

No `TODO_FILLED_IN_<task_id>` tokens found in the audited report roots.

## A4 — secret-like tokens outside .git

| path | line | offending | match |
|---|---|---|---|
| `.env.example` | 12 | False | `ASSEMBLYAI_API_KEY=` |
| `CLAUDE.md` | 330 | False | `#SBATCH --job-name=asr_<task_name>` |
| `CLAUDE.md` | 600 | False | `ASSEMBLYAI_API_KEY` |
| `CLAUDE.md` | 825 | False | `docs/claude_task_progress.md` |
| `CLAUDE.md` | 826 | False | `docs/claude_task_progress.yaml` |
| `README.md` | 20 | False | `For the full implementation plan see [`plan.md`](plan.md). For per-task execution history see [`docs/claude_task_progress.md`](docs/claude_task_progress.md) and [`docs/claude_task_progress.yaml`](docs/claude_task_progress.yaml).` |
| `README.md` | 121 | False | `- `ASSEMBLYAI_API_KEY=<your-key>`` |
| `README.md` | 145 | False | `- Live AssemblyAI calls cost money, are gated by `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY`, are not part of the post-deploy smoke, and are never run in CI.` |
| `README.md` | 177 | False | `claude_task_progress.md` |
| `README.md` | 178 | False | `claude_task_progress.yaml` |
| `artifacts/robust_asr/handoff/README.md` | 107 | False | `- **selected_backend:** `null` (when `ask_repeat==true`) or` |
| `artifacts/robust_asr/handoff/README.md` | 175 | False | `enabled backend.** The handoff contains no `ASSEMBLYAI_API_KEY`, no` |
| `artifacts/robust_asr/handoff/README.md` | 176 | False | ``sk_*` token, and no `Bearer` credential` |
| `artifacts/robust_asr/handoff/README.md` | 231 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md`;` |
| `artifacts/robust_asr/handoff/README.md` | 232 | False | `- `reports/robust_asr/task_reports/P8_GATE_attempt2.md`.` |
| `artifacts/robust_asr/handoff/handoff_validation_template.md` | 26 | False | `- no_secrets grep (ASSEMBLYAI_API_KEY, sk_, Bearer):` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 163 | False | ``confidence=null`, `ask_repeat=true`, `selected_backend=null`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 212 | False | `- `ask_repeat_threshold = -1.0`` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 218 | False | `1. If `no_speech_prob > 0.6` → `action = "ask_repeat"`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 220 | False | `2. Else if `avg_logprob < -1.0` → `action = "ask_repeat"`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 262 | False | `When `action == "ask_repeat"` the runtime SKIPS backend execution` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 263 | False | `and returns a response with `ask_repeat=true`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 269 | False | `to the local-first pathway (`ask_repeat` with` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 281 | False | ``deployable_actions = ["whisper_base_ct2_int8", "ask_repeat"]`;` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 300 | False | `- `ACTION_ASK_REPEAT = "ask_repeat"`` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 335 | False | `backend, or `null` when `ask_repeat=true`.` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 337 | False | `backend, or `null` when `ask_repeat=true`.` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 341 | False | `(still within `[0.0, 1.0]`); `null` when `ask_repeat=true` or` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 343 | False | `- `ask_repeat` — boolean. `true` whenever the selector branch is` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 348 | False | `ran; `null` when `ask_repeat=true`. No other value is permitted by` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 360 | False | `(`0` if `ask_repeat=true`).` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 396 | False | `falling back to `ask_repeat` and/or emitting a `response.errors`` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 411 | False | `### 5.2 Backend timeout maps to ask_repeat or response.errors` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 418 | False | `2. Set `selected_backend = null`, `ask_repeat = true`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 428 | False | `selector's `ask_repeat` action is the only legal fallback (no cloud` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 467 | False | `Response shaping: `ask_repeat=true`, `selected_backend=null`,` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 485 | False | ``ask_repeat=true`, `selected_backend=null`, etc.` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 491 | False | `returned `ask_repeat` because `no_speech_prob > 0.6` or` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 502 | False | `deterministic path. If the local path then yields an `ask_repeat`` |
| `artifacts/robust_asr/handoff/rp5_runtime_spec.md` | 528 | False | `| `ACTION_ASK_REPEAT = "ask_repeat"` | control action (not a backend); PRESENT as a deployable action | `selected_router/deterministic_selector.json` `deployable_actions` includes `ask_repeat`; no backend invocation required |` |
| `artifacts/robust_asr/handoff/selected_router/deterministic_selector.json` | 6 | False | `"ask_repeat_threshold": -1.0,` |
| `artifacts/robust_asr/handoff/selected_router/deterministic_selector.json` | 13 | False | `"ask_repeat"` |
| `artifacts/robust_asr/handoff/selected_router/metadata.json` | 2 | False | `"ask_repeat_supported": true,` |
| `artifacts/robust_asr/handoff/selected_router/rp5_inference.py` | 30 | False | `ACTION_ASK_REPEAT = "ask_repeat"` |
| `artifacts/robust_asr/handoff/selected_router/rp5_inference.py` | 67 | False | `ask_repeat_threshold = _CONSTANTS["ask_repeat_threshold"]` |
| `artifacts/robust_asr/handoff/selected_router/rp5_inference.py` | 76 | False | `if avg_logprob < ask_repeat_threshold:` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 3 | False | `"ask_repeat_threshold": -1.0,` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 18 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 28 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 58 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 68 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/handoff/selected_router/test_vectors.json` | 185 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/router/selected_router/deterministic_selector.json` | 6 | False | `"ask_repeat_threshold": -1.0,` |
| `artifacts/robust_asr/router/selected_router/deterministic_selector.json` | 13 | False | `"ask_repeat"` |
| `artifacts/robust_asr/router/selected_router/metadata.json` | 2 | False | `"ask_repeat_supported": true,` |
| `artifacts/robust_asr/router/selected_router/rp5_inference.py` | 30 | False | `ACTION_ASK_REPEAT = "ask_repeat"` |
| `artifacts/robust_asr/router/selected_router/rp5_inference.py` | 67 | False | `ask_repeat_threshold = _CONSTANTS["ask_repeat_threshold"]` |
| `artifacts/robust_asr/router/selected_router/rp5_inference.py` | 76 | False | `if avg_logprob < ask_repeat_threshold:` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 3 | False | `"ask_repeat_threshold": -1.0,` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 18 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 28 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 58 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 68 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/router/selected_router/test_vectors.json` | 185 | False | `"expected_action": "ask_repeat",` |
| `artifacts/robust_asr/runtime_contract/contract_smoke_job_metadata.json` | 2 | False | `"task_id": "P0.4",` |
| `artifacts/robust_asr/runtime_contract/final_response_fixture.json` | 7 | False | `"ask_repeat": false,` |
| `artifacts/robust_asr/runtime_contract/final_response_schema.json` | 5 | False | `"description": "Finalized RP5 ASR runtime response schema for the robust_asr deployable runtime. Produced by P9.0 under OUTCOME_E_DETERMINISTIC_SELECTOR. selected_backend is restricted to whisper_base_ct2_int8 (or null when ask_repeat=true)` |
| `artifacts/robust_asr/runtime_contract/final_response_schema.json` | 35 | False | `"ask_repeat",` |
| `artifacts/robust_asr/runtime_contract/final_response_schema.json` | 62 | False | `"ask_repeat": {` |
| `artifacts/robust_asr/runtime_contract/rp5_response_fixture.json` | 6 | False | `"ask_repeat": false,` |
| `artifacts/robust_asr/runtime_contract/stdout.txt` | 12 | False | `A11 PASS: response.ask_repeat=False` |
| `artifacts/robust_asr/runtime_contract/stdout.txt` | 13 | False | `A12 PASS: transcript_is_null=False ask_repeat=False errors_nonempty=False` |
| `artifacts/robust_asr/runtime_contract/stdout.txt` | 14 | False | `A13 PASS: selected_backend='whisper_base_ct2_int8' ask_repeat=False` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/approval_packet.yaml` | 6 | False | `task_id: P0.2` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 14 | False | `continue_without_per_task_plan_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 15 | False | `continue_without_per_task_closure_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 22 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 23 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.1_bootstrap.md` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 27 | False | `task_id: P0.2` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 28 | False | `task_title: Inventory existing assets and lock reuse policy` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 102 | False | `continue_without_per_task_plan_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 103 | False | `continue_without_per_task_closure_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 110 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/execution_report.yaml` | 111 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.2_asset_inventory.md` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/phase_gate_report.yaml` | 14 | False | `continue_without_per_task_plan_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/phase_gate_report.yaml` | 15 | False | `continue_without_per_task_closure_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/phase_gate_report.yaml` | 22 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/phase_gate_report.yaml` | 23 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.5_card_templates.md` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 14 | False | `continue_without_per_task_plan_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 15 | False | `continue_without_per_task_closure_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 22 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 23 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.1_bootstrap.md` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 29 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 32 | False | `task_id: P0.2` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 33 | False | `task_title: Inventory existing assets and lock reuse policy` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/planning_report.yaml` | 86 | False | `next_task_on_success: P0.3` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/supplemental_evidence_report.yaml` | 14 | False | `continue_without_per_task_plan_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/supplemental_evidence_report.yaml` | 15 | False | `continue_without_per_task_closure_approval: false` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/supplemental_evidence_report.yaml` | 22 | False | `requested_task_matches_tracker: true` |
| `artifacts/robust_asr/state_packets/report_shape_fixtures/supplemental_evidence_report.yaml` | 23 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.1_bootstrap.md` |
| `configs/robust_asr/eval_manifests_v1.yaml` | 91 | False | `api_key_env: ASSEMBLYAI_API_KEY` |
| `configs/robust_asr/eval_manifests_v1.yaml` | 96 | False | `ASSEMBLYAI_API_KEY is read from the environment only and is never` |
| `configs/robust_asr/reuse_policy_v1.yaml` | 131 | False | `action set under each profile, ask_repeat_wer_threshold,` |
| `configs/robust_asr/reuse_policy_v1.yaml` | 133 | False | `selector constants (ask_repeat_threshold=-1.0, escalate_threshold=-0.5,` |
| `configs/robust_asr/reuse_policy_v1.yaml` | 176 | False | `notes: Model card and router card templates (P0.5 seeded; finalized progressively). model_router_card_completion added under CHANGE_SCOPE on accepted_report_commit d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d to fill or N/A-rewrite every TODO_F` |
| `configs/robust_asr/reuse_policy_v1.yaml` | 470 | False | `validator: file_basename_matches_p<task_id>_*.sh` |
| `configs/robust_asr/reuse_policy_v1.yaml` | 477 | False | `p<task_id>_*.sh (e.g. p0_3_runtime_smoke.sh) under slurm/jobs/,` |
| `configs/robust_asr/router_v1.yaml` | 23 | False | `ask_repeat_threshold: -1.0     # avg_logprob below this -> ask_repeat` |
| `configs/robust_asr/router_v1.yaml` | 25 | False | `no_speech_threshold:   0.6     # no_speech_prob above this -> ask_repeat` |
| `configs/robust_asr/router_v1.yaml` | 45 | False | `battery_aware:   [whisper_base_ct2_int8, ask_repeat]` |
| `configs/robust_asr/router_v1.yaml` | 46 | False | `cloud_allowed:   [whisper_base_ct2_int8, assemblyai, ask_repeat]` |
| `configs/robust_asr/router_v1.yaml` | 47 | False | `lora_enabled:    [whisper_base_ct2_int8, whisper_lora_ct2_int8, ask_repeat]` |
| `configs/robust_asr/router_v1.yaml` | 48 | False | `full:            [whisper_base_ct2_int8, assemblyai, whisper_lora_ct2_int8, ask_repeat]` |
| `configs/robust_asr/router_v1.yaml` | 53 | False | `ask_repeat_wer_threshold: 0.6   # predicted WER above which ask_repeat is preferred` |
| `configs/robust_asr/router_v1.yaml` | 72 | False | `# deterministic selector reduces to whisper_base_ct2_int8 vs ask_repeat;` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 8 | False | `| 0.2  | done   | 2026-04-29 | Created docs/claude_task_progress.yaml and docs/claude_task_progress.md. |` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 28 | False | `| 4.2  | done    | 2026-04-30 | Files created: tests/integration/__init__.py, tests/integration/test_live_assemblyai.py (1 test: @pytest.mark.live_provider, module-level skip when RUN_LIVE_ASSEMBLYAI_TEST!=1 or ASSEMBLYAI_API_KEY missing, 1` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 37 | False | `| 6.3** | blocked    | 2026-04-30 | **WSL verification on commit 0db0a8b FAILED — propagation fix applied, awaiting re-verification.** WSL failure summary: API span and worker span both now appear in collector logs; `job.id` key is present;` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 38 | False | `| 6.3  | done        | 2026-04-30 | **Task 6.3 closed.** External WSL Docker OTel collector verification PASSED on commit 62c81da. Stack: `docker compose build --no-cache api worker` + `down -v` + `up -d postgres redis minio otel-collector`` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 40 | False | `| 6.4* | blocked     | 2026-04-30 | **WSL verification on commit 0f05dfb FAILED at the Docker pytest step; fix applied, awaiting re-verification.** WSL failure summary: stack came up, infra services started, migrations + bucket setup ok, pr` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 41 | False | `| 6.4  | blocked     | 2026-04-30 | **Task 6.4 implementation complete on datamove1; blocked pending WSL Docker verification.** Files created: infra/grafana/provisioning/datasources/prometheus.yml (uid: prometheus, url http://prometheus:909` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 43 | False | `| 7.2  | blocked     | 2026-04-30 | **Task 7.2 implementation complete on datamove1; blocked pending WSL Node + Docker verification.** Files modified: services/frontend/app/page.tsx (extended the existing client component with polling and a` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 45 | False | `| 7.1  | blocked     | 2026-04-30 | **Task 7.1 implementation complete on datamove1; blocked pending WSL Node verification.** Files created: services/frontend/package.json (next 14.2.15, react 18.3.1, react-dom 18.3.1, typescript 5.5.4, @ty` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 48 | False | `| 6.3*** | blocked   | 2026-04-30 | **WSL verification on commit 658c0d2 FAILED again — diagnostic logging + stronger test added; production still cannot be reproduced in tests.** WSL failure summary: stack came up healthy; POST /v1/transcr` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 214 | False | `echo "=== API diagnostic: api.task_enqueued ==="` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 215 | False | `docker compose logs api 2>&1 | grep '"event": "api.task_enqueued"' | tail -3` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 471 | False | `docs/claude_task_progress.md` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 472 | False | `docs/claude_task_progress.yaml` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 569 | False | `git add docs/claude_task_progress.md docs/claude_task_progress.yaml` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 578 | False | `- `docs/claude_task_progress.yaml`: `tasks."7.1": done`, `last_completed_task: "7.1"`, `current_task: "7.2"`, `blocked: false`, `blocker: null`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 579 | False | `- `docs/claude_task_progress.md`: append a `done` row for 7.1 citing WSL Node version, lockfile commit hash, lint/typecheck/build results, and pass/fail for each of the eleven manual checks. Check 10 must record the literal English message ` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 709 | False | `- `docs/claude_task_progress.yaml`: `tasks."7.2": done`, `last_completed_task: "7.2"`, `current_task: "7.3"`, `blocked: false`, `blocker: null`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 710 | False | `- `docs/claude_task_progress.md`: append a `done` row for 7.2 citing WSL Node version, `npm run lint/typecheck/build` outcomes, and pass/fail for each of the four manual checks. Check C must record the literal English message verified.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 909 | False | `- `docs/claude_task_progress.yaml`: set `tasks."7.3": done`, `last_completed_task: "7.3"`, `current_task: "8.1"`, `blocked: false`, `blocker: null`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 910 | False | `- `docs/claude_task_progress.md`: append a follow-up `done` row for 7.3 citing WSL Node version, `npm run typecheck/lint/build` outcomes, and pass/fail for each of the five Step 9 manual checks (Check 4 must record the literal English 429 m` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 924 | False | `- `docs/claude_task_progress.yaml` — set `tasks."8.1": blocked`, `blocked: true`, blocker description.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 925 | False | `- `docs/claude_task_progress.md` — this entry.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 985 | False | `- `docs/claude_task_progress.yaml`: set `tasks."8.1": done`, `last_completed_task: "8.1"`, `current_task: "8.2"`, `blocked: false`, `blocker: null`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 986 | False | `- `docs/claude_task_progress.md`: append a follow-up `done` row for 8.1 citing the GitHub Actions run URL/commit and per-job outcome.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1029 | False | `- `docs/claude_task_progress.yaml` — blocker text updated; `tasks."8.1"` remains `blocked`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1030 | False | `- `docs/claude_task_progress.md` — this entry.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1087 | False | `- `docs/smoke_tests.md` — new English smoke-test guide covering all five plan.md actions: Overview, Prerequisites, Where artifacts go, Start the stack, One-time stack setup (Alembic + MinIO bucket), Wait for readiness, Cut A smoke test, Enh` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1088 | False | `- `docs/claude_task_progress.yaml` — `tasks."8.2": blocked`, `blocked: true`, `blocker` describes the external WSL/Docker walk-through still required.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1089 | False | `- `docs/claude_task_progress.md` — this entry.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1100 | False | `- Live AssemblyAI test is opt-in and requires **both** `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<your-key>`. CI does not set the gate. The doc never prints a real key value.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1107 | False | `- All required commands present in `docs/smoke_tests.md`: `docker compose -f infra/compose/docker-compose.yml up -d --build`, `... run --rm --no-deps api alembic upgrade head`, `... run --rm --no-deps api python -c`, `pytest -q tests/smoke/` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1110 | False | `- No real `ASSEMBLYAI_API_KEY` value (only the placeholder `<your-key>`).` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1113 | False | `- `docs/claude_task_progress.yaml` parsed and verified: `tasks."8.1": done`, `tasks."8.2": blocked`, `current_task: "8.2"`, `last_completed_task: "8.1"`, `blocked: true`, `blocker` non-empty.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1114 | False | `- `docs/claude_task_progress.md` includes a `Task 8.2` heading.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1115 | False | `- `git status` + diff scope check: only the three planned paths are changed (`docs/smoke_tests.md`, `docs/claude_task_progress.md`, `docs/claude_task_progress.yaml`); `.codex` remains untracked and unstaged.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1203 | False | `- *real provider path has explicit environment gating* — documented as gated by both `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<your-key>`; CI does not set the gate; no real key value appears in any committed file.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1234 | False | `- `docs/claude_task_progress.md` — this section, appended.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1235 | False | `- `docs/claude_task_progress.yaml` — tracker flipped to `tasks."8.3": blocked`, `blocked: true`, with a `blocker` describing the missing external verification.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1246 | False | `- All required env-var names present: `ASR_PROVIDER`, `DATABASE_URL`, `REDIS_URL`, `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`, `ASSEMBLYAI_API_KEY`, `UPLOAD_LIMIT_BYTES`, `RATE_LIMIT_PER_MINUTE`` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1249 | False | `- No real-looking secret values: no `ASSEMBLYAI_API_KEY=[A-Za-z0-9]{16,}`; only placeholder or `minioadmin` values appear after `MINIO_SECRET_KEY=`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1252 | False | `- `docs/claude_task_progress.yaml` parsed and verified: `current_phase: 8`, `current_task: "8.3"`, `last_completed_task: "8.2"`, `tasks."8.3": blocked`, `blocked: true`, `blocker` non-empty.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1253 | False | `- `docs/claude_task_progress.md` includes the heading `## Task 8.3 — implemented (blocked)`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1254 | False | `- Exact changed-file allowlist: tracked + staged + untracked-non-`.codex` set equals exactly `docs/claude_task_progress.md`, `docs/claude_task_progress.yaml`, `docs/deployment.md`.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1318 | False | `- No real `ASSEMBLYAI_API_KEY` was used or printed; the live AssemblyAI test is **not required** to close Task 8.3.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1349 | False | `No real `ASSEMBLYAI_API_KEY` was used or printed. The live AssemblyAI test was not run because it is opt-in and not required for Task 8.3 closure.` |
| `docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md` | 1371 | False | `This is **documentation only**, not a new task. No `plan.md` task was added; the YAML tracker at `docs/claude_task_progress.yaml` is unchanged. Phase 8 / Cut C remains the final phase of the MVP, and `current_task` remains `null`.` |
| `docs/deployment.md` | 17 | False | `# edit .env: set MINIO_ACCESS_KEY, MINIO_SECRET_KEY, optionally ASSEMBLYAI_API_KEY` |
| `docs/deployment.md` | 95 | False | `| `ASSEMBLYAI_API_KEY` | only if `ASR_PROVIDER=assemblyai` | Placeholder `<assemblyai-api-key>` only; never committed |` |
| `docs/deployment.md` | 103 | False | `- On the VPS, copy `.env.example` to `.env`, then edit `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, and (only when `ASR_PROVIDER=assemblyai`) `ASSEMBLYAI_API_KEY` with values that are not stored in the repository.` |
| `docs/deployment.md` | 104 | False | `- Never commit a real `MINIO_SECRET_KEY` or `ASSEMBLYAI_API_KEY`. In this guide they appear only as placeholders: `<minio-access-key>`, `<minio-secret-key>`, `<assemblyai-api-key>`.` |
| `docs/deployment.md` | 107 | False | `- The live AssemblyAI smoke test in `docs/smoke_tests.md` is opt-in and gated by both `RUN_LIVE_ASSEMBLYAI_TEST=1` and `ASSEMBLYAI_API_KEY=<assemblyai-api-key>`. Closing the deployment task does not require running it.` |
| `docs/plans/archive/legacy_reference_plans/20260507T223435Z/demo_platform_plan.md` | 197 | False | `5. Trackers should live under `docs/progress/` to avoid mixing branch-specific progress with legacy `docs/claude_task_progress.*`.` |
| `docs/plans/archive/legacy_reference_plans/20260507T223435Z/demo_platform_plan.md` | 722 | False | `5. leave legacy `docs/claude_task_progress.*` untouched unless router note is needed.` |
| `docs/plans/archive/legacy_reference_plans/20260507T223435Z/training_datamove1_plan.md` | 501 | False | `4. If `docs/claude_task_progress.*` exists, leave it as legacy or root tracker and do not reuse it for the training branch.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 64 | False | `session_log.continue_without_per_task_plan_approval == true.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 182 | False | `task_id                (string or null)` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 211 | False | `1. Write phase_summary.<P_n>: "FAIL, failed_task=<task_id>,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 534 | False | `reports/robust_asr/task_reports/` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 624 | False | `docs/claude_task_progress.md` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 625 | False | `docs/claude_task_progress.yaml` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 925 | False | `ASSEMBLYAI_API_KEY and HF_TOKEN where explicitly noted).` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 989 | False | `selected_action, selector_reason, ask_repeat_allowed,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 992 | False | `whisper_lora_ct2_int8, ask_repeat}.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1050 | False | `ASSEMBLYAI_API_KEY, sk_, Bearer ).` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1082 | False | `reports/robust_asr/task_reports/.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1113 | False | `3. No residual TODO_FILLED_IN_<task_id> tokens for tasks whose` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1114 | False | `tracker.tasks[<task_id>].status == PASS.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1115 | False | `4. No secret-like tokens (ASSEMBLYAI_API_KEY, sk_, Bearer )` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1441 | False | `Reads:   ASSEMBLYAI_API_KEY from env. If unset, exit 8 with stderr` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1442 | False | `"ASSEMBLYAI_API_KEY_UNSET".` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1489 | False | `ask_repeat applied if min predicted_wer > ask_repeat_wer_threshold.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1508 | False | `is either whisper_base_ct2_int8 or ask_repeat. Records one row` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1634 | False | `(epsilon_wer, ask_repeat_wer_threshold,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1661 | False | `Behavior: Computes deterministic-selector WER, WA, ask_repeat_rate,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1753 | False | `Behavior: If ASSEMBLYAI_API_KEY env var is unset, prints` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1843 | False | `for a in available_actions_without_ask_repeat)` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1845 | False | `eligible = {a for a in available_actions_without_ask_repeat` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1856 | False | `if min_predicted_wer > ask_repeat_wer_threshold:` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1857 | False | `chosen = "ask_repeat"` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1860 | False | `chosen = "ask_repeat"` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1867 | False | `ask_repeat_wer_threshold = 0.350` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1928 | False | `ask_repeat_threshold=-1.0,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1933 | False | `Returns one of: 'whisper_base_ct2_int8', 'assemblyai', 'ask_repeat'.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1937 | False | `return 'ask_repeat'` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1938 | False | `if decode_features.get('avg_logprob', 0.0) < ask_repeat_threshold:` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1939 | False | `return 'ask_repeat'` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1948 | False | `ask_repeat_threshold  = -1.0` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 1958 | False | `AND ASSEMBLYAI_API_KEY env var set` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2263 | False | `continue_without_per_task_plan_approval: false` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2264 | False | `continue_without_per_task_closure_approval: false` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2328 | False | `task_reports_root:      { path: reports/robust_asr/task_reports, sha256: null, produced_by_task: P0.1 }` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2391 | False | `task_id:` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2398 | False | `next_task: <task_id>` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2428 | False | `narrative substeps `<task_id>a`, `<task_id>b` do not count.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2461 | False | `TODO_FILLED_IN_<task_id> placeholders` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2463 | False | `TODO_FILLED_IN_<task_id> placeholders` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2725 | False | `grep -rE 'ASSEMBLYAI_API_KEY|sk_|Bearer ' --exclude-dir=.git` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2859 | False | `14. Create reports/robust_asr/task_reports/.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2878 | False | `- reports/robust_asr/task_reports/` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2946 | False | `- docs/claude_task_progress.*` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 2985 | False | `docs/claude_task_progress.*) and existing plans (plan.md,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3005 | False | `task_id | allowed_write_paths | allowed_read_paths |` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3195 | False | `"ask_repeat": <bool>,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3219 | False | `11. response.ask_repeat is bool.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3220 | False | `12. (response.transcript is null) iff (response.ask_repeat == true OR errors non-empty).` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3221 | False | `13. response.selected_backend is null iff response.ask_repeat == true.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3278 | False | `Use TODO_FILLED_IN_<task_id> placeholders linked to the task that` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3285 | False | `Include at least 8 TODO_FILLED_IN_<task_id> placeholders.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 3839 | False | `set under each profile, ask_repeat_wer_threshold,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 4288 | False | `1. Residual TODO_FILLED_IN_<task_id> for closed task: status = FAIL,` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 4356 | False | `TODO_FILLED_IN_<task_id> for closed tasks.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 4358 | False | `TODO_FILLED_IN_<task_id> for closed tasks.` |
| `docs/plans/robust_asr_agent_plan_v3_4_7.md` | 4565 | False | `8  ASSEMBLYAI_API_KEY_UNSET` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 114 | False | `and docs/claude_task_progress.* are not robust_asr state.` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 221 | False | `The project is allowed to ship with Whisper base plus ask_repeat and a` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 279 | False | `| FAIL × OK × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, negative LoRA report |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 281 | False | `| FAIL × BLOCKED × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 283 | False | `| SMOKE_FAIL × OK × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, smoke negative report |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 285 | False | `| SMOKE_FAIL × BLOCKED × BLOCKED | E | base + ask_repeat + deterministic selector | base, deterministic selector, smoke negative report |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 287 | False | `| HALTED × OK × BLOCKED | E after orchestrator review | base + ask_repeat + deterministic selector | blocker report plus deterministic selector |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 289 | False | `| HALTED × BLOCKED × BLOCKED | E after orchestrator review | base + ask_repeat + deterministic selector | blocker report plus deterministic selector |` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 355 | False | `with their TODO_FILLED_IN_<task_id> placeholders,` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 732 | False | `1. Confirm task_id equals TRACKER-DERIVED NEXT TASK.` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 733 | False | `2. Confirm requested_task_matches_tracker == true.` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 756 | False | `1. Confirm task_id matches the approved task.` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 859 | False | `task_id                (string or null)` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 889 | False | `phase_summary.<P_n>: FAIL, failed_task=<task_id>, blocker=<marker_or_reason>` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 914 | False | `continue_without_per_task_plan_approval: true` |
| `docs/plans/robust_asr_orchestrator_plan_v3_4_7.md` | 915 | False | `continue_without_per_task_closure_approval: true` |
| `docs/plans/state_packet_schemas_v1.yaml` | 59 | False | `requested_task_matches_tracker:  { type: bool,              required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 60 | False | `latest_task_report_path:         { type: string_or_null,    required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 81 | False | `requested_task_matches_tracker: { type: bool,   required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 85 | False | `task_id:      { type: string,          required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 86 | False | `task_title:   { type: string,          required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 102 | False | `notes: "Each row is task_id from touch_policy.md" }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 129 | False | `next_task_on_success: { type: string,         required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 158 | False | `task_id:    { type: string, required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 159 | False | `task_title: { type: string, required: true }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 204 | False | `notes: "Verbatim YAML for tracker.tasks[task_id] and any decisions[*] updated" }` |
| `docs/plans/state_packet_schemas_v1.yaml` | 284 | False | `task_id:                { type: string_or_null, required: true }` |
| `docs/profiles/CLAUDE.demo.md` | 610 | False | `ASSEMBLYAI_API_KEY` |
| `docs/profiles/CLAUDE.robust_asr.md` | 79 | False | `docs/claude_task_progress.md` |
| `docs/profiles/CLAUDE.robust_asr.md` | 80 | False | `docs/claude_task_progress.yaml` |
| `docs/profiles/CLAUDE.training.md` | 317 | False | `#SBATCH --job-name=asr_<task_name>` |
| `docs/profiles/CLAUDE.training.md` | 587 | False | `ASSEMBLYAI_API_KEY` |
| `docs/progress/robust_asr_progress.md` | 9 | False | `- **CHANGE_SCOPE(`model_router_card_completion`) applied** on orchestrator-accepted_report_commit `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d`. Card-completion fix: replaced every `TODO_FILLED_IN_<task_id>` token in `docs/reports/robust_asr/m` |
| `docs/progress/robust_asr_progress.md` | 10 | False | `- **CHANGE_SCOPE(`reuse_policy_p10_2_script_allowance`) applied** on orchestrator-accepted_report_commit `9452afcf3c3f6b1874d86650724606d8e902b286`. Administrative policy fix: `configs/robust_asr/reuse_policy_v1.yaml` row `scripts/robust_as` |
| `docs/progress/robust_asr_progress.md` | 11 | False | `- **APPROVE_EXECUTION(P10.1) recorded** on accepted_report_commit `37a588b6aa4ee3116c32778092990b8dc9d023b0`. `current_task` advanced `P10.1 → P10.2`; `last_completed_task` advanced `P9_GATE → P10.1`; `state_transport.expected_next_task` ad` |
| `docs/progress/robust_asr_progress.md` | 12 | False | `- **P10.1 EXECUTED PASS under APPROVE_PLAN(P10.1)** on accepted_report_commit `d08dfa821957d4dfa5c3049fc1a60a850d2097ac`. Branch B (deterministic selector evidence path) under `OUTCOME_E_DETERMINISTIC_SELECTOR` + `BLOCKED_API` + `SKIPPED_BY` |
| `docs/progress/robust_asr_progress.md` | 13 | False | `- **PHASE_APPROVE(P9) recorded** on accepted_report_commit `a3c7d3713809e6d77e4d53e423cc50973b5fa5a4` (the P9_GATE attempt-1 gate-evidence commit). `current_task` advanced `P9_GATE → P10.1`; `last_completed_task` advanced `P9.2 → P9_GATE`; ` |
| `docs/progress/robust_asr_progress.md` | 14 | False | `- **P9_GATE attempt 1 PASS — `phase_summary.P9` advanced to `PASS`; awaiting orchestrator `PHASE_APPROVE(P9)`.** Under orchestrator `APPROVE_PLAN(P9_GATE)` on accepted_report_commit `ec9b7caea99c27d63fca3cb458eca8f06e7f6260`, the P9 gate pr` |
| `docs/progress/robust_asr_progress.md` | 16 | False | `- **FIX_BEFORE_CLOSE(P9.2) applied — strict handoff-tag validator now passes A1–A7.** Orchestrator returned `FIX_BEFORE_CLOSE` on accepted_report_commit `f900d80837cc23dd5289c0bdb5630009c6e9b9af` after P9.2 surfaced that `scripts/robust_asr` |
| `docs/progress/robust_asr_progress.md` | 23 | False | `- Handoff scope: deployable backend = `whisper_base_ct2_int8` only; `router_kind` = `deterministic_selector`. LoRA excluded (`SKIPPED_BY_DECISION_A`; `claims_enabled.positive_lora=false`; no `lora_ct2_int8/` dir in handoff). AssemblyAI excl` |
| `docs/progress/robust_asr_progress.md` | 49 | False | `- claims_enabled.cloud_tradeoff: false (set by P5.1 BLOCKED_API; ASSEMBLYAI_API_KEY unset)` |
| `docs/progress/robust_asr_progress.md` | 68 | False | `- state_transport.latest_phase_gate_report: reports/robust_asr/task_reports/P8_GATE_attempt2.md` |
| `docs/progress/robust_asr_progress.md` | 136 | False | `- `reports/robust_asr/task_reports/P10.1_final_verification.md` (sha256 `ed7b149b29924c20f8ddeb5139494ad5e75e6d06fc530120efe1cc810a2d80ea`).` |
| `docs/progress/robust_asr_progress.md` | 170 | False | `- `state_transport.latest_planning_report` and `.latest_execution_report` → `reports/robust_asr/task_reports/P10.1_final_verification.md`.` |
| `docs/progress/robust_asr_progress.md` | 208 | False | `- `state_transport.latest_phase_gate_report = reports/robust_asr/task_reports/P9_GATE_attempt1.md` (held).` |
| `docs/progress/robust_asr_progress.md` | 235 | False | `- `reports/robust_asr/task_reports/P9_GATE_attempt1.md`, `P9.0_runtime_contract.md`, `P9.1_handoff_package.md`, `P9.2_rp5_runtime_spec.md`, `P9.2_strict_tag_validator_fix.md`, `P8_GATE_attempt2.md` — byte-unchanged.` |
| `docs/progress/robust_asr_progress.md` | 274 | False | `- `tasks.P9_GATE` added: `attempt=1`, `status=PASS`, full `predicate_inputs` block with the 12 observed values and PASS/FAIL flags, `report=reports/robust_asr/task_reports/P9_GATE_attempt1.md`, `files_changed`, `commands_run`, `key_outputs`` |
| `docs/progress/robust_asr_progress.md` | 276 | False | `- `state_transport.latest_phase_gate_report`: `reports/robust_asr/task_reports/P8_GATE_attempt2.md` → **`reports/robust_asr/task_reports/P9_GATE_attempt1.md`**.` |
| `docs/progress/robust_asr_progress.md` | 309 | False | `- `reports/robust_asr/task_reports/P9.0_runtime_contract.md`, `P9.1_handoff_package.md`, `P9.2_rp5_runtime_spec.md`, `P9.2_strict_tag_validator_fix.md`, `P8_GATE_attempt2.md` — byte-unchanged.` |
| `docs/progress/robust_asr_progress.md` | 335 | False | `- `state_transport.latest_phase_gate_report`: `reports/robust_asr/task_reports/P8_GATE_attempt2.md` — held.` |
| `docs/progress/robust_asr_progress.md` | 359 | False | `- `reports/robust_asr/task_reports/P8.1_system_eval.md`, `reports/robust_asr/task_reports/P8.2_demo_manifest.md`, `reports/robust_asr/task_reports/P8_GATE_attempt2.md` — byte-unchanged.` |
| `docs/progress/robust_asr_progress.md` | 388 | False | `- `state_transport.latest_phase_gate_report`: `null` → **`reports/robust_asr/task_reports/P8_GATE_attempt2.md`**.` |
| `docs/progress/robust_asr_progress.md` | 415 | False | `- `reports/robust_asr/task_reports/P8.1_system_eval.md` and `reports/robust_asr/task_reports/P8.2_demo_manifest.md` — byte-unchanged.` |
| `docs/progress/robust_asr_progress.md` | 441 | False | `- `reports/robust_asr/task_reports/plan_index_refresh.md`: compact evidence report written for this scope change.` |
| `docs/progress/robust_asr_progress.md` | 468 | False | `- No P8 evidence files; no demo audio bytes; no manifest; no `build_demo_examples.py`; no `tests/robust_asr/test_leakage.py`; no `reports/robust_asr/system/system_eval.md`; no `reports/robust_asr/demo/provenance_audit.md`; no `reports/robus` |
| `docs/progress/robust_asr_progress.md` | 550 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md` — status header changed to `IMPLEMENTED_PENDING_APPROVAL` under enacted demo-only deviation; new "Update — P8.2-deviation enactment (demo-only upstream overlap accepted)" section app` |
| `docs/progress/robust_asr_progress.md` | 716 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md` — new "Update — P8.2-upstream-leakage-audit (re-HALT after upstream overlap detected)" section appended; status header changed to `HALTED — DEMO_UPSTREAM_LOCKED_OVERLAP`.` |
| `docs/progress/robust_asr_progress.md` | 784 | False | ``reports/robust_asr/task_reports/P8.2_demo_manifest.md` updated with a new "Update — P8.2-provenance-rerun (provenance repaired from asr-rp5 evidence)" section; status header changed to `IMPLEMENTED_PENDING_APPROVAL`.` |
| `docs/progress/robust_asr_progress.md` | 905 | False | `- `reports/robust_asr/touch_policy.md` P8.2 row amended — `allowed_write_paths` now also includes `reports/robust_asr/demo/provenance_audit.md` (the public-corpus / license / upstream-attribution audit required for P9.1 handoff and P10 fina` |
| `docs/progress/robust_asr_progress.md` | 942 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md` (new): full report.` |
| `docs/progress/robust_asr_progress.md` | 997 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md`` |
| `docs/progress/robust_asr_progress.md` | 1214 | False | `- `reports/robust_asr/task_reports/P7.3_router_package.md`.` |
| `docs/progress/robust_asr_progress.md` | 1225 | False | `(99.9474 %), `ask_repeat` 28 (0.0526 %), `assemblyai` 0,` |
| `docs/progress/robust_asr_progress.md` | 1233 | False | ``ask_repeat` rows already have `baseline_wer = 1.0`); Wilcoxon` |
| `docs/progress/robust_asr_progress.md` | 1321 | False | `- `reports/robust_asr/task_reports/P7.3_router_package.md`` |
| `docs/progress/robust_asr_progress.md` | 1577 | False | `- `reports/robust_asr/task_reports/P6.1_selector_evidence.md` (sha256` |
| `docs/progress/robust_asr_progress.md` | 1590 | False | `(`selector_reason=baseline`) + 28 `ask_repeat`` |
| `docs/progress/robust_asr_progress.md` | 1595 | False | ``ask_repeat_allowed=True` on every row.` |
| `docs/progress/robust_asr_progress.md` | 1613 | False | ``P6_1_task_report` recorded with sha256s;` |
| `docs/progress/robust_asr_progress.md` | 1670 | False | ``reports/robust_asr/task_reports/P6.1_selector_evidence.md`,` |
| `docs/progress/robust_asr_progress.md` | 1794 | False | ``ASSEMBLYAI_API_KEY` was unset, no HTTP request or paid API call was` |
| `docs/progress/robust_asr_progress.md` | 1828 | False | ``ASSEMBLYAI_RUNTIME=false reason=key_unset`. `ASSEMBLYAI_API_KEY` is` |
| `docs/progress/robust_asr_progress.md` | 1838 | False | ``reports/robust_asr/task_reports/P5.1_assemblyai.md`. No` |
| `docs/progress/robust_asr_progress.md` | 1842 | False | `exit 8 = `ASSEMBLYAI_API_KEY_UNSET`;` |
| `docs/progress/robust_asr_progress.md` | 1849 | False | ``ASSEMBLYAI_API_KEY` is read from the environment only and is never` |
| `docs/progress/robust_asr_progress.md` | 1917 | False | ``reports/robust_asr/task_reports/P5.1_assemblyai.md`,` |
| `docs/progress/robust_asr_progress.md` | 1923 | False | ``ASSEMBLYAI_API_KEY` from environment only (never logged or persisted);` |
| `docs/progress/robust_asr_progress.md` | 2055 | False | `- `reports/robust_asr/task_reports/P3.2_decision_a.md`` |
| `docs/progress/robust_asr_progress.md` | 2101 | False | ``reports/robust_asr/task_reports/P3.2_decision_a.md`,` |
| `docs/progress/robust_asr_progress.md` | 2217 | False | `reproducibility): see `reports/robust_asr/task_reports/P3.1_lora_smoke.md`` |
| `docs/progress/robust_asr_progress.md` | 2233 | False | ``c5eac79f…721be`), `reports/robust_asr/task_reports/P3.1_lora_smoke.md`,` |
| `docs/progress/robust_asr_progress.md` | 2321 | False | ``reports/robust_asr/task_reports/P3.1_lora_smoke.md`,` |
| `docs/progress/robust_asr_progress.md` | 2534 | False | ``tasks.P2.2.artifacts_added.{lora_smoke_config, p2_2_task_report}`` |
| `docs/progress/robust_asr_progress.md` | 2567 | False | ``reports/robust_asr/task_reports/P2.2_lora_smoke_config.md`, but the` |
| `docs/progress/robust_asr_progress.md` | 2574 | False | ``reports/robust_asr/task_reports/P2.2_lora_smoke_config.md`,` |
| `docs/progress/robust_asr_progress.md` | 2911 | False | `- `reports/robust_asr/task_reports/P2.1_baseline.md`` |
| `docs/progress/robust_asr_progress.md` | 2974 | False | ``reports/robust_asr/task_reports/P2.1_baseline.md`,` |
| `docs/progress/robust_asr_progress.md` | 3094 | False | `- `reports/robust_asr/task_reports/P1.4_degradation_v1.md`.` |
| `docs/progress/robust_asr_progress.md` | 3175 | False | ``reports/robust_asr/task_reports/P1.4_degradation_v1.md`,` |
| `docs/progress/robust_asr_progress.md` | 3223 | False | `- `reports/robust_asr/task_reports/P1.3_manifest_summary.md`.` |
| `docs/progress/robust_asr_progress.md` | 3282 | False | ``reports/robust_asr/task_reports/P1.3_manifest_summary.md`,` |
| `docs/progress/robust_asr_progress.md` | 3346 | False | ``reports/robust_asr/task_reports/P1.2_eval_schema.md`.` |
| `docs/progress/robust_asr_progress.md` | 3428 | False | ``reports/robust_asr/task_reports/P1.2_eval_schema.md`, scope-change` |
| `docs/progress/robust_asr_progress.md` | 3499 | False | `- P0.5 PASS: Model card and router card templates. `docs/reports/robust_asr/model_card_lora.md` (9 sections; 30 `TODO_FILLED_IN_<task_id>` placeholders, ≥ 10 required; sha256 `6f1a6ba8...`) and `docs/reports/robust_asr/router_card.md` (9 se` |
| `docs/progress/robust_asr_progress.md` | 3513 | False | ``reports/robust_asr/task_reports/P1.1_data_inventory.md`,` |
| `docs/progress/robust_asr_progress.md` | 3534 | False | `robust_asr `p<task_id>_*.sh` scripts (permitted_use=read_only_with_robust_asr_writes).` |
| `docs/progress/robust_asr_progress.md` | 3555 | False | ``reports/robust_asr/task_reports/P0.3_runtime_smoke.md`,` |
| `docs/progress/robust_asr_progress.yaml` | 40 | False | `continue_without_per_task_plan_approval: false` |
| `docs/progress/robust_asr_progress.yaml` | 41 | False | `continue_without_per_task_closure_approval: false` |
| `docs/progress/robust_asr_progress.yaml` | 47 | False | `latest_planning_report: reports/robust_asr/task_reports/P10.1_final_verification.md` |
| `docs/progress/robust_asr_progress.yaml` | 48 | False | `latest_execution_report: reports/robust_asr/task_reports/P10.1_final_verification.md` |
| `docs/progress/robust_asr_progress.yaml` | 49 | False | `prior_execution_report_p9_2: reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` |
| `docs/progress/robust_asr_progress.yaml` | 50 | False | `prior_execution_report_p9_2_strict_tag_validator_fix: reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` |
| `docs/progress/robust_asr_progress.yaml` | 51 | False | `latest_phase_gate_report: reports/robust_asr/task_reports/P9_GATE_attempt1.md` |
| `docs/progress/robust_asr_progress.yaml` | 56 | False | `task_id: P10.1` |
| `docs/progress/robust_asr_progress.yaml` | 66 | False | `task_id: P10.1` |
| `docs/progress/robust_asr_progress.yaml` | 76 | False | `task_id: P9_GATE` |
| `docs/progress/robust_asr_progress.yaml` | 86 | False | `task_id: P9_GATE` |
| `docs/progress/robust_asr_progress.yaml` | 96 | False | `task_id: P9.2` |
| `docs/progress/robust_asr_progress.yaml` | 106 | False | `task_id: P9.2` |
| `docs/progress/robust_asr_progress.yaml` | 116 | False | `task_id: P9.1` |
| `docs/progress/robust_asr_progress.yaml` | 126 | False | `task_id: P9.1` |
| `docs/progress/robust_asr_progress.yaml` | 136 | False | `task_id: P9.0` |
| `docs/progress/robust_asr_progress.yaml` | 146 | False | `task_id: P9.0` |
| `docs/progress/robust_asr_progress.yaml` | 156 | False | `task_id: P8_GATE` |
| `docs/progress/robust_asr_progress.yaml` | 166 | False | `task_id: P8_GATE` |
| `docs/progress/robust_asr_progress.yaml` | 176 | False | `task_id: plan_index_refresh` |
| `docs/progress/robust_asr_progress.yaml` | 186 | False | `task_id: P8.2` |
| `docs/progress/robust_asr_progress.yaml` | 196 | False | `task_id: P8.2-deviation` |
| `docs/progress/robust_asr_progress.yaml` | 206 | False | `task_id: P8.2-deviation` |
| `docs/progress/robust_asr_progress.yaml` | 212 | False | `rationale: "Enact the authorized demo-only deviation. Add top-level deviation block to artifacts/robust_asr/demo/demo_examples_manifest.json (deviation_id=P8_2_demo_only_upstream_overlap, deviation_status=approved_for_demo_only_use_pending_` |
| `docs/progress/robust_asr_progress.yaml` | 216 | False | `task_id: P8.2-deviation-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 226 | False | `task_id: P8.2-deviation` |
| `docs/progress/robust_asr_progress.yaml` | 236 | False | `task_id: P8.2-upstream-leakage-audit` |
| `docs/progress/robust_asr_progress.yaml` | 246 | False | `task_id: P8.2-provenance-rerun` |
| `docs/progress/robust_asr_progress.yaml` | 256 | False | `task_id: P8.2-provenance` |
| `docs/progress/robust_asr_progress.yaml` | 266 | False | `task_id: P8.2-provenance` |
| `docs/progress/robust_asr_progress.yaml` | 276 | False | `task_id: P8.2-provenance-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 286 | False | `task_id: P8.2-provenance` |
| `docs/progress/robust_asr_progress.yaml` | 296 | False | `task_id: P8.2` |
| `docs/progress/robust_asr_progress.yaml` | 306 | False | `task_id: P8.2-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 316 | False | `task_id: P8.2` |
| `docs/progress/robust_asr_progress.yaml` | 326 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 336 | False | `task_id: P8.1` |
| `docs/progress/robust_asr_progress.yaml` | 346 | False | `task_id: P8.1` |
| `docs/progress/robust_asr_progress.yaml` | 352 | False | `rationale: "P8.1 plan approved on the YAML-parse-fix commit f23a270. Implement scripts/robust_asr/evaluate_system.py, slurm/jobs/p8_1_system_eval.sh, reports/robust_asr/system/system_eval.md, and reports/robust_asr/task_reports/P8.1_system_` |
| `docs/progress/robust_asr_progress.yaml` | 356 | False | `task_id: P8.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 366 | False | `task_id: P8.1` |
| `docs/progress/robust_asr_progress.yaml` | 376 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 386 | False | `task_id: P7.3` |
| `docs/progress/robust_asr_progress.yaml` | 396 | False | `task_id: P7.3` |
| `docs/progress/robust_asr_progress.yaml` | 402 | False | `rationale: "P7.3 plan approved on the P7.3 scope-change commit 394df2d. Implement scripts/robust_asr/package_deterministic_selector.py, scripts/robust_asr/evaluate_deterministic_selector.py, tests/robust_asr/test_router_runtime.py, the arti` |
| `docs/progress/robust_asr_progress.yaml` | 406 | False | `task_id: P7.3-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 416 | False | `task_id: P7.3` |
| `docs/progress/robust_asr_progress.yaml` | 426 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 436 | False | `task_id: P6.1` |
| `docs/progress/robust_asr_progress.yaml` | 446 | False | `task_id: P6.1` |
| `docs/progress/robust_asr_progress.yaml` | 452 | False | `rationale: "P6.1 plan approved on the P6.1 scope-change commit 4a9f9291. Implement configs/robust_asr/router_v1.yaml, append DETERMINISTIC_SELECTOR_VERSION to libs/common/versions.py, create scripts/robust_asr/build_selector_evidence_table.` |
| `docs/progress/robust_asr_progress.yaml` | 456 | False | `task_id: P6.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 466 | False | `task_id: P6.1` |
| `docs/progress/robust_asr_progress.yaml` | 476 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 486 | False | `task_id: P5.1` |
| `docs/progress/robust_asr_progress.yaml` | 492 | False | `rationale: "P5.1 legally halted with BLOCKED_API reason=key_unset. ASSEMBLYAI_API_KEY was unset, no HTTP request or paid API call was made, pricing guard and tests passed, claims_enabled.cloud_tradeoff=false was set, and BLOCKED_OOD_PUBLIC ` |
| `docs/progress/robust_asr_progress.yaml` | 496 | False | `task_id: P5.1` |
| `docs/progress/robust_asr_progress.yaml` | 502 | False | `rationale: "P5.1 plan approved on the scope-change-packet commit. Implement configs/robust_asr/pricing_v1.yaml, scripts/robust_asr/{probe_assemblyai_runtime,populate_assemblyai_cache,evaluate_assemblyai_from_cache}.py, tests/robust_asr/test` |
| `docs/progress/robust_asr_progress.yaml` | 506 | False | `task_id: P5.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 516 | False | `task_id: P5.1` |
| `docs/progress/robust_asr_progress.yaml` | 526 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 536 | False | `task_id: P3.2` |
| `docs/progress/robust_asr_progress.yaml` | 546 | False | `task_id: P3.2` |
| `docs/progress/robust_asr_progress.yaml` | 556 | False | `task_id: P3.2-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 566 | False | `task_id: P3.2` |
| `docs/progress/robust_asr_progress.yaml` | 576 | False | `task_id: P3.1` |
| `docs/progress/robust_asr_progress.yaml` | 586 | False | `task_id: P3.1` |
| `docs/progress/robust_asr_progress.yaml` | 592 | False | `rationale: "P3.1 plan accepted on the scope-change commit; implement scripts/robust_asr/{train_lora_smoke,evaluate_lora_smoke,smoke_export_lora_ct2}.py, slurm/jobs/p3_1_lora_smoke.sh, tests/robust_asr/test_lora_smoke.py; run Slurm via slurm` |
| `docs/progress/robust_asr_progress.yaml` | 596 | False | `task_id: P3.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 606 | False | `task_id: P3.1` |
| `docs/progress/robust_asr_progress.yaml` | 616 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 626 | False | `task_id: P2.2` |
| `docs/progress/robust_asr_progress.yaml` | 636 | False | `task_id: P2.2` |
| `docs/progress/robust_asr_progress.yaml` | 646 | False | `task_id: P2.2-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 652 | False | `rationale: "P2.2 scope-change accepted at commit d78678a; rewritten touch_policy P2.2 row authorizing configs/robust_asr/lora_smoke.yaml, reports/robust_asr/task_reports/P2.2_lora_smoke_config.md, and the read paths required for manifest-me` |
| `docs/progress/robust_asr_progress.yaml` | 656 | False | `task_id: P2.2` |
| `docs/progress/robust_asr_progress.yaml` | 666 | False | `task_id: P2.1` |
| `docs/progress/robust_asr_progress.yaml` | 676 | False | `task_id: P2.1-rerun` |
| `docs/progress/robust_asr_progress.yaml` | 686 | False | `task_id: P2.1-model-build` |
| `docs/progress/robust_asr_progress.yaml` | 696 | False | `task_id: P2.1-model-build` |
| `docs/progress/robust_asr_progress.yaml` | 706 | False | `task_id: P2.1-model-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 716 | False | `task_id: P2.1-model` |
| `docs/progress/robust_asr_progress.yaml` | 726 | False | `task_id: P2.1` |
| `docs/progress/robust_asr_progress.yaml` | 736 | False | `task_id: P2.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 746 | False | `task_id: P2.1` |
| `docs/progress/robust_asr_progress.yaml` | 756 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 766 | False | `task_id: P1.4` |
| `docs/progress/robust_asr_progress.yaml` | 776 | False | `task_id: P1.4` |
| `docs/progress/robust_asr_progress.yaml` | 786 | False | `task_id: P1.4-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 796 | False | `task_id: P1.4` |
| `docs/progress/robust_asr_progress.yaml` | 806 | False | `task_id: P1.3` |
| `docs/progress/robust_asr_progress.yaml` | 816 | False | `task_id: P1.3` |
| `docs/progress/robust_asr_progress.yaml` | 826 | False | `task_id: P1.3-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 836 | False | `task_id: P1.3` |
| `docs/progress/robust_asr_progress.yaml` | 846 | False | `task_id: P1.2` |
| `docs/progress/robust_asr_progress.yaml` | 856 | False | `task_id: P1.2` |
| `docs/progress/robust_asr_progress.yaml` | 866 | False | `task_id: P1.2-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 876 | False | `task_id: P1.2` |
| `docs/progress/robust_asr_progress.yaml` | 886 | False | `task_id: P1.1` |
| `docs/progress/robust_asr_progress.yaml` | 896 | False | `task_id: P1.1` |
| `docs/progress/robust_asr_progress.yaml` | 906 | False | `task_id: P1.1-scope-change` |
| `docs/progress/robust_asr_progress.yaml` | 916 | False | `task_id: P1.1` |
| `docs/progress/robust_asr_progress.yaml` | 926 | False | `task_id: null` |
| `docs/progress/robust_asr_progress.yaml` | 936 | False | `task_id: P0.5` |
| `docs/progress/robust_asr_progress.yaml` | 946 | False | `task_id: P0.5` |
| `docs/progress/robust_asr_progress.yaml` | 956 | False | `task_id: P0.4` |
| `docs/progress/robust_asr_progress.yaml` | 966 | False | `task_id: P0.4` |
| `docs/progress/robust_asr_progress.yaml` | 976 | False | `task_id: P0.3-rerun-2` |
| `docs/progress/robust_asr_progress.yaml` | 986 | False | `task_id: P0.3-rerun-2` |
| `docs/progress/robust_asr_progress.yaml` | 999 | False | `task_id: model_router_card_completion` |
| `docs/progress/robust_asr_progress.yaml` | 1004 | False | `required_fix: "Complete docs/reports/robust_asr/model_card_lora.md and docs/reports/robust_asr/router_card.md before P10.2 final_asset_audit.py runs, because the active plan Section 10 items 11-12 require no residual TODO_FILLED_IN_<task_id` |
| `docs/progress/robust_asr_progress.yaml` | 1007 | False | `report: reports/robust_asr/task_reports/model_router_card_completion.md` |
| `docs/progress/robust_asr_progress.yaml` | 1052 | False | `task_id: reuse_policy_p10_2_script_allowance` |
| `docs/progress/robust_asr_progress.yaml` | 1060 | False | `report: reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` |
| `docs/progress/robust_asr_progress.yaml` | 1125 | False | `task_reports_root:` |
| `docs/progress/robust_asr_progress.yaml` | 1126 | False | `path: reports/robust_asr/task_reports` |
| `docs/progress/robust_asr_progress.yaml` | 1163 | False | `change: "docs/reports/robust_asr/** allowed_tasks extended by [model_router_card_completion]; row class/permitted_use/no-touch unchanged; notes annotated. Authorizes the same task to fill or N/A-rewrite every TODO_FILLED_IN_<task_id> placeh` |
| `docs/progress/robust_asr_progress.yaml` | 1238 | False | `completion_evidence: "All TODO_FILLED_IN_<task_id> tokens (P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P3.2, P4.1, P4.2, P4.3, P5.1, P8.1, P8.2, P9.1) replaced with concise PASS / PARTIAL / N/A statements per the orchestrator-issued source mappings` |
| `docs/progress/robust_asr_progress.yaml` | 1249 | False | `completion_evidence: "All TODO_FILLED_IN_<task_id> tokens (P1.3, P5.1, P6.1, P6.2, P7.1, P7.2, P7.3, P8.1, P8.2, P9.1) replaced with concise PASS / PARTIAL / N/A statements per the orchestrator-issued source mappings. PASS tasks cite their ` |
| `docs/progress/robust_asr_progress.yaml` | 1431 | False | `path: reports/robust_asr/task_reports/P3.1_lora_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 1498 | False | `P6_1_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 1499 | False | `path: reports/robust_asr/task_reports/P6.1_selector_evidence.md` |
| `docs/progress/robust_asr_progress.yaml` | 1542 | False | `P7_3_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 1543 | False | `path: reports/robust_asr/task_reports/P7.3_router_package.md` |
| `docs/progress/robust_asr_progress.yaml` | 1565 | False | `P8_1_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 1566 | False | `path: reports/robust_asr/task_reports/P8.1_system_eval.md` |
| `docs/progress/robust_asr_progress.yaml` | 1636 | False | `notes: "Final runtime contract artifacts produced by P9.0. Synthetic fixtures (NOT derived from demo audio, demo manifest rows, demo audio_id, demo upstream_audio_id, demo speaker_id, or demo WAV hashes). selected_backend restricted to whis` |
| `docs/progress/robust_asr_progress.yaml` | 1739 | False | `rationale: "Section 5.6 predicate evaluated on selector_evidence (53,230 rows) against the single declared baseline whisper_base_ct2_int8 under OUTCOME_E_DETERMINISTIC_SELECTOR. Primary policy ask_repeat_wer=1.0: all 28 ask_repeat rows alre` |
| `docs/progress/robust_asr_progress.yaml` | 1793 | False | `- reports/robust_asr/task_reports/P0.1_bootstrap.md` |
| `docs/progress/robust_asr_progress.yaml` | 1850 | False | `- reports/robust_asr/task_reports/P0.2_asset_inventory.md` |
| `docs/progress/robust_asr_progress.yaml` | 1888 | False | `- reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 1906 | False | `- "Write reports/robust_asr/task_reports/P0.3_runtime_smoke.md"` |
| `docs/progress/robust_asr_progress.yaml` | 1934 | False | `parent_task_id: P0.3` |
| `docs/progress/robust_asr_progress.yaml` | 1941 | False | `- reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` |
| `docs/progress/robust_asr_progress.yaml` | 1977 | False | `parent_task_id: P0.3` |
| `docs/progress/robust_asr_progress.yaml` | 1985 | False | `- reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 1998 | False | `- "Write reports/robust_asr/task_reports/P0.3_runtime_smoke.md (rerun HALTED execution report)"` |
| `docs/progress/robust_asr_progress.yaml` | 2023 | False | `parent_task_id: P0.3` |
| `docs/progress/robust_asr_progress.yaml` | 2030 | False | `- reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 2043 | False | `- "Write reports/robust_asr/task_reports/P0.3_runtime_smoke.md (PASS)"` |
| `docs/progress/robust_asr_progress.yaml` | 2083 | False | `- reports/robust_asr/task_reports/P0.4_runtime_contract.md` |
| `docs/progress/robust_asr_progress.yaml` | 2100 | False | `- "Write reports/robust_asr/task_reports/P0.4_runtime_contract.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2135 | False | `- reports/robust_asr/task_reports/P0.5_card_templates.md` |
| `docs/progress/robust_asr_progress.yaml` | 2147 | False | `- "Write reports/robust_asr/task_reports/P0.5_card_templates.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2169 | False | `- reports/robust_asr/task_reports/P1.1_data_inventory.md   # rewritten` |
| `docs/progress/robust_asr_progress.yaml` | 2186 | False | `- "Write reports/robust_asr/task_reports/P1.1_data_inventory.md (rerun)"` |
| `docs/progress/robust_asr_progress.yaml` | 2230 | False | `- reports/robust_asr/task_reports/P1.2_eval_schema.md` |
| `docs/progress/robust_asr_progress.yaml` | 2248 | False | `- "Write reports/robust_asr/task_reports/P1.2_eval_schema.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2274 | False | `- reports/robust_asr/task_reports/P1.3_manifest_summary.md` |
| `docs/progress/robust_asr_progress.yaml` | 2288 | False | `- "Write reports/robust_asr/task_reports/P1.3_manifest_summary.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2333 | False | `- reports/robust_asr/task_reports/P1.4_degradation_v1.md` |
| `docs/progress/robust_asr_progress.yaml` | 2352 | False | `- "Write reports/robust_asr/task_reports/P1.4_degradation_v1.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2402 | False | `- reports/robust_asr/task_reports/P2.1_baseline.md` |
| `docs/progress/robust_asr_progress.yaml` | 2417 | False | `- "Write reports/robust_asr/task_reports/P2.1_baseline.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2550 | False | `- reports/robust_asr/task_reports/P2.2_lora_smoke_config.md` |
| `docs/progress/robust_asr_progress.yaml` | 2563 | False | `- "Write reports/robust_asr/task_reports/P2.2_lora_smoke_config.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2594 | False | `p2_2_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 2595 | False | `path: reports/robust_asr/task_reports/P2.2_lora_smoke_config.md` |
| `docs/progress/robust_asr_progress.yaml` | 2633 | False | `- reports/robust_asr/task_reports/P3.1_lora_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 2650 | False | `- "Write reports/robust_asr/task_reports/P3.1_lora_smoke.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2660 | False | `- "Five Slurm iterations to reach PASS: 2131879 (HF cache offline lookup), 2131884 (config.json missing), 2131889 (PEFT task_type forwards input_ids), 2131891 (eval_audio_id key mismatch), 2131897 (export dtype kwarg), 2131908 (merged_fp16 ` |
| `docs/progress/robust_asr_progress.yaml` | 2756 | False | `p3_1_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 2757 | False | `path: reports/robust_asr/task_reports/P3.1_lora_smoke.md` |
| `docs/progress/robust_asr_progress.yaml` | 2771 | False | `- reports/robust_asr/task_reports/P3.2_decision_a.md` |
| `docs/progress/robust_asr_progress.yaml` | 2785 | False | `- "Write reports/robust_asr/task_reports/P3.2_decision_a.md"` |
| `docs/progress/robust_asr_progress.yaml` | 2822 | False | `p3_2_task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 2823 | False | `path: reports/robust_asr/task_reports/P3.2_decision_a.md` |
| `docs/progress/robust_asr_progress.yaml` | 2878 | False | `- reports/robust_asr/task_reports/P5.1_assemblyai.md` |
| `docs/progress/robust_asr_progress.yaml` | 2888 | False | `- "BLOCKED_API recorded: ASSEMBLYAI_API_KEY unset on datamove1; no AssemblyAI request issued"` |
| `docs/progress/robust_asr_progress.yaml` | 2921 | False | `task_report:` |
| `docs/progress/robust_asr_progress.yaml` | 2922 | False | `path: reports/robust_asr/task_reports/P5.1_assemblyai.md` |
| `docs/progress/robust_asr_progress.yaml` | 2949 | False | `- "rewrite P5.1 row to authorize: configs/robust_asr/pricing_v1.yaml, configs/robust_asr/eval_manifests_v1.yaml (append assemblyai backend_endpoints), configs/robust_asr/reuse_policy_v1.yaml (scope rows), scripts/robust_asr/{probe_assemblya` |
| `docs/progress/robust_asr_progress.yaml` | 2950 | False | `- "authorize external: ASSEMBLYAI_API_KEY env-only (never logged or persisted); AssemblyAI transcript cache at /mnt/.../runtime/assemblyai_cache/** (read_write, large_artifact, never committed); robust_asr Apptainer image (exec only)"` |
| `docs/progress/robust_asr_progress.yaml` | 2958 | False | `notes: "CHANGE_SCOPE(P5.1) recorded against 45b6cac; scope-change applied at commit e45903e; CHANGE_SCOPE-packet recording committed at f7a845f. APPROVE_EXECUTION(P5.1-scope-change) and APPROVE_PLAN(P5.1) both accepted on f7a845f. P5.1 impl` |
| `docs/progress/robust_asr_progress.yaml` | 2999 | False | `ask_repeat: 28` |
| `docs/progress/robust_asr_progress.yaml` | 3008 | False | `ask_repeat_allowed_all_true: true` |
| `docs/progress/robust_asr_progress.yaml` | 3021 | False | `- reports/robust_asr/task_reports/P6.1_selector_evidence.md` |
| `docs/progress/robust_asr_progress.yaml` | 3033 | False | `- "selected_action codomain restricted to {whisper_base_ct2_int8, ask_repeat} as required by single-deployable-backend rule; no assemblyai or whisper_lora_ct2_int8 selections"` |
| `docs/progress/robust_asr_progress.yaml` | 3045 | False | `- "rewrite P6.1 row to authorize writes: configs/robust_asr/router_v1.yaml, scripts/robust_asr/build_selector_evidence_table.py, scripts/robust_asr/validate_selector_evidence.py, artifacts/robust_asr/router/selector_evidence.parquet, report` |
| `docs/progress/robust_asr_progress.yaml` | 3054 | False | `notes: "P6.1 selector-evidence path PASS. Build sentinel OK_SELECTOR_EVIDENCE_BUILD rows=53230; validator OK_SELECTOR_EVIDENCE; full pytest tests/robust_asr 124/124; OK_REPORT_SHAPE. Decode-feature proxy policy: P2.1 whisper_base_ct2_int8.p` |
| `docs/progress/robust_asr_progress.yaml` | 3131 | False | `ask_repeat_rate: 0.000526` |
| `docs/progress/robust_asr_progress.yaml` | 3160 | False | `- reports/robust_asr/task_reports/P7.3_router_package.md` |
| `docs/progress/robust_asr_progress.yaml` | 3171 | False | `- "rewrite P7.3 row to authorize writes: scripts/robust_asr/package_deterministic_selector.py, scripts/robust_asr/evaluate_deterministic_selector.py, tests/robust_asr/test_router_runtime.py, artifacts/robust_asr/router/selected_router/**, r` |
| `docs/progress/robust_asr_progress.yaml` | 3193 | False | `notes: "P7.3 PASS — Outcome E Branch B (deterministic selector packaging). Scope-change commit 394df2d2778e0f7204aba8155fa66e2eea8cb1a9 binds reuse_policy_v1.yaml (tests/robust_asr/** allowed_tasks += P7.3) and touch_policy.md (P7.3 row rew` |
| `docs/progress/robust_asr_progress.yaml` | 3237 | False | `- reports/robust_asr/task_reports/P8.1_system_eval.md` |
| `docs/progress/robust_asr_progress.yaml` | 3253 | False | `- "Primary policy ask_repeat_wer=1.0: mean_wer_selector=mean_wer_baseline=0.209797; mean_regret_selector=mean_regret_baseline=0.000000; paired 95% CI=[0.000000,0.000000] (percentile_fallback); Wilcoxon n=0 stat=NaN p=NaN; predicate (i)=Fals` |
| `docs/progress/robust_asr_progress.yaml` | 3254 | False | `- "Sensitivity ask_repeat_wer=0.5 (probe only): mean_wer_selector=0.209534, mean_regret_selector=-0.000263, BCa 95% CI=[-0.000385,-0.000188], Wilcoxon n=28 stat=0.0 p=1.213e-07; not used for Decision D under §5.4 alpha=1.0 cost convention"` |
| `docs/progress/robust_asr_progress.yaml` | 3255 | False | `- "selector action mix on 53,230 rows: whisper_base_ct2_int8 53,202 (99.9474%); ask_repeat 28 (0.0526%); assemblyai 0; whisper_lora_ct2_int8 0"` |
| `docs/progress/robust_asr_progress.yaml` | 3260 | False | `notes: "P8.1 PASS — Outcome E Branch B. evaluate_system.py loads selected_router/, joins selector_evidence.parquet to eval_tables/whisper_base_ct2_int8.parquet on audio_id (parity 0.0), computes paired delta = wer(selector_action_i) - wer(b` |
| `docs/progress/robust_asr_progress.yaml` | 3288 | False | `- reports/robust_asr/task_reports/P8_GATE_attempt2.md` |
| `docs/progress/robust_asr_progress.yaml` | 3297 | False | `- "Write reports/robust_asr/task_reports/P8_GATE_attempt2.md (phase gate report)"` |
| `docs/progress/robust_asr_progress.yaml` | 3300 | False | `- "git add reports/robust_asr/task_reports/P8_GATE_attempt2.md docs/progress/robust_asr_progress.yaml docs/progress/robust_asr_progress.md docs/progress/robust_asr_state_capsule.md; git commit; git push"` |
| `docs/progress/robust_asr_progress.yaml` | 3334 | False | `notes: "P8 gate PASS on attempt 2 under orchestrator APPROVE_PLAN(P8_GATE) (accepted_report_commit=643efe520904caeff84e29b11cb764ad07bbe3d9) with Reading A pre-ruling on the disjointness-proof conjunct. All five P8 gate predicate conjuncts ` |
| `docs/progress/robust_asr_progress.yaml` | 3393 | False | `- reports/robust_asr/task_reports/P8.2_demo_manifest.md` |
| `docs/progress/robust_asr_progress.yaml` | 3462 | False | `- reports/robust_asr/task_reports/P8.2_demo_manifest.md` |
| `docs/progress/robust_asr_progress.yaml` | 3503 | False | `- reports/robust_asr/task_reports/P8.2_demo_manifest.md` |
| `docs/progress/robust_asr_progress.yaml` | 3544 | False | `- reports/robust_asr/task_reports/plan_index_refresh.md` |
| `docs/progress/robust_asr_progress.yaml` | 3550 | False | `- "Write reports/robust_asr/task_reports/plan_index_refresh.md (compact evidence report for the scope change)"` |
| `docs/progress/robust_asr_progress.yaml` | 3552 | False | `- "git add plan.md CLAUDE.md docs/progress/robust_asr_progress.yaml docs/progress/robust_asr_progress.md docs/progress/robust_asr_state_capsule.md reports/robust_asr/task_reports/plan_index_refresh.md; git commit; git push"` |
| `docs/progress/robust_asr_progress.yaml` | 3574 | False | `- reports/robust_asr/task_reports/P9.0_runtime_contract.md` |
| `docs/progress/robust_asr_progress.yaml` | 3622 | False | `- reports/robust_asr/task_reports/P9.0_runtime_contract.md` |
| `docs/progress/robust_asr_progress.yaml` | 3636 | False | `- "Write reports/robust_asr/task_reports/P9.0_runtime_contract.md"` |
| `docs/progress/robust_asr_progress.yaml` | 3651 | False | `notes: "P9.0 final runtime contract executed under orchestrator APPROVE_PLAN(P9.0) on accepted_report_commit 4c6fb87. Deliverables (4 JSON artifacts + libs/common/runtime_contract.py extension + task report) emit OK_CONTRACT_FINAL with 19/1` |
| `docs/progress/robust_asr_progress.yaml` | 3674 | False | `- reports/robust_asr/task_reports/P9.1_handoff_package.md` |
| `docs/progress/robust_asr_progress.yaml` | 3697 | False | `A6: "PASS — no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/"` |
| `docs/progress/robust_asr_progress.yaml` | 3714 | False | `assemblyai: "BLOCKED_API; claims_enabled.cloud_tradeoff=false; AssemblyAI must not be represented as an enabled backend; backend_configs/ secret-grep PASS (0 matches for ASSEMBLYAI_API_KEY/sk_/Bearer)"` |
| `docs/progress/robust_asr_progress.yaml` | 3743 | False | `- reports/robust_asr/task_reports/P9.1_handoff_package.md` |
| `docs/progress/robust_asr_progress.yaml` | 3769 | False | `- "Write reports/robust_asr/task_reports/P9.1_handoff_package.md"` |
| `docs/progress/robust_asr_progress.yaml` | 3779 | False | `- "Backend set: deployable_backends=[whisper_base_ct2_int8]; LoRA excluded (lora_status=SKIPPED_BY_DECISION_A; claims_enabled.positive_lora=false; no lora_ct2_int8/ dir); AssemblyAI excluded (BLOCKED_API; claims_enabled.cloud_tradeoff=false` |
| `docs/progress/robust_asr_progress.yaml` | 3786 | False | `notes: "P9.1 handoff package executed under orchestrator APPROVE_EXECUTION(P9.0) acceptance commit f7a195b8 + previously approved P9.1 plan. Two-commit sequence per orchestrator's critical execution constraint: Commit A (64eba43) = 'Package` |
| `docs/progress/robust_asr_progress.yaml` | 3794 | False | `- reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` |
| `docs/progress/robust_asr_progress.yaml` | 3852 | False | `report_path: reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` |
| `docs/progress/robust_asr_progress.yaml` | 3855 | False | `- reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` |
| `docs/progress/robust_asr_progress.yaml` | 3870 | False | `ACTION_ASK_REPEAT: "ask_repeat -> control action (not a backend); PRESENT in deterministic_selector.json.deployable_actions"` |
| `docs/progress/robust_asr_progress.yaml` | 3889 | False | `- reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` |
| `docs/progress/robust_asr_progress.yaml` | 3904 | False | `- "Write reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md"` |
| `docs/progress/robust_asr_progress.yaml` | 3920 | False | `notes: "P9.2 RP5 runtime spec executed under orchestrator APPROVE_PLAN(P9.2) on accepted_report_commit 9f54b02. Single-commit task: write artifacts/robust_asr/handoff/rp5_runtime_spec.md (sha256 bbcf912d...) with the six lowercase-anchored ` |
| `docs/progress/robust_asr_progress.yaml` | 3955 | False | `- reports/robust_asr/task_reports/P9_GATE_attempt1.md` |
| `docs/progress/robust_asr_progress.yaml` | 3969 | False | `- "Write reports/robust_asr/task_reports/P9_GATE_attempt1.md (phase_gate_report)"` |
| `docs/progress/robust_asr_progress.yaml` | 3970 | False | `- "Edit docs/progress/robust_asr_progress.yaml: latest_approval_packet -> APPROVE_PLAN(P9_GATE) on ec9b7ca; APPROVE_EXECUTION(P9.2) on 6711768 demoted to prior_approval_packet_p9_2_exec; tasks.P9_GATE added (attempt=1, status=PASS, predicat` |
| `docs/progress/robust_asr_progress.yaml` | 3972 | False | `- "git add reports/robust_asr/task_reports/P9_GATE_attempt1.md docs/progress/robust_asr_progress.yaml docs/progress/robust_asr_progress.md docs/progress/robust_asr_state_capsule.md; git commit -m 'Evaluate P9 robust ASR gate' (author Gabrie` |
| `docs/progress/robust_asr_progress.yaml` | 3985 | False | `notes: "P9 gate PASS on attempt 1 under orchestrator APPROVE_PLAN(P9_GATE) (accepted_report_commit=ec9b7caea99c27d63fca3cb458eca8f06e7f6260). All 12 conjuncts of the P9 gate predicate (agent plan §2693-§2713) evaluate PASS: (1) tasks.P9.0.s` |
| `docs/progress/robust_asr_progress.yaml` | 4017 | False | `report: reports/robust_asr/task_reports/P10.1_final_verification.md` |
| `docs/progress/robust_asr_progress.yaml` | 4020 | False | `task_report_sha256: ed7b149b29924c20f8ddeb5139494ad5e75e6d06fc530120efe1cc810a2d80ea` |
| `docs/progress/robust_asr_progress.yaml` | 4023 | False | `- reports/robust_asr/task_reports/P10.1_final_verification.md` |
| `docs/progress/robust_asr_progress.yaml` | 4036 | False | `- "sha256sum reports/robust_asr/task_reports/P10.1_final_verification.md  ->  ed7b149b29924c20f8ddeb5139494ad5e75e6d06fc530120efe1cc810a2d80ea"` |
| `docs/progress/robust_asr_progress.yaml` | 4038 | False | `- "Write reports/robust_asr/task_reports/P10.1_final_verification.md (P10.1 task report)"` |
| `docs/progress/robust_asr_progress.yaml` | 4041 | False | `- "git add reports/robust_asr/final_verification.md reports/robust_asr/task_reports/P10.1_final_verification.md docs/progress/robust_asr_progress.yaml docs/progress/robust_asr_progress.md docs/progress/robust_asr_state_capsule.md; git commi` |
| `docs/progress/robust_asr_progress.yaml` | 4048 | False | `- "Tracker mutations on this commit: latest_approval_packet -> APPROVE_PLAN(P10.1) on d08dfa8...; PHASE_APPROVE(P9) on a3c7d37... demoted to prior_approval_packet_p9_gate_phase_approve; tasks.P10.1 added (status=PASS); artifacts.final_verif` |
| `docs/progress/robust_asr_progress.yaml` | 4055 | False | `notes: "P10.1 PASS on attempt 1 under orchestrator APPROVE_PLAN(P10.1) (accepted_report_commit=d08dfa821957d4dfa5c3049fc1a60a850d2097ac). All seven actions of agent plan §4234-§4249 are satisfied under Branch B (deterministic selector evide` |
| `docs/progress/robust_asr_progress.yaml` | 4059 | False | `task_id: P8.2-deviation` |
| `docs/progress/robust_asr_progress.yaml` | 4089 | False | `enactment_path: "Recording this scope authorization does NOT enact the deviation. To enact: (1) operator/orchestrator records APPROVE_PLAN(P8.2-deviation) restating the 5 constraints; (2) implementation amends artifacts/robust_asr/demo/demo` |
| `docs/progress/robust_asr_progress.yaml` | 4119 | False | `- reports/robust_asr/task_reports/P8.2_demo_manifest.md` |
| `docs/progress/robust_asr_state_capsule.md` | 3 | False | `Updated by: CHANGE_SCOPE(`model_router_card_completion`) applied on orchestrator accepted_report_commit `d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d`. ORCHESTRATOR_DECISION (latest_scope_change_packet, recorded under `state_transport.latest_sc` |
| `docs/progress/robust_asr_state_capsule.md` | 5 | False | `## Prior update — CHANGE_SCOPE(`reuse_policy_p10_2_script_allowance`) applied on orchestrator accepted_report_commit `9452afcf3c3f6b1874d86650724606d8e902b286`. ORCHESTRATOR_DECISION (latest_scope_change_packet, recorded under `state_transp` |
| `docs/progress/robust_asr_state_capsule.md` | 7 | False | `## Prior update — APPROVE_EXECUTION(P10.1) recorded on accepted_report_commit `37a588b6aa4ee3116c32778092990b8dc9d023b0`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P10.1 phase=P10 decision=APPROVE_EXECUTION accepted` |
| `docs/progress/robust_asr_state_capsule.md` | 9 | False | `## Prior update — P10.1 EXECUTED PASS under APPROVE_PLAN(P10.1) on accepted_report_commit `d08dfa821957d4dfa5c3049fc1a60a850d2097ac`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P10.1 phase=P10 decision=APPROVE_PLAN a` |
| `docs/progress/robust_asr_state_capsule.md` | 11 | False | `## Prior update — PHASE_APPROVE(P9) recorded — P9 phase approved on accepted_report_commit `a3c7d3713809e6d77e4d53e423cc50973b5fa5a4`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=phase task_id=P9_GATE phase=P9 decision=PHASE_APPRO` |
| `docs/progress/robust_asr_state_capsule.md` | 13 | False | `## Prior update — P9_GATE attempt 1 PASS recorded — phase_summary.P9 advanced to PASS; awaiting orchestrator PHASE_APPROVE(P9). ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9_GATE phase=P9 decision=APPROVE_PLAN accept` |
| `docs/progress/robust_asr_state_capsule.md` | 15 | False | `## Prior update — APPROVE_EXECUTION(P9.2) recorded — P9.2 RP5 runtime spec accepted at `6711768743bbed4e947bea884a92b12ab095ebf7`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9.2 phase=P9 decision=APPROVE_EXECUTION a` |
| `docs/progress/robust_asr_state_capsule.md` | 17 | False | `## Prior update — FIX_BEFORE_CLOSE(P9.2) applied — strict handoff-tag validator now passes A1–A7. ORCHESTRATOR_DECISION (FIX_BEFORE_CLOSE, applied without becoming `latest_approval_packet`): scope=fix task_id=P9.2 phase=P9 decision=FIX_BEFO` |
| `docs/progress/robust_asr_state_capsule.md` | 19 | False | `## Prior update — P9.2 EXECUTED PASS under APPROVE_PLAN(P9.2) on accepted_report_commit `9f54b028f6d24cac6fcd5b6b75ea7770d5783475`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9.2 phase=P9 decision=APPROVE_PLAN accep` |
| `docs/progress/robust_asr_state_capsule.md` | 21 | False | `## Prior update — APPROVE_EXECUTION(P9.1) recorded — P9.1 Handoff package accepted at `6301dbc1637af0f0c74be6e06f77d182e050b77a`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9.1 phase=P9 decision=APPROVE_EXECUTION ac` |
| `docs/progress/robust_asr_state_capsule.md` | 23 | False | `## Prior update — P9.1 APPROVE_PLAN packet protocol fix. ORCHESTRATOR_DECISION (latest_approval_packet, recorded retroactively): scope=task task_id=P9.1 phase=P9 decision=APPROVE_PLAN accepted_report_commit=`655a05cfa0f13aad97bb0133b94dfee0` |
| `docs/progress/robust_asr_state_capsule.md` | 25 | False | `## Prior update — P9.1 EXECUTED PASS under previously approved P9.1 plan + orchestrator's two-commit-sequence execution constraint. ORCHESTRATOR_DECISION (latest_approval_packet, **held** from prior commit): scope=task task_id=P9.0 phase=P9` |
| `docs/progress/robust_asr_state_capsule.md` | 27 | False | `## Prior update — APPROVE_EXECUTION(P9.0) recorded — P9.0 Final runtime contract accepted at `f7a195b8828278e42fcc642090cc315309404e07`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9.0 phase=P9 decision=APPROVE_EXECU` |
| `docs/progress/robust_asr_state_capsule.md` | 29 | False | `## Prior update — P9.0 EXECUTED PASS under `APPROVE_PLAN(P9.0)` on accepted_report_commit `4c6fb87d8e5e72bbec82a4f9acf9b8bbe2aefa13`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P9.0 phase=P9 decision=APPROVE_PLAN acc` |
| `docs/progress/robust_asr_state_capsule.md` | 31 | False | `## Prior update — PHASE_APPROVE(P8) recorded — P8_GATE attempt 2 accepted at `0b221c9e213c68636ce0cbf0da75b67baae7d31a`; `current_task` advanced `P8_GATE -> P9.0`; `last_completed_task` advanced `P8.2 -> P8_GATE`; `current_phase` advanced `` |
| `docs/progress/robust_asr_state_capsule.md` | 33 | False | `## Prior update — P8_GATE attempt 2 PASS — all five P8 gate predicate conjuncts satisfied; `phase_summary.P8` advanced `null -> PASS`; awaiting orchestrator `PHASE_APPROVE(P8)`. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task tas` |
| `docs/progress/robust_asr_state_capsule.md` | 35 | False | `## Prior update — CHANGE_SCOPE(plan_index_refresh) recorded — administrative branch entry-point pointer refresh; P8 evidence and P8_GATE state held. ORCHESTRATOR_DECISION (latest_approval_packet): scope=scope_change task_id=plan_index_refre` |
| `docs/progress/robust_asr_state_capsule.md` | 37 | False | `## Prior update — P8.2 APPROVE_EXECUTION recorded — `tasks.P8.2.status` PASS under enacted demo-only deviation; `current_task` advanced `P8.2 -> P8_GATE`; `last_completed_task` advanced `P8.1 -> P8.2`. ORCHESTRATOR_DECISION (latest_approval` |
| `docs/progress/robust_asr_state_capsule.md` | 39 | False | `## Prior update — P8.2-deviation APPROVE_EXECUTION recorded — enactment accepted; parent `tasks.P8.2` remains `IMPLEMENTED_PENDING_APPROVAL`. ORCHESTRATOR_DECISION: scope=task task_id=P8.2-deviation phase=P8 decision=APPROVE_EXECUTION accep` |
| `docs/progress/robust_asr_state_capsule.md` | 41 | False | `## Prior update — P8.2-deviation ENACTED — demo-only overlap deviation accepted; final provenance verdict `PASS_WITH_DEMO_ONLY_DEVIATION`; tasks.P8.2 status `HALTED -> IMPLEMENTED_PENDING_APPROVAL`; markers loses `MISSING_EVIDENCE`; blocked` |
| `docs/progress/robust_asr_state_capsule.md` | 43 | False | `## Prior update — P8.2-deviation CHANGE_SCOPE recorded — demo-only overlap deviation framework authorized but NOT enacted. ORCHESTRATOR_DECISION: scope=scope_change task_id=P8.2-deviation phase=P8 decision=CHANGE_SCOPE accepted_report_commi` |
| `docs/progress/robust_asr_state_capsule.md` | 45 | False | `## Prior update — P8.2-upstream-leakage-audit APPROVE_EXECUTION recorded — audit accepted; parent `tasks.P8.2` remains HALTED with `MISSING_EVIDENCE` / `DEMO_UPSTREAM_LOCKED_OVERLAP`. ORCHESTRATOR_DECISION: scope=task task_id=P8.2-upstream-` |
| `docs/progress/robust_asr_state_capsule.md` | 47 | False | `## Prior update — P8.2-upstream-leakage-audit — upstream-level disjointness FAIL; tasks.P8.2 status IMPLEMENTED_PENDING_APPROVAL -> HALTED; marker MISSING_EVIDENCE re-added; reason DEMO_UPSTREAM_LOCKED_OVERLAP; blocked=true. Provenance fiel` |
| `docs/progress/robust_asr_state_capsule.md` | 49 | False | `## Prior update — P8.2-provenance-rerun — provenance repaired from operator-supplied asr-rp5 evidence — verdict PASS; tasks.P8.2 status HALTED -> IMPLEMENTED_PENDING_APPROVAL. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_` |
| `docs/progress/robust_asr_state_capsule.md` | 51 | False | `## Prior update — P8.2-provenance APPROVE_EXECUTION recorded — audit accepted; parent `tasks.P8.2` remains HALTED. ORCHESTRATOR_DECISION: scope=task task_id=P8.2-provenance phase=P8 decision=APPROVE_EXECUTION accepted_report_commit=`deb8085` |
| `docs/progress/robust_asr_state_capsule.md` | 53 | False | `## Prior update — P8.2-provenance audit — verdict INSUFFICIENT — P8.2 HALTED with marker MISSING_EVIDENCE / reason DEMO_PROVENANCE_INSUFFICIENT. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P8.2-provenance phase=P8 dec` |
| `docs/progress/robust_asr_state_capsule.md` | 55 | False | `## Prior update — P8.2 CHANGE_SCOPE recorded (provenance repair) — touch_policy P8.2 row amended to authorize `reports/robust_asr/demo/provenance_audit.md` (write). ORCHESTRATOR_DECISION: scope=scope_change task_id=P8.2-provenance phase=P8 ` |
| `docs/progress/robust_asr_state_capsule.md` | 57 | False | `## Prior update — P8.2 IMPLEMENTED — 8 public demo entries built; leakage-test strengthened; PASS pending APPROVE_EXECUTION(P8.2). ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P8.2 phase=P8 decision=APPROVE_PLAN accept` |
| `docs/progress/robust_asr_state_capsule.md` | 59 | False | `## Prior update — P8.2 CHANGE_SCOPE recorded — authorize demo example builder, 8 public demo WAV files, demo manifest, and leakage-test edit. ORCHESTRATOR_DECISION: scope=scope_change task_id=P8.2 phase=P8 decision=CHANGE_SCOPE accepted_rep` |
| `docs/progress/robust_asr_state_capsule.md` | 61 | False | `## Prior update — P8 PHASE_REJECT recorded — gate predicate incomplete; route-correction back to P8.2. ORCHESTRATOR_DECISION: scope=phase task_id=null phase=P8 decision=PHASE_REJECT accepted_report_commit=null next_expected_task=`P8.2` requ` |
| `docs/progress/robust_asr_state_capsule.md` | 63 | False | `## Prior update — P8.1 APPROVE_EXECUTION recorded. ORCHESTRATOR_DECISION: scope=task task_id=P8.1 phase=P8 decision=APPROVE_EXECUTION accepted_report_commit=`1b9f33e681276f977c1e87db4978963ee2a3a9bd` next_expected_task=`P8_GATE` required_fi` |
| `docs/progress/robust_asr_state_capsule.md` | 65 | False | `## Prior update — P8.1 PASS — system evaluation and Decision D under OUTCOME_E_DETERMINISTIC_SELECTOR. ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P8.1 phase=P8 decision=APPROVE_PLAN accepted_report_commit=`f23a27024c` |
| `docs/progress/robust_asr_state_capsule.md` | 67 | False | `## Prior update — P8.1 CHANGE_SCOPE recorded — authorize `scripts/robust_asr/evaluate_system.py` in the P8.1 touch-policy row. ORCHESTRATOR_DECISION: scope=scope_change task_id=P8.1 phase=P8 decision=CHANGE_SCOPE accepted_report_commit=`440` |
| `docs/progress/robust_asr_state_capsule.md` | 71 | False | `## Prior update — P7.3 APPROVE_EXECUTION recorded. ORCHESTRATOR_DECISION: scope=task task_id=P7.3 phase=P7 decision=APPROVE_EXECUTION accepted_report_commit=`d009c318acd99041de3175af26b91df2adddffa6` next_expected_task=`P7_GATE` required_fi` |
| `docs/progress/robust_asr_state_capsule.md` | 73 | False | `## Prior update — P7.3 PASS — deterministic selector packaged (Outcome E, Branch B). ORCHESTRATOR_DECISION (latest_approval_packet): scope=task task_id=P7.3 phase=P7 decision=APPROVE_PLAN accepted_report_commit=`394df2d2778e0f7204aba8155fa6` |
| `docs/progress/robust_asr_state_capsule.md` | 75 | False | `## Prior update — P7.3 CHANGE_SCOPE recorded — deterministic selector packaging. ORCHESTRATOR_DECISION: scope=scope_change task_id=P7.3 phase=P7 decision=CHANGE_SCOPE accepted_report_commit=`e9ebbfe` next_expected_task=P7.3 required_fix="Au` |
| `docs/progress/robust_asr_state_capsule.md` | 79 | False | `## Prior update — P6.1 APPROVE_EXECUTION recorded. ORCHESTRATOR_DECISION: scope=task task_id=P6.1 phase=P6 decision=APPROVE_EXECUTION accepted_report_commit=`64413500094b79a160fbcb179b432fd6ccdaf80f` next_expected_task=P6_GATE required_fix=` |
| `docs/progress/robust_asr_state_capsule.md` | 81 | False | `## Prior update — P6.1 PASS — selector-evidence path (Outcome E). ORCHESTRATOR_DECISION: scope=task task_id=P6.1 phase=P6 decision=APPROVE_PLAN accepted_report_commit=`4a9f9291f0a1e90d21f0d771885d9eaf273aa37b` next_expected_task=P6_GATE req` |
| `docs/progress/robust_asr_state_capsule.md` | 83 | False | `## Prior update — P6.1 CHANGE_SCOPE recorded. ORCHESTRATOR_DECISION: scope=scope_change task_id=P6.1 phase=P6 decision=CHANGE_SCOPE accepted_report_commit=`9ffc885` next_expected_task=P6.1 required_fix="Authorize deterministic-selector conf` |
| `docs/progress/robust_asr_state_capsule.md` | 87 | False | `## Prior update — P5.1 APPROVE_EXECUTION recorded. ORCHESTRATOR_DECISION: scope=task task=P5.1 phase=P5 decision=APPROVE_EXECUTION accepted_report_commit=`c71e0a0bb25a5d2749801d8fc7444869ff331d1b` next_expected_task=P5_GATE required_fix=nul` |
| `docs/progress/robust_asr_state_capsule.md` | 89 | False | `## Prior update — P5.1 HALTED — BLOCKED_API (key_unset). APPROVE_EXECUTION(P5.1-scope-change) and APPROVE_PLAN(P5.1) both recorded on commit `f7a845f3ff8f2bf51b8bcc8ff2342a4e4f817f64`. P5.1 implementation deliverables written this commit: `` |
| `docs/progress/robust_asr_state_capsule.md` | 91 | False | `## Prior update — P5.1 CHANGE_SCOPE recorded. ORCHESTRATOR_DECISION: scope=scope_change task=P5.1 phase=P5 decision=CHANGE_SCOPE accepted_report_commit=`45b6cac93d1fe3eb54630a7511c331439715bb68` next_expected_task=P5.1 required_fix="Authori` |
| `docs/progress/robust_asr_state_capsule.md` | 97 | False | `## Prior update — P3.2 PASS — Decision_A_smoke recorded as FAIL (mechanical Section 5.1: `macro_wa_gain=-0.12843 < 0.005`, `max_family_wa_gain=-0.11345 < 0.010`, `clean_wa_regression=0.11345 > 0.010` and `> 0.020`, `per_family_wa_gain_varia` |
| `docs/progress/robust_asr_state_capsule.md` | 99 | False | `## Prior update — P3.2 CHANGE_SCOPE recorded — touch_policy.md P3.2 row rewritten to authorize `scripts/robust_asr/decide_lora_smoke.py`, `tests/robust_asr/test_decide_lora_smoke.py`, `reports/robust_asr/lora/lora_smoke_report.md`, `reports` |
| `docs/progress/robust_asr_state_capsule.md` | 105 | False | `Updated by: P3.1 PASS — LoRA smoke train + eval + export smoke executed via Slurm job `2131980` (COMPLETED `0:0`, 9m48s on `aisurrey03.surrey.ac.uk`, RTX 2080 Ti, partition `2080ti`, MaxRSS 2,826,500 KiB, container sha256 `8db5364c7610496a3` |
| `docs/progress/robust_asr_state_capsule.md` | 109 | False | `Updated by: P3.1 CHANGE_SCOPE recorded — `reports/robust_asr/touch_policy.md` P3.1 row REWRITTEN to authorize the v3.4.7 P3.1 LoRA smoke train/eval/export task. The stale P3.2-style `reports/robust_asr/lora/lora_smoke_report.md` entry was R` |
| `docs/progress/robust_asr_state_capsule.md` | 121 | False | `Updated by: P2.2 PASS — LoRA smoke split config built and committed. `configs/robust_asr/lora_smoke.yaml` written (43,252 bytes; sha256 `4d7ae4489587937e841df9ca172e9b9933e4647ddbe06edf3b00adc713e00cff`). Top-level keys: `version`, `seed`, ` |
| `docs/progress/robust_asr_state_capsule.md` | 125 | False | `Updated by: P2.2 CHANGE_SCOPE recorded — `reports/robust_asr/touch_policy.md` P2.2 row REWRITTEN to authorize the v3.4.7 P2.2 LoRA smoke split config task. New `allowed_write_paths`: `configs/robust_asr/lora_smoke.yaml`, `reports/robust_asr` |
| `docs/progress/robust_asr_state_capsule.md` | 149 | False | `Updated by: P2.1 HALTED — sentinel `MISSING_EVIDENCE`. CT2 INT8 weights for `whisper_base_ct2_int8` not present at any `candidate_local_paths` declared in `configs/robust_asr/eval_manifests_v1.yaml`; `scripts/robust_asr/run_backend_eval.py`` |
| `docs/progress/robust_asr_state_capsule.md` | 153 | False | `P2.1 CHANGE_SCOPE recorded — `configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md` amended to authorize P2.1 baseline-eval deliverables. `configs/robust_asr/**` row: P2.1 added to `allowed_tasks` (now `[P0.2, P0` |
| `docs/progress/robust_asr_state_capsule.md` | 169 | False | ``configs/robust_asr/reuse_policy_v1.yaml` and `reports/robust_asr/touch_policy.md` amended to authorize additive P1.4 degradation_v1 work. NEW reuse_policy override row for `libs/audio/degradations.py` (class=existing_runtime_code, permitte` |
| `docs/progress/robust_asr_state_capsule.md` | 193 | False | `latest_execution_report: reports/robust_asr/task_reports/P1.2_eval_schema.md` |
| `docs/progress/robust_asr_state_capsule.md` | 194 | False | `latest_planning_report: reports/robust_asr/task_reports/P1.2_eval_schema.md` |
| `docs/progress/robust_asr_state_capsule.md` | 218 | False | `validator=file_basename_matches_p<task_id>_*.sh, commit_allowed=true.` |
| `docs/progress/robust_asr_state_capsule.md` | 318 | False | `reports/robust_asr/task_reports/P0.3_runtime_smoke.md,` |
| `docs/progress/robust_asr_state_capsule.md` | 368 | False | `30 `TODO_FILLED_IN_<task_id>` placeholders (≥ 10 required);` |
| `docs/progress/robust_asr_state_capsule.md` | 373 | False | `24 `TODO_FILLED_IN_<task_id>` placeholders (≥ 8 required);` |
| `docs/progress/robust_asr_state_capsule.md` | 416 | False | `reports/robust_asr/task_reports/P1.1_data_inventory.md,` |
| `docs/progress/robust_asr_state_capsule.md` | 504 | False | `- `reports/robust_asr/task_reports/P1.1_data_inventory.md` — execution` |
| `docs/progress/robust_asr_state_capsule.md` | 633 | False | `- `reports/robust_asr/task_reports/P1.2_eval_schema.md`.` |
| `docs/progress/training_datamove1_progress.md` | 16 | False | `- T0.3: created independent training trackers `docs/progress/training_datamove1_progress.{md,yaml}` per training plan §8 format. Legacy `docs/claude_task_progress.*` left untouched as historical.` |
| `docs/progress/training_datamove1_progress.md` | 2067 | False | `- `on_disk_checkpoint_sha256_check`: passed (canonical SHA-256` |
| `docs/progress/training_datamove1_progress.md` | 2071 | False | `- `on_disk_latest_sha256_check`: passed (alias `latest.pt` SHA-256` |
| `docs/progress/training_datamove1_progress.yaml` | 923 | False | `current_task_after: "T5.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 924 | False | `last_completed_task_after: "T4.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 1010 | False | `current_task_after: "T5.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1011 | False | `last_completed_task_after: "T5.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1098 | False | `current_task_after: "T5.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 1099 | False | `last_completed_task_after: "T5.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1230 | False | `current_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1231 | False | `last_completed_task_after: "T5.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 1296 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1297 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1383 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1384 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1482 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1483 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1586 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1587 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1751 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1752 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 1863 | False | `current_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 1864 | False | `last_completed_task_after: "T6.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 2000 | False | `current_task_after: "T6.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 2001 | False | `last_completed_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2122 | False | `current_task_after: "T6.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 2123 | False | `last_completed_task_after: "T6.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2282 | False | `current_task_after: "T7.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 2283 | False | `last_completed_task_after: "T6.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 2485 | False | `current_task_after: "T7.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2486 | False | `last_completed_task_after: "T7.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 2550 | False | `current_task_after: "T8.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 2551 | False | `last_completed_task_after: "T7.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2637 | False | `on_disk_checkpoint_sha256_check: passed` |
| `docs/progress/training_datamove1_progress.yaml` | 2638 | False | `on_disk_latest_sha256_check: passed` |
| `docs/progress/training_datamove1_progress.yaml` | 2642 | False | `current_task_after: "T8.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2643 | False | `last_completed_task_after: "T8.1"` |
| `docs/progress/training_datamove1_progress.yaml` | 2730 | False | `current_task_after: "T8.3"` |
| `docs/progress/training_datamove1_progress.yaml` | 2731 | False | `last_completed_task_after: "T8.2"` |
| `docs/progress/training_datamove1_progress.yaml` | 2838 | False | `current_task_after: null` |
| `docs/progress/training_datamove1_progress.yaml` | 2839 | False | `last_completed_task_after: "T8.3"` |
| `docs/reports/robust_asr/model_card_lora.md` | 51 | False | `- AssemblyAI reference numbers: **N/A — HALTED under BLOCKED_API**. P5.1 is `HALTED` because `ASSEMBLYAI_API_KEY` is unset, exit-8 guard `BLOCKED_API` engaged. `artifacts/robust_asr/eval_tables/assemblyai.parquet` was never produced. Assemb` |
| `docs/reports/robust_asr/model_card_lora.md` | 52 | False | `- System-level metrics (selector applied): per `reports/robust_asr/system/system_eval.md` (first line `positive_system: false`): under `OUTCOME_E_NARROWED_SCOPE` with the single deployable transcript-producing backend `whisper_base_ct2_int8` |
| `docs/reports/robust_asr/router_card.md` | 14 | False | `- Purpose: at inference time, decide which deployable backend handles a given input clip. Per `artifacts/robust_asr/router/selected_router/deterministic_selector.json`, the deployable action set is `[whisper_base_ct2_int8, ask_repeat]`. `as` |
| `docs/reports/robust_asr/router_card.md` | 29 | False | `- Decision rule (model class, thresholds, fallbacks): the deployed selector is the §5.5 deterministic constants block recorded in `artifacts/robust_asr/router/selected_router/deterministic_selector.json`: `ask_repeat_threshold = -1.0`, `esc` |
| `docs/reports/robust_asr/router_card.md` | 45 | False | `- Held-out router evaluation metrics (top-1 selection accuracy, regret vs. oracle, per-degradation gains): **N/A — skipped under `OUTCOME_E_DETERMINISTIC_SELECTOR`**. `tasks.P7.2` is `SKIPPED_BY_OUTCOME_E`; no learned router was trained, so` |
| `docs/reports/robust_asr/router_card.md` | 47 | False | `- Decision D (positive_system claim) outcome: `Decision_D_positive_system.outcome = false` under `OUTCOME_E_NARROWED_SCOPE` held on `tasks.P8.1` and `decisions.Decision_D_positive_system`. Per `system_eval.md` Decision D: under `OUTCOME_E` ` |
| `docs/reports/robust_asr/router_card.md` | 54 | False | `- Cold-start / missing-feature handling: when feature proxies are missing or invalid, the deterministic selector defaults to `whisper_base_ct2_int8` (the unique deployable transcript-producing backend; `assemblyai_available = false`, `lora_` |
| `docs/reports/robust_asr/router_card.md` | 55 | False | `- AssemblyAI fallback (unavailable cache or quota exceeded): **N/A — HALTED under `BLOCKED_API`**. AssemblyAI is not an enabled backend; `assemblyai_available = false` is hardwired in the deployed runtime per `metadata.json` `cloud_availabl` |
| `docs/reports/robust_asr/router_card.md` | 63 | False | `- Mis-routing cost vs. always-baseline policy: per `reports/robust_asr/system/system_eval.md`, the deterministic selector is mathematically equivalent to always-baseline on 53 202/53 230 rows (99.9474 %) and emits `ask_repeat` on 28 rows wh` |
| `docs/smoke_tests.md` | 136 | False | `- `ASSEMBLYAI_API_KEY=<your-key>`` |
| `docs/smoke_tests.md` | 147 | False | `-e ASSEMBLYAI_API_KEY=<your-key> \` |
| `docs/smoke_tests.md` | 156 | False | `ASSEMBLYAI_API_KEY=<your-key> \` |
| `docs/smoke_tests.md` | 172 | False | `- `event` — application event name (for example `api.task_enqueued`, `worker.job_received`, `worker.span_started`)` |
| `libs/asr_adapter/factory.py` | 15 | False | `"AssemblyAI provider selected but ASSEMBLYAI_API_KEY is not set"` |
| `libs/common/eval_schema.yaml` | 16 | False | `# reports/robust_asr/task_reports/P1.2_eval_schema.md and is reported` |
| `libs/common/runtime_contract.py` | 81 | False | `"ask_repeat", "selected_backend", "router_kind",` |
| `libs/common/runtime_contract.py` | 93 | False | `"ask_repeat": {"type": "boolean"},` |
| `libs/common/runtime_contract.py` | 220 | False | `# A11 — response.ask_repeat is bool` |
| `libs/common/runtime_contract.py` | 221 | False | `ar = _get(response, "ask_repeat")` |
| `libs/common/runtime_contract.py` | 222 | False | `emit(_AID(11), _is_bool(ar), f"response.ask_repeat={ar!r}")` |
| `libs/common/runtime_contract.py` | 224 | False | `# A12 — (transcript is null) iff (ask_repeat==True OR errors non-empty)` |
| `libs/common/runtime_contract.py` | 233 | False | `f"transcript_is_null={transcript_is_null} ask_repeat={ar!r} "` |
| `libs/common/runtime_contract.py` | 237 | False | `# A13 — selected_backend is null iff ask_repeat == True` |
| `libs/common/runtime_contract.py` | 243 | False | `f"selected_backend={sb!r} ask_repeat={ar!r}",` |
| `libs/common/runtime_contract.py` | 372 | False | `"ask_repeat", "selected_backend", "router_kind",` |
| `libs/common/runtime_contract.py` | 384 | False | `"ask_repeat": {"type": "boolean"},` |
| `pyproject.toml` | 52 | False | `"live_provider: requires RUN_LIVE_ASSEMBLYAI_TEST=1 and ASSEMBLYAI_API_KEY; never runs in CI",` |
| `reports/robust_asr/asset_inventory.md` | 45 | False | `- `docs/claude_task_progress.md` — ABSENT` |
| `reports/robust_asr/asset_inventory.md` | 46 | False | `- `docs/claude_task_progress.yaml` — ABSENT` |
| `reports/robust_asr/asset_inventory.md` | 208 | False | `| docs/claude_task_progress.md | ABSENT — file does not exist |` |
| `reports/robust_asr/asset_inventory.md` | 209 | False | `| docs/claude_task_progress.yaml | ABSENT — file does not exist |` |
| `reports/robust_asr/asset_inventory.md` | 217 | False | `- 5 legacy state paths present; 2 absent (docs/claude_task_progress.*)` |
| `reports/robust_asr/data_inventory.md` | 140 | False | `- `reports/robust_asr/task_reports/P1.1_data_inventory.md` (rewritten)` |
| `reports/robust_asr/final_verification.md` | 83 | False | `- A6 PASS: no `ASSEMBLYAI_API_KEY` / `sk_` / `Bearer` in `backend_configs/`` |
| `reports/robust_asr/final_verification.md` | 93 | False | `- All 19 assertions PASS (A01–A19): request/response IDs match; audio encoding `wav`, sample_rate `16000`, channels `1`, duration `4.0s`; constraints `local_first`, `allow_third_party=False`, `max_latency_ms=2000`; response `ask_repeat=Fals` |
| `reports/robust_asr/final_verification.md` | 184 | False | `- columns: `audio_id`, `reference_normalized`, `whisper_base_ct2_int8_wer`, `whisper_base_ct2_int8_latency_ms`, `whisper_base_ct2_int8_wa`, `selected_action`, `selector_reason`, `ask_repeat_allowed`, `assemblyai_available`, `lora_available`` |
| `reports/robust_asr/repo_integration_policy.md` | 48 | False | `| docs/claude_task_progress.* | legacy_state | read_only | false | ABSENT — if created, treat as legacy_state |` |
| `reports/robust_asr/repository_inventory.md` | 56 | False | `- docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.yaml  (archived)` |
| `reports/robust_asr/repository_inventory.md` | 57 | False | `- docs/archive/legacy_trackers/20260507T223435Z/claude_task_progress.md    (archived)` |
| `reports/robust_asr/repository_inventory.md` | 81 | False | `reports/robust_asr/task_reports/` |
| `reports/robust_asr/router/selector_evidence_summary.md` | 19 | False | `- Section 5.5 constants: `ask_repeat_threshold=-1.0`,` |
| `reports/robust_asr/router/selector_evidence_summary.md` | 38 | False | `| `ask_repeat`            | 28    | 0.0526 %  | `no_speech`       |` |
| `reports/robust_asr/router/selector_evidence_summary.md` | 42 | False | ``ask_repeat_allowed = True` on every row.` |
| `reports/robust_asr/router/selector_evidence_summary.md` | 83 | False | ``ask_repeat`}; `assemblyai_available=False` ⇒ never `assemblyai`;` |
| `reports/robust_asr/router/selector_final_eval.md` | 10 | False | `- Section 5.5 constants: `ask_repeat_threshold=-1.0`, `escalate_threshold=-0.5`, `no_speech_threshold=0.6`, `health_check_ttl_seconds=300.0`` |
| `reports/robust_asr/router/selector_final_eval.md` | 23 | False | `| `ask_repeat`            |     28 |     0.0526 % |` |
| `reports/robust_asr/router/selector_final_eval.md` | 29 | False | `- `transcript_emitted_rate` (non-`ask_repeat`): 99.9474 %` |
| `reports/robust_asr/router/selector_final_eval.md` | 38 | False | `- `ASK_REPEAT_WER` convention: 1.0 (no transcript is emitted on `ask_repeat`; using a maximum-penalty convention for regret accounting). `ASK_REPEAT_WA` = 0.0.` |
| `reports/robust_asr/runtime_contract_smoke.md` | 54 | False | `| A11 | PASS | `response.ask_repeat=False` is bool |` |
| `reports/robust_asr/runtime_contract_smoke.md` | 55 | False | `| A12 | PASS | (transcript is null) iff (ask_repeat=true OR errors non-empty) — both sides False |` |
| `reports/robust_asr/runtime_contract_smoke.md` | 56 | False | `| A13 | PASS | selected_backend null iff ask_repeat=true — both sides False |` |
| `reports/robust_asr/runtime_image_rebuild.md` | 143 | False | `- `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md`` |
| `reports/robust_asr/runtime_smoke.md` | 127 | False | `latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `reports/robust_asr/runtime_smoke.md` | 133 | False | `task_id: P0.3-rerun-2` |
| `reports/robust_asr/system/system_eval.md` | 14 | False | `- ask_repeat WER policy (primary): 1.0` |
| `reports/robust_asr/system/system_eval.md` | 15 | False | `- ask_repeat WER sensitivity values: 0.5` |
| `reports/robust_asr/system/system_eval.md` | 17 | False | `## Primary result (ask_repeat WER = 1.0)` |
| `reports/robust_asr/system/system_eval.md` | 37 | False | `- Under OUTCOME_E with a single deployable transcribing backend, the deterministic selector's only divergence from always-baseline is the 28 `ask_repeat` rows (selector_reason == `no_speech`). All 28 rows have `whisper_base_ct2_int8_wer = 1` |
| `reports/robust_asr/system/system_eval.md` | 39 | False | `## Sensitivity check (alternative ask_repeat WER)` |
| `reports/robust_asr/system/system_eval.md` | 41 | False | `- ask_repeat_wer = 0.5: mean_wer_selector=0.209534, mean_wer_baseline=0.209797, mean_regret_selector=-0.000263, CI(method=BCa)=[-0.000385, -0.000188], Wilcoxon n=28 stat=0.0 p=1.2131545083660686e-07, strict_lt=True, CI_excludes_0=True, posi` |
| `reports/robust_asr/task_reports/P0.1_bootstrap.md` | 26 | False | `- reports/robust_asr/task_reports/P0.1_bootstrap.md  (this file)` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 23 | False | `continue_without_per_task_plan_approval:    false` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 24 | False | `continue_without_per_task_closure_approval: false` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 29 | False | `requested_task_matches_tracker:       true` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 30 | False | `latest_task_report_path:      reports/robust_asr/task_reports/P0.1_bootstrap.md` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 39 | False | `task_id:    P0.2` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 40 | False | `task_title: Inventory existing assets and lock reuse policy` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 64 | False | `- reports/robust_asr/task_reports/P0.2_asset_inventory.md` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 297 | False | `state_transport.latest_execution_report: reports/robust_asr/task_reports/P0.2_asset_inventory.md` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 326 | False | `continue_without_per_task_plan_approval:    false` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 327 | False | `continue_without_per_task_closure_approval: false` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 332 | False | `requested_task_matches_tracker:       true` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 333 | False | `latest_task_report_path:      reports/robust_asr/task_reports/P0.2_asset_inventory.md` |
| `reports/robust_asr/task_reports/P0.2_asset_inventory.md` | 358 | False | `2. docs/claude_task_progress.{md,yaml}: ABSENT from repo. No rows required.` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 20 | False | `session_log_overrides: {continue_without_per_task_plan_approval: false, continue_without_per_task_closure_approval: false, continue_through_gates: false}` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 24 | False | `requested_task_matches_tracker: true` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 25 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 32 | False | `task_id: P0.3-rebuild` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 33 | False | `parent_task_id: P0.3` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 34 | False | `task_title: Build robust_asr Apptainer image at the new authorized path` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 46 | False | `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 73 | False | `validator_evidence: basename matches p<task_id>_*.sh` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 125 | False | `- "Write reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md (this file)"` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 179 | False | `- {path: reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md,                               exists: true, sha256: <computed at commit time>}` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 203 | False | `- {path: reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md,                                                            large_artifact: false, committed_to_git: true}` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 229 | False | `parent_task_id: P0.3` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 251 | False | `latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 257 | False | `task_id: P0.3-rebuild` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 284 | False | `session_log_overrides: {continue_without_per_task_plan_approval: false, continue_without_per_task_closure_approval: false, continue_through_gates: false}` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 288 | False | `requested_task_matches_tracker: true` |
| `reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` | 289 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.3_runtime_image_rebuild.md` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 23 | False | `session_log_overrides: {continue_without_per_task_plan_approval: false, continue_without_per_task_closure_approval: false, continue_through_gates: false}` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 27 | False | `requested_task_matches_tracker: true` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 28 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 35 | False | `task_id: P0.3-rerun-2` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 36 | False | `parent_task_id: P0.3` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 37 | False | `task_title: Rerun runtime smoke against new image with env-isolated apptainer exec` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 39 | False | `parent_task_outcome: PASS` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 50 | False | `reports/robust_asr/task_reports/P0.3_runtime_smoke.md                (this file; PASS)` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 87 | False | `- "Write reports/robust_asr/task_reports/P0.3_runtime_smoke.md (this file; PASS)"` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 135 | False | `- {path: reports/robust_asr/task_reports/P0.3_runtime_smoke.md,              large_artifact: false, committed_to_git: true}` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 162 | False | `parent_task_id: P0.3` |
| `reports/robust_asr/task_reports/P0.3_runtime_smoke.md` | 181 | False | `latest_execution_report: reports/robust_asr/task_reports/P0.3_runtime_smoke.md` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 21 | False | `session_log_overrides: {continue_without_per_task_plan_approval: false, continue_without_per_task_closure_approval: false, continue_through_gates: false}` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 25 | False | `requested_task_matches_tracker: true` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 26 | False | `latest_task_report_path: reports/robust_asr/task_reports/P0.4_runtime_contract.md` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 30 | False | `task_id: P0.4` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 35 | False | `task_id: P0.4-scope-change` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 43 | False | `task_id: P0.4` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 44 | False | `task_title: RP5 runtime contract skeleton (request/response JSON + 19 assertions)` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 64 | False | `reports/robust_asr/task_reports/P0.4_runtime_contract.md   (this file)` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 114 | False | `- "Write reports/robust_asr/task_reports/P0.4_runtime_contract.md (this file)"` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 156 | False | `- {path: reports/robust_asr/task_reports/P0.4_runtime_contract.md,               large_artifact: false, committed_to_git: true}` |
| `reports/robust_asr/task_reports/P0.4_runtime_contract.md` | 195 | False | `latest_execution_report: reports/robust_asr/task_reports/P0.4_runtime_contract.md` |
| `reports/robust_asr/task_reports/P0.5_card_templates.md` | 15 | False | `task_id: P0.4` |
| `reports/robust_asr/task_reports/P0.5_card_templates.md` | 26 | False | `task_id: P0.5` |
| `reports/robust_asr/task_reports/P0.5_card_templates.md` | 41 | False | `- `reports/robust_asr/task_reports/P0.5_card_templates.md` (this report)` |
| `reports/robust_asr/task_reports/P0.5_card_templates.md` | 103 | False | `- `state_transport.latest_execution_report = reports/robust_asr/task_reports/P0.5_card_templates.md`` |
| `reports/robust_asr/task_reports/P1.1_data_inventory.md` | 59 | False | `| `test -f reports/robust_asr/task_reports/P1.1_data_inventory.md` | — | OK |` |
| `reports/robust_asr/task_reports/P1.1_data_inventory.md` | 78 | False | `- `reports/robust_asr/task_reports/P1.1_data_inventory.md` (this file, rewritten)` |
| `reports/robust_asr/task_reports/P1.1_data_inventory.md` | 94 | False | `- `state_transport.latest_planning_report:` `reports/robust_asr/task_reports/P1.1_data_inventory.md`` |
| `reports/robust_asr/task_reports/P1.1_data_inventory.md` | 95 | False | `- `state_transport.latest_execution_report:` `reports/robust_asr/task_reports/P1.1_data_inventory.md`` |
| `reports/robust_asr/task_reports/P1.2_eval_schema.md` | 3 | False | `- task_id: P1.2` |
| `reports/robust_asr/task_reports/P1.3_manifest_summary.md` | 77 | False | `- `reports/robust_asr/task_reports/P1.3_manifest_summary.md` (this file).` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 29 | False | `- task_id: `P10.1`` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 30 | False | `- task_title: "Final verification"` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 38 | False | `task_id: P10.1` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 89 | False | `- `reports/robust_asr/task_reports/P10.1_final_verification.md` (NEW; this file)` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 122 | False | `- `reports/robust_asr/**` (line 65–68 of `configs/robust_asr/reuse_policy_v1.yaml`): `allowed_tasks` includes `P10.1`. Permits writing `reports/robust_asr/final_verification.md` and `reports/robust_asr/task_reports/P10.1_final_verification.` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 132 | False | `- `state_transport.latest_planning_report` ← `reports/robust_asr/task_reports/P10.1_final_verification.md` (this exec replaces an older `P1.1_data_inventory.md` placeholder).` |
| `reports/robust_asr/task_reports/P10.1_final_verification.md` | 133 | False | `- `state_transport.latest_execution_report` ← `reports/robust_asr/task_reports/P10.1_final_verification.md`.` |
| `reports/robust_asr/task_reports/P2.1_baseline.md` | 160 | False | `- `reports/robust_asr/task_reports/P2.1_baseline.md` (this file).` |
| `reports/robust_asr/task_reports/P3.1_lora_smoke.md` | 31 | False | `| 2131889 | FAILED 1:0 | 00:00:22 | Downloaded `config.json` to HF cache; PEFT `task_type="SEQ_2_SEQ_LM"` caused PEFT to forward `input_ids` into `WhisperForConditionalGeneration.forward` which expects `input_features`. |` |
| `reports/robust_asr/task_reports/P3.1_lora_smoke.md` | 32 | False | `| 2131891 | FAILED 1:0 | 00:09:42 | Removed `task_type`; eval emitted "no eval rows produced" because `eval_audio_id` was built as the manifest's base id and did not match the baseline parquet's `base::degradation_id::tier` key. |` |
| `reports/robust_asr/task_reports/P3.2_decision_a.md` | 35 | False | `- `reports/robust_asr/task_reports/P3.2_decision_a.md` — this file.` |
| `reports/robust_asr/task_reports/P5.1_assemblyai.md` | 35 | False | ``ASSEMBLYAI_API_KEY` is unset in the datamove1 environment. Per` |
| `reports/robust_asr/task_reports/P5.1_assemblyai.md` | 96 | False | `1. **KEY_UNSET** (exit 8) when `ASSEMBLYAI_API_KEY` is missing.` |
| `reports/robust_asr/task_reports/P6.1_selector_evidence.md` | 45 | False | ``selected_action`, `selector_reason`, `ask_repeat_allowed`,` |
| `reports/robust_asr/task_reports/P6.1_selector_evidence.md` | 94 | False | `| `ask_repeat`            | 28     | 0.0526 %  | `no_speech` |` |
| `reports/robust_asr/task_reports/P6.1_selector_evidence.md` | 97 | False | ``ask_repeat_allowed=True` on every row (validator §993-§996 hold).` |
| `reports/robust_asr/task_reports/P6.1_selector_evidence.md` | 141 | False | ``ask_repeat`.").` |
| `reports/robust_asr/task_reports/P7.3_router_package.md` | 103 | False | ``ask_repeat_threshold = -1.0`, `escalate_threshold = -0.5`,` |
| `reports/robust_asr/task_reports/P7.3_router_package.md` | 125 | False | `| `ask_repeat_rate`                       | 0.0526 % |` |
| `reports/robust_asr/task_reports/P7.3_router_package.md` | 139 | False | `Regret is identically zero because the 28 `ask_repeat` rows already` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 39 | False | ``[whisper_base_ct2_int8, ask_repeat]` is reachable when both` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 44 | False | `- `ask_repeat` WER policy (primary): 1.0 (full-miss convention; §5.4` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 102 | False | `## Headline numbers (Decision D, primary policy ask_repeat_wer=1.0)` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 107 | False | `| selector action mix | `whisper_base_ct2_int8` 53 202 (99.9474 %), `ask_repeat` 28 (0.0526 %), `assemblyai` 0, `whisper_lora_ct2_int8` 0 |` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 120 | False | `Reason: all 28 `ask_repeat` rows already have` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 122 | False | ``ask_repeat_wer=1.0` policy the per-row delta is identically zero;` |
| `reports/robust_asr/task_reports/P8.1_system_eval.md` | 128 | False | `## Sensitivity check (ask_repeat_wer = 0.5)` |
| `reports/robust_asr/task_reports/P8.2_demo_manifest.md` | 51 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md` (this report).` |
| `reports/robust_asr/task_reports/P8.2_demo_manifest.md` | 321 | False | `- `reports/robust_asr/task_reports/P8.2_demo_manifest.md` (this` |
| `reports/robust_asr/task_reports/P8_GATE_attempt2.md` | 27 | False | `- task_id: `P8_GATE`` |
| `reports/robust_asr/task_reports/P8_GATE_attempt2.md` | 45 | False | `- evidence: live `head -n 1` of the file (returned `positive_system: false`); cross-reference `reports/robust_asr/task_reports/P8.1_system_eval.md` and `tasks.P8.1.notes` recording Slurm job `2132279` COMPLETED 0:0 producing the file.` |
| `reports/robust_asr/task_reports/P8_GATE_attempt2.md` | 95 | False | `- `state_transport.latest_phase_gate_report`: `null` → **`reports/robust_asr/task_reports/P8_GATE_attempt2.md`**.` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 29 | False | `requested_task_matches_tracker: true` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 33 | False | `task_id: P8_GATE` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 44 | False | `- task_id: **P9.0**` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 45 | False | `- task_title: Final runtime contract` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 56 | False | `reports/robust_asr/task_reports/P9.0_runtime_contract.md          (new)` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 106 | False | `A11 PASS: response.ask_repeat=False` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 107 | False | `A12 PASS: transcript_is_null=False ask_repeat=False errors_nonempty=False` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 108 | False | `A13 PASS: selected_backend='whisper_base_ct2_int8' ask_repeat=False` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 242 | False | ``reports/robust_asr/task_reports/P9.0_runtime_contract.md`.` |
| `reports/robust_asr/task_reports/P9.0_runtime_contract.md` | 297 | False | `state_transport.latest_execution_report: reports/robust_asr/task_reports/P9.0_runtime_contract.md` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 31 | False | `task_id: P9.0` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 40 | False | `- task_id: **P9.1**` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 41 | False | `- task_title: Handoff package` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 68 | False | `reports/robust_asr/task_reports/P9.1_handoff_package.md                             (new)` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 137 | False | `24. Write reports/robust_asr/task_reports/P9.1_handoff_package.md` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 156 | False | `A6 PASS: no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 277 | False | `config grep for `ASSEMBLYAI_API_KEY` / `sk_` / `Bearer ` returned 0` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 330 | False | ``reports/robust_asr/task_reports/P9.1_handoff_package.md`.` |
| `reports/robust_asr/task_reports/P9.1_handoff_package.md` | 386 | False | `state_transport.latest_execution_report: reports/robust_asr/task_reports/P9.1_handoff_package.md` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 3 | False | `- task_id: P9.2` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 104 | False | `| `ACTION_CLOUD = "assemblyai"` | non-deployed dead code in this handoff | NO (intentional) | `selected_router/deterministic_selector.json` `deployable_actions` excludes `assemblyai`; `assemblyai_action_emitted_when = "assemblyai_available=` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 105 | False | `| `ACTION_ASK_REPEAT = "ask_repeat"` | control action (not a backend) | YES | `selected_router/deterministic_selector.json` `deployable_actions` includes `ask_repeat`; no backend invocation required |` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 209 | False | `A6 PASS: no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 296 | False | ``reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md`` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 321 | False | `- `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md`` |
| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | 353 | False | `- `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md`` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 5 | False | `- task_id: P9.2` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 103 | False | `A6 PASS: no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 117 | False | `| A6 | PASS   | no `ASSEMBLYAI_API_KEY` / `sk_` / `Bearer ` in `backend_configs/` |` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 147 | False | `| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | new (this file) |` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 167 | False | `| `reports/robust_asr/task_reports/P9.2_rp5_runtime_spec.md` | **unchanged** (this fix does not require touching the P9.2 execution report; the report's discussion of the prior strict-A7 outcome is now superseded by this fix report; future ` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 191 | False | ``reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md`` |
| `reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md` | 227 | False | ``reports/robust_asr/task_reports/P9.2_strict_tag_validator_fix.md`` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 32 | False | `- task_id: `P9_GATE`` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 70 | False | `- A11 PASS: response.ask_repeat=False` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 71 | False | `- A12 PASS: transcript/ask_repeat/errors consistency` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 99 | False | `- A6 PASS: no `ASSEMBLYAI_API_KEY` / `sk_` / `Bearer ` in `backend_configs/`` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 135 | False | `- `tasks.P9_GATE` added: `attempt=1`, `status=PASS`, `predicate_inputs=` the 12 observed values above with PASS/FAIL flags, `report=reports/robust_asr/task_reports/P9_GATE_attempt1.md`.` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 136 | False | `- `state_transport.latest_phase_gate_report`: `reports/robust_asr/task_reports/P8_GATE_attempt2.md` → **`reports/robust_asr/task_reports/P9_GATE_attempt1.md`**.` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 174 | False | `- `reports/robust_asr/task_reports/P9.0_runtime_contract.md`, `P9.1_handoff_package.md`, `P9.2_rp5_runtime_spec.md`, `P9.2_strict_tag_validator_fix.md` — byte-unchanged.` |
| `reports/robust_asr/task_reports/P9_GATE_attempt1.md` | 214 | False | `- (post-write) `git add reports/robust_asr/task_reports/P9_GATE_attempt1.md docs/progress/robust_asr_progress.yaml docs/progress/robust_asr_progress.md docs/progress/robust_asr_state_capsule.md; git commit -m 'Evaluate P9 robust ASR gate'; ` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 21 | False | `- "docs/reports/robust_asr/model_card_lora.md exists; no residual TODO_FILLED_IN_<task_id> for closed tasks."` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 22 | False | `- "docs/reports/robust_asr/router_card.md exists; no residual TODO_FILLED_IN_<task_id> for closed tasks."` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 24 | False | `Section 4.1 §1105–§1119 defines `final_asset_audit.py` Assertion 3: "No residual TODO_FILLED_IN_<task_id> tokens for tasks whose tracker.tasks[<task_id>].status == PASS." Decision Rule 1 (§4288): "Residual TODO_FILLED_IN_<task_id> for close` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 28 | False | `Pre-amendment, the cards contained 30 (model card) + 24 (router card) = 54 `TODO_FILLED_IN_<task_id>` tokens, of which a strict count of ≥ 18 occurrences targeted PASS-status tasks (P1.2, P1.4, P2.1, P3.1, P3.2, P6.1, P7.3, P8.1, P8.2, P9.1` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 38 | False | `5. Agent plan Section 10 items 11–12 §4355–§4358 normatively require absence of residual `TODO_FILLED_IN_<task_id>` for closed tasks in BOTH cards as a pre-COMPLETE condition.` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 73 | False | `notes: Model card and router card templates (P0.5 seeded; finalized progressively). model_router_card_completion added under CHANGE_SCOPE on accepted_report_commit d714bac8f4d49e7a5b0ca7616a6ee5758a330d5d to fill or N/A-rewrite every TODO_F` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 92 | False | `- `reports/robust_asr/task_reports/model_router_card_completion.md` (this report; new)` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 101 | False | `- `docs/reports/robust_asr/model_card_lora.md`: 30 `TODO_FILLED_IN_<task_id>` tokens covering task ids `[P1.1, P1.2, P1.3, P1.4, P2.1, P3.1, P3.2, P4.1, P4.2, P4.3, P5.1, P8.1, P8.2, P9.1]`.` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 102 | False | `- `docs/reports/robust_asr/router_card.md`: 24 `TODO_FILLED_IN_<task_id>` tokens covering task ids `[P1.3, P5.1, P6.1, P6.2, P7.1, P7.2, P7.3, P8.1, P8.2, P9.1]`.` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 117 | False | `For each `<task_id>` whose placeholder appeared in the cards, the following replacement rule was applied (per the orchestrator-issued source mappings):` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 128 | False | `- `P5.1` (HALTED — `BLOCKED_API`): replaced with "**N/A — HALTED under BLOCKED_API**" plus marker citation, citing handoff README §6.3 and `verify_handoff_package.py --strict` A6 secret-scan PASS. Confirmed: AssemblyAI is NOT an enabled bac` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 167 | False | `- `reports/robust_asr/task_reports/P10.1_final_verification.md` sha256 `ed7b149b…` held.` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 168 | False | `- All other prior task reports under `reports/robust_asr/task_reports/` — byte-unchanged.` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 206 | False | `1. Create `scripts/robust_asr/final_asset_audit.py` per agent plan §1105–§1119 (under `task_id=P10.2`, authorized by the prior `reuse_policy_p10_2_script_allowance` CHANGE_SCOPE on `9452afc…`).` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 207 | False | `2. Run it. With cards now fully filled, Assertion 3 ("No residual TODO_FILLED_IN_<task_id> tokens for tasks whose tracker.tasks[<task_id>].status == PASS") is expected to PASS regardless of `--report-root` scope (whether `reports/robust_asr` |
| `reports/robust_asr/task_reports/model_router_card_completion.md` | 208 | False | `3. Write `reports/robust_asr/final_asset_audit.md` and `reports/robust_asr/task_reports/P10.2_final_audit.md`.` |
| `reports/robust_asr/task_reports/plan_index_refresh.md` | 95 | False | ``reports/robust_asr/task_reports/P8.1_system_eval.md`,` |
| `reports/robust_asr/task_reports/plan_index_refresh.md` | 96 | False | ``reports/robust_asr/task_reports/P8.2_demo_manifest.md`.` |
| `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` | 82 | False | `Agent plan §4275 (P10.2 Action 1) requires running `final_asset_audit.py`, which does not yet exist on disk. Per agent plan §915, scripts referenced by the plan must satisfy their Section-4.1 contract. The implementation commit of `scripts/` |
| `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` | 119 | False | `- `reports/robust_asr/task_reports/P10.1_final_verification.md` sha256 `ed7b149b…` held.` |
| `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` | 120 | False | `- All prior task reports under `reports/robust_asr/task_reports/` (P0.x, P1.x, P2.1, P3.x, P5.1, P6.1, P7.3, P8.1, P8.2, P8_GATE_attempt2, P9.0, P9.1, P9.2, P9.2_strict_tag_validator_fix, P9_GATE_attempt1, plan_index_refresh, P10.1) — byte-` |
| `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` | 131 | False | `- `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` (this report; new)` |
| `reports/robust_asr/task_reports/reuse_policy_p10_2_script_allowance.md` | 138 | False | `Orchestrator returns `APPROVE_PLAN(P10.2)` against the planning report. P10.2 implementation may then proceed with creation of `scripts/robust_asr/final_asset_audit.py` (per agent plan §1105–§1119), running it (default `--report-root=report` |
| `reports/robust_asr/touch_policy.md` | 11 | False | `| task_id | allowed_write_paths | allowed_read_paths | default_no_touch_paths | external_paths_requiring_approval |` |
| `reports/robust_asr/touch_policy.md` | 14 | False | `| P0.1 | docs/profiles/CLAUDE.robust_asr.md, CLAUDE.md (block only), docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md, reports/robust_asr/repository_inventory.md, report` |
| `reports/robust_asr/touch_policy.md` | 15 | False | `| P0.2 | reports/robust_asr/asset_inventory.md, reports/robust_asr/repo_integration_policy.md, reports/robust_asr/touch_policy.md, configs/robust_asr/reuse_policy_v1.yaml, scripts/robust_asr/validate_report_shape.py, artifacts/robust_asr/st` |
| `reports/robust_asr/touch_policy.md` | 16 | False | `| P0.3 | reports/robust_asr/runtime_smoke.md, artifacts/robust_asr/runtime_smoke/runtime_smoke_job_metadata.json, artifacts/robust_asr/runtime_smoke/stdout.txt, artifacts/robust_asr/runtime_smoke/stderr.txt, reports/robust_asr/task_reports/` |
| `reports/robust_asr/touch_policy.md` | 17 | False | `| P0.4 | artifacts/robust_asr/runtime_contract/rp5_request_fixture.json, artifacts/robust_asr/runtime_contract/rp5_response_fixture.json, libs/common/runtime_contract.py, scripts/robust_asr/validate_runtime_contract.py, tests/robust_asr/tes` |
| `reports/robust_asr/touch_policy.md` | 18 | False | `| P0.5 | docs/reports/robust_asr/model_card_lora.md, docs/reports/robust_asr/router_card.md, reports/robust_asr/task_reports/P0.5_card_templates.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress` |
| `reports/robust_asr/touch_policy.md` | 19 | False | `| P1.1 | configs/robust_asr/data_v1.yaml, reports/robust_asr/data_inventory.md, reports/robust_asr/task_reports/P1.1_data_inventory.md, scripts/robust_asr/check_speaker_disjoint.py, configs/robust_asr/reuse_policy_v1.yaml (scope-change rows` |
| `reports/robust_asr/touch_policy.md` | 20 | False | `| P1.2 | libs/common/eval_schema.yaml, libs/common/normalization.py, libs/common/metrics.py, libs/common/versions.py (append NORMALIZATION_VERSION only; existing constants preserved), scripts/robust_asr/validate_eval_schema.py, tests/robust` |
| `reports/robust_asr/touch_policy.md` | 21 | False | `| P1.3 | scripts/robust_asr/build_public_manifests.py, scripts/robust_asr/summarize_manifests.py, artifacts/robust_asr/manifests/*.parquet, reports/robust_asr/manifest_summary.md, reports/robust_asr/task_reports/P1.3_manifest_summary.md, re` |
| `reports/robust_asr/touch_policy.md` | 22 | False | `| P1.4 | libs/audio/degradations.py (append-only narrow patch: add sample_clean, sample_cafe_noise, sample_phone_band, sample_far_field_room, sample_muffled_lowpass; preserve existing apply_degradation, DEGRADATION_FAMILIES, and DEGRADATION` |
| `reports/robust_asr/touch_policy.md` | 23 | False | `| P2.1 | configs/robust_asr/eval_manifests_v1.yaml, scripts/robust_asr/run_backend_eval.py, scripts/robust_asr/summarize_backend_eval.py, scripts/robust_asr/validate_eval_table.py, scripts/robust_asr/build_whisper_base_ct2_int8.py, slurm/jo` |
| `reports/robust_asr/touch_policy.md` | 24 | False | `| P2.2 | configs/robust_asr/lora_smoke.yaml, reports/robust_asr/task_reports/P2.2_lora_smoke_config.md, reports/robust_asr/touch_policy.md (scope-change rows), docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, do` |
| `reports/robust_asr/touch_policy.md` | 25 | False | `| P3.1 | scripts/robust_asr/train_lora_smoke.py, scripts/robust_asr/evaluate_lora_smoke.py, scripts/robust_asr/smoke_export_lora_ct2.py, slurm/jobs/p3_1_lora_smoke.sh, tests/robust_asr/test_lora_smoke.py, artifacts/robust_asr/lora_smoke/che` |
| `reports/robust_asr/touch_policy.md` | 26 | False | `| P3.2 | scripts/robust_asr/decide_lora_smoke.py, tests/robust_asr/test_decide_lora_smoke.py, reports/robust_asr/lora/lora_smoke_report.md, reports/robust_asr/lora/decision_a_smoke.md, reports/robust_asr/task_reports/P3.2_decision_a.md, rep` |
| `reports/robust_asr/touch_policy.md` | 27 | False | `| P4.1 | artifacts/robust_asr/lora_full/*, artifacts/robust_asr/lora_merged_fp16/*, reports/robust_asr/task_reports/P4.1_lora_full.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_st` |
| `reports/robust_asr/touch_policy.md` | 28 | False | `| P4.2 | artifacts/robust_asr/eval_tables/whisper_lora_fp16.parquet, reports/robust_asr/lora/full_lora_eval.md, reports/robust_asr/task_reports/P4.2_lora_eval.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md,` |
| `reports/robust_asr/touch_policy.md` | 29 | False | `| P4.3 | artifacts/robust_asr/lora_ct2_int8/*, artifacts/robust_asr/eval_tables/whisper_lora_ct2_int8.parquet, reports/robust_asr/lora/lora_ct2_int8_preservation.md, reports/robust_asr/task_reports/P4.3_int8_preservation.md, docs/progress/r` |
| `reports/robust_asr/touch_policy.md` | 30 | False | `| P5.1 | configs/robust_asr/pricing_v1.yaml, configs/robust_asr/eval_manifests_v1.yaml (append assemblyai backend_endpoints entry; existing entries preserved), configs/robust_asr/reuse_policy_v1.yaml (scope-change rows), scripts/robust_asr/` |
| `reports/robust_asr/touch_policy.md` | 31 | False | `| P6.1 | configs/robust_asr/router_v1.yaml, scripts/robust_asr/build_selector_evidence_table.py, scripts/robust_asr/validate_selector_evidence.py, artifacts/robust_asr/router/selector_evidence.parquet, reports/robust_asr/router/selector_evi` |
| `reports/robust_asr/touch_policy.md` | 32 | False | `| P6.2 | artifacts/robust_asr/router/router_features.parquet, artifacts/robust_asr/router/train_matrix.parquet (or similar), artifacts/robust_asr/router/val_matrix.parquet, artifacts/robust_asr/router/test_locked_matrix.parquet, reports/rob` |
| `reports/robust_asr/touch_policy.md` | 33 | False | `| P7.1 | reports/robust_asr/router/*, reports/robust_asr/task_reports/P7.1_router_select.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | Plan files, router matric` |
| `reports/robust_asr/touch_policy.md` | 34 | False | `| P7.2 | artifacts/robust_asr/router/candidates/*, reports/robust_asr/task_reports/P7.2_router_train.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md, slurm/jobs/p7_` |
| `reports/robust_asr/touch_policy.md` | 35 | False | `| P7.3 | scripts/robust_asr/package_deterministic_selector.py, scripts/robust_asr/evaluate_deterministic_selector.py, tests/robust_asr/test_router_runtime.py, artifacts/robust_asr/router/selected_router/**, reports/robust_asr/router/selecto` |
| `reports/robust_asr/touch_policy.md` | 36 | False | `| P8.1 | scripts/robust_asr/evaluate_system.py, slurm/jobs/p8_1_system_eval.sh, reports/robust_asr/system/system_eval.md, reports/robust_asr/task_reports/P8.1_system_eval.md, reports/robust_asr/touch_policy.md (scope-change row), docs/progr` |
| `reports/robust_asr/touch_policy.md` | 37 | False | `| P8.2 | scripts/robust_asr/build_demo_examples.py, artifacts/robust_asr/demo/demo_examples_manifest.json, artifacts/robust_asr/demo/audio/** (exactly 8 small public WAV files; carveout from generic *.wav no-touch rule per reuse_policy_v1.y` |
| `reports/robust_asr/touch_policy.md` | 38 | False | `| P9.0 | artifacts/robust_asr/runtime_contract/final_response_schema.json, reports/robust_asr/task_reports/P9.0_final_contract.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_` |
| `reports/robust_asr/touch_policy.md` | 39 | False | `| P9.1 | artifacts/robust_asr/handoff/*, reports/robust_asr/task_reports/P9.1_handoff_package.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | Plan files, all robu` |
| `reports/robust_asr/touch_policy.md` | 40 | False | `| P9.2 | artifacts/robust_asr/handoff/rp5_runtime_spec.md, reports/robust_asr/task_reports/P9.2_rp5_spec.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | Plan file` |
| `reports/robust_asr/touch_policy.md` | 41 | False | `| P10.1 | reports/robust_asr/final_verification.md, reports/robust_asr/task_reports/P10.1_final_verification.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | All r` |
| `reports/robust_asr/touch_policy.md` | 42 | False | `| P10.2 | reports/robust_asr/final_asset_audit.md, reports/robust_asr/task_reports/P10.2_final_audit.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | All robust_as` |
| `reports/robust_asr/touch_policy.md` | 43 | False | `| P10.3 | reports/robust_asr/plan_tracker_consistency.md, reports/robust_asr/task_reports/P10.3_consistency.md, docs/progress/robust_asr_progress.yaml, docs/progress/robust_asr_progress.md, docs/progress/robust_asr_state_capsule.md | All ro` |
| `scripts/robust_asr/build_degradation_v1.py` | 275 | False | `free_gb = shutil.disk_usage(audio_root).free / (1024 ** 3)` |
| `scripts/robust_asr/build_degradation_v1.py` | 372 | False | `free_gb_post = shutil.disk_usage(audio_root).free / (1024 ** 3)` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 17 | False | `ask_repeat}` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 19 | False | `ask_repeat_allowed                bool` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 63 | False | `ask_repeat_threshold: float,` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 76 | False | `return "ask_repeat", "no_speech"` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 77 | False | `if avg_logprob < ask_repeat_threshold:` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 78 | False | `return "ask_repeat", "low_logprob"` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 129 | False | `ask_repeat_threshold = float(det_cfg["ask_repeat_threshold"])` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 194 | False | `ask_repeat_threshold=ask_repeat_threshold,` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 209 | False | `ask_repeat_allowed = [True] * n` |
| `scripts/robust_asr/build_selector_evidence_table.py` | 224 | False | `"ask_repeat_allowed": ask_repeat_allowed,` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 4 | False | `Computes deterministic-selector WER, Word Accuracy, ask_repeat_rate,` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 43 | False | `# Convention for ask_repeat-arm WER in regret computation: the user is` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 145 | False | `return "ask_repeat"` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 146 | False | `if avg_logprob < constants["ask_repeat_threshold"]:` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 147 | False | `return "ask_repeat"` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 207 | False | `actions == "ask_repeat", ASK_REPEAT_WER, baseline_wer` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 210 | False | `actions == "ask_repeat", ASK_REPEAT_WA, baseline_wa` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 215 | False | `n_ask_repeat = int((actions == "ask_repeat").sum())` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 220 | False | `ask_repeat_rate = n_ask_repeat / n` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 222 | False | `local_only_rate = (n_baseline + n_ask_repeat + n_lora) / n  # i.e. non-cloud` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 223 | False | `transcript_emitted_rate = (n - n_ask_repeat) / n` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 229 | False | `# Latency proxy: baseline + ask_repeat both run locally on` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 230 | False | `# whisper_base_ct2_int8; ask_repeat additionally prompts the user` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 294 | False | `f"`ask_repeat_threshold={constants['ask_repeat_threshold']}`, "` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 320 | False | `f"| `ask_repeat`            | {n_ask_repeat:>6d} | {pct(ask_repeat_rate):>12s} |"` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 338 | False | `f"- `transcript_emitted_rate` (non-`ask_repeat`): "` |
| `scripts/robust_asr/evaluate_deterministic_selector.py` | 359 | False | `"is emitted on `ask_repeat`; using a maximum-penalty convention "` |
| `scripts/robust_asr/evaluate_system.py` | 146 | False | `actions: np.ndarray, baseline_wer: np.ndarray, ask_repeat_wer: float` |
| `scripts/robust_asr/evaluate_system.py` | 149 | False | `out[actions == "ask_repeat"] = ask_repeat_wer` |
| `scripts/robust_asr/evaluate_system.py` | 156 | False | `ask_repeat_wer: float,` |
| `scripts/robust_asr/evaluate_system.py` | 161 | False | `selector_wer = _selector_wer(actions, baseline_wer, ask_repeat_wer)` |
| `scripts/robust_asr/evaluate_system.py` | 178 | False | `"ask_repeat_wer": ask_repeat_wer,` |
| `scripts/robust_asr/evaluate_system.py` | 304 | False | `args.ask_repeat_wer,` |
| `scripts/robust_asr/evaluate_system.py` | 311 | False | `for s_wer in args.ask_repeat_wer_sensitivity:` |
| `scripts/robust_asr/evaluate_system.py` | 312 | False | `if s_wer == args.ask_repeat_wer:` |
| `scripts/robust_asr/evaluate_system.py` | 391 | False | `f"- ask_repeat WER policy (primary): "` |
| `scripts/robust_asr/evaluate_system.py` | 392 | False | `f"{args.ask_repeat_wer}"` |
| `scripts/robust_asr/evaluate_system.py` | 396 | False | `str(r["ask_repeat_wer"]) for r in sens_runs` |
| `scripts/robust_asr/evaluate_system.py` | 399 | False | `f"- ask_repeat WER sensitivity values: {sens_vals}"` |
| `scripts/robust_asr/evaluate_system.py` | 402 | False | `lines.append("## Primary result (ask_repeat WER = "` |
| `scripts/robust_asr/evaluate_system.py` | 403 | False | `f"{args.ask_repeat_wer})")` |
| `scripts/robust_asr/evaluate_system.py` | 462 | False | `"always-baseline is the 28 `ask_repeat` rows (selector_reason "` |
| `scripts/robust_asr/evaluate_system.py` | 464 | False | `"= 1.0` already, so at the primary policy ask_repeat_wer=1.0 "` |
| `scripts/robust_asr/evaluate_system.py` | 472 | False | `lines.append("## Sensitivity check (alternative ask_repeat WER)")` |
| `scripts/robust_asr/evaluate_system.py` | 478 | False | `f"- ask_repeat_wer = {sens['ask_repeat_wer']}: "` |
| `scripts/robust_asr/package_deterministic_selector.py` | 105 | False | `ACTION_ASK_REPEAT = "ask_repeat"` |
| `scripts/robust_asr/package_deterministic_selector.py` | 142 | False | `ask_repeat_threshold = _CONSTANTS["ask_repeat_threshold"]` |
| `scripts/robust_asr/package_deterministic_selector.py` | 151 | False | `if avg_logprob < ask_repeat_threshold:` |
| `scripts/robust_asr/package_deterministic_selector.py` | 209 | False | `"ask_repeat_threshold",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 227 | False | `ar = constants["ask_repeat_threshold"]   # -1.0` |
| `scripts/robust_asr/package_deterministic_selector.py` | 239 | False | `"expected_action": "ask_repeat",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 244 | False | `"expected_action": "ask_repeat",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 261 | False | `"expected_action": "ask_repeat",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 266 | False | `"expected_action": "ask_repeat",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 333 | False | `"expected_action": "ask_repeat",` |
| `scripts/robust_asr/package_deterministic_selector.py` | 380 | False | `"deployable_actions": ["whisper_base_ct2_int8", "ask_repeat"],` |
| `scripts/robust_asr/package_deterministic_selector.py` | 429 | False | `"ask_repeat_supported": True,` |
| `scripts/robust_asr/populate_assemblyai_cache.py` | 9 | False | `1. If ASSEMBLYAI_API_KEY is unset → exit 8 (KEY_UNSET); no requests.` |
| `scripts/robust_asr/populate_assemblyai_cache.py` | 19 | False | `5. ASSEMBLYAI_API_KEY is never logged or written to disk.` |
| `scripts/robust_asr/populate_assemblyai_cache.py` | 25 | False | `8 ASSEMBLYAI_API_KEY_UNSET` |
| `scripts/robust_asr/populate_assemblyai_cache.py` | 321 | False | `key = os.environ.get("ASSEMBLYAI_API_KEY")` |
| `scripts/robust_asr/populate_assemblyai_cache.py` | 323 | False | `print("ASSEMBLYAI_API_KEY_UNSET", file=sys.stderr)` |
| `scripts/robust_asr/probe_assemblyai_runtime.py` | 5 | False | `- If ASSEMBLYAI_API_KEY is unset, prints` |
| `scripts/robust_asr/probe_assemblyai_runtime.py` | 13 | False | `The script never logs or persists the value of ASSEMBLYAI_API_KEY.` |
| `scripts/robust_asr/probe_assemblyai_runtime.py` | 29 | False | `key = env.get("ASSEMBLYAI_API_KEY")` |
| `scripts/robust_asr/validate_selector_evidence.py` | 9 | False | `whisper_lora_ct2_int8, ask_repeat}.` |
| `scripts/robust_asr/validate_selector_evidence.py` | 36 | False | `"ask_repeat_allowed",` |
| `scripts/robust_asr/validate_selector_evidence.py` | 45 | False | `"ask_repeat",` |
| `scripts/robust_asr/verify_handoff_package.py` | 14 | False | `(grep for ASSEMBLYAI_API_KEY, sk_, Bearer ).` |
| `scripts/robust_asr/verify_handoff_package.py` | 53 | False | `"ASSEMBLYAI_API_KEY",` |
| `scripts/robust_asr/verify_handoff_package.py` | 54 | False | `"sk_",` |
| `scripts/robust_asr/verify_handoff_package.py` | 55 | False | `"Bearer ",` |
| `scripts/robust_asr/verify_handoff_package.py` | 158 | False | `# secrets (grep for ASSEMBLYAI_API_KEY, sk_, Bearer )." The scope is` |
| `scripts/robust_asr/verify_handoff_package.py` | 183 | False | `"no ASSEMBLYAI_API_KEY / sk_ / Bearer in backend_configs/")` |
| `scripts/training/build_degradation_bank.py` | 251 | False | `free_bytes = shutil.disk_usage(parent).free` |
| `scripts/training/models.py` | 138 | False | `a bounded mask M in [0, mask_max], multiplies the degraded magnitude by` |
| `scripts/training/models.py` | 155 | False | `mask_max: float = 2.0,` |
| `scripts/training/models.py` | 163 | False | `self.mask_max = float(mask_max)` |
| `scripts/training/models.py` | 243 | False | `mask = self.mask_max * torch.sigmoid(logits)` |
| `scripts/training/select_checkpoint.py` | 233 | False | `on_disk_shas: dict[int, str] = {}` |
| `scripts/training/select_checkpoint.py` | 237 | False | `on_disk_shas[step] = _sha256(ck)` |
| `scripts/training/select_checkpoint.py` | 243 | False | `if latest_sha != on_disk_shas[20000]:` |
| `scripts/training/select_checkpoint.py` | 250 | False | `f"step_0020000={on_disk_shas[20000]}"` |
| `scripts/training/select_checkpoint.py` | 322 | False | `on_disk_for_meta = _sha256(ck_path_meta)` |
| `scripts/training/select_checkpoint.py` | 323 | False | `if on_disk_for_meta != on_disk_shas[step]:` |
| `scripts/training/select_checkpoint.py` | 327 | False | `f"meta_path={ck_path_meta} meta_sha={on_disk_for_meta}; "` |
| `scripts/training/select_checkpoint.py` | 329 | False | `f"{on_disk_shas[step]}"` |
| `scripts/training/select_checkpoint.py` | 335 | False | `"sha256": on_disk_shas[step],` |
| `scripts/training/select_checkpoint.py` | 434 | False | `"checkpoint_step_0020000_sha256": on_disk_shas[20000],` |
| `services/api/app/main.py` | 276 | False | `"api.task_enqueued",` |
| `services/worker/app/celery_app.py` | 22 | False | `task_serializer="json",` |
| `services/worker/app/celery_app.py` | 55 | False | `name = getattr(celery_app.conf, "task_default_queue", None)` |
| `tests/asr_adapter/test_factory.py` | 38 | False | `with pytest.raises(AdapterTranscriptionError, match="ASSEMBLYAI_API_KEY"):` |
| `tests/integration/test_live_assemblyai.py` | 6 | False | `ASSEMBLYAI_API_KEY=<your key>` |
| `tests/integration/test_live_assemblyai.py` | 11 | False | `RUN_LIVE_ASSEMBLYAI_TEST=1 ASSEMBLYAI_API_KEY=<key> \\` |
| `tests/integration/test_live_assemblyai.py` | 27 | False | `_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")` |
| `tests/integration/test_live_assemblyai.py` | 33 | False | `_missing.append("ASSEMBLYAI_API_KEY")` |
| `tests/libs/test_settings.py` | 91 | False | `s = make(monkeypatch, extra={"ASR_PROVIDER": "assemblyai"}, drop=["ASSEMBLYAI_API_KEY"])` |
| `tests/libs/test_settings.py` | 96 | False | `s = make(monkeypatch, extra={"ASR_PROVIDER": "assemblyai", "ASSEMBLYAI_API_KEY": "testkey"})` |
| `tests/observability/test_json_formatter.py` | 132 | False | `record = _make_record(extra={"Authorization": "Bearer tok"})` |
| `tests/observability/test_queue_backlog_metric.py` | 39 | False | `monkeypatch.setattr(celery_app.conf, "task_default_queue", "asr_queue", raising=False)` |
| `tests/observability/test_queue_backlog_metric.py` | 44 | False | `monkeypatch.setattr(celery_app.conf, "task_default_queue", None, raising=False)` |
| `tests/robust_asr/test_assemblyai.py` | 65 | False | `monkeypatch.delenv("ASSEMBLYAI_API_KEY", raising=False)` |
| `tests/robust_asr/test_assemblyai.py` | 112 | False | `monkeypatch.delenv("ASSEMBLYAI_API_KEY", raising=False)` |
| `tests/robust_asr/test_assemblyai.py` | 123 | False | `if k != "ASSEMBLYAI_API_KEY"}},` |
| `tests/robust_asr/test_assemblyai.py` | 126 | False | `assert "ASSEMBLYAI_API_KEY_UNSET" in r.stderr` |
| `tests/robust_asr/test_assemblyai.py` | 137 | False | `monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test")` |
| `tests/robust_asr/test_assemblyai.py` | 155 | False | `monkeypatch.setenv("ASSEMBLYAI_API_KEY", "test")` |
| `tests/robust_asr/test_router_runtime.py` | 94 | False | `assert constants["ask_repeat_threshold"] == -1.0` |
| `tests/robust_asr/test_router_runtime.py` | 100 | False | `assert doc["deployable_actions"] == ["whisper_base_ct2_int8", "ask_repeat"]` |
| `tests/robust_asr/test_router_runtime.py` | 122 | False | `expected_actions = {"whisper_base_ct2_int8", "assemblyai", "ask_repeat"}` |
| `tests/robust_asr/test_router_runtime.py` | 225 | False | `"assert r['action'] == 'ask_repeat' and r['reason'] == 'no_speech', r\n"` |
| `tests/robust_asr/test_runtime_contract_skeleton.py` | 92 | False | `"A11": lambda q, s: s.__setitem__("ask_repeat", "false"),` |
| `tests/robust_asr/test_runtime_contract_skeleton.py` | 93 | False | `# A12: ask_repeat=False, errors=[] but transcript=null -> RHS False, LHS True` |
| `tests/robust_asr/test_runtime_contract_skeleton.py` | 95 | False | `# A13: ask_repeat=False but selected_backend=null -> LHS True, RHS False` |
| `tests/worker/test_celery_app.py` | 32 | False | `def test_ping_task_registered_by_name(celery_module):` |
| `tests/worker/test_celery_app.py` | 36 | False | `def test_ping_task_returns_pong(celery_module):` |
| `tests/worker/test_transcribe_task.py` | 567 | False | `"AssemblyAI provider selected but ASSEMBLYAI_API_KEY is not set"` |
| `tests/worker/test_transcribe_task.py` | 577 | False | `assert "ASSEMBLYAI_API_KEY" in failed_calls[0][1]` |
| `tests/worker/test_worker_tracing.py` | 257 | False | `Note: Celery's task_always_eager has no effect on celery_app.send_task() — only` |

Offending=true rows are credential-bearing strings (e.g., `ASSEMBLYAI_API_KEY=<value>`, `sk_<token>`, `Bearer <token>`) that fail A4. Offending=false rows are legitimate negations / regex mentions in policy or documentation context.

## Overall verdict

PASS — `OK_FINAL_ASSET_AUDIT`

