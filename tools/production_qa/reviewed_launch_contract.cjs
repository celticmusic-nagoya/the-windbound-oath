"use strict";
// Read-only selection and verification. Never submits requests or modifies refs.
const crypto = require("node:crypto");
const PATH = ".github/workflows/morwen-vroid-macos-probe.yml";
const ACTIVE = ["queued","in_progress","waiting","requested","pending"];
const DEPENDENCIES = [".github/workflows/morwen-request-launch.yml","tools/private-preservation/release_transport.py","tools/production_qa/capture_transfer_views.sh","tools/production_qa/import_vrm_transfer.py","tools/production_qa/install_blender_530.sh","tools/production_qa/morwen_transfer_claim.py","tools/production_qa/pack_transfer.py","tools/production_qa/preserve_blender_transfer.py","tools/production_qa/receive_morwen_transfer.py","tools/production_qa/render_transfer_views.py","tools/production_qa/restore_morwen_artifact_preflight.py","tools/production_qa/restore_morwen_preserved.py","tools/production_qa/reviewed_launch_contract.cjs","tools/production_qa/run_blender_transfer.sh","tools/production_qa/shared_asset_lease.py","tools/production_qa/shared_asset_reservation.py","tools/production_qa/transfer_private_release.py","tools/production_qa/verify_transfer_output.py","tools/production_qa/vrm_export_session.sh"];
function need(ok, message) { if (!ok) throw Error(message); }
function verifyContract(contract, blob, profile, asset, blobFor) {
  need(contract && contract.schema === "two-reviewed-launch-v1" &&
    contract.review_state === "REVIEWED_FOR_OWNER_LAUNCH", "launch contract not reviewed");
  need(asset === "MORWEN" && contract.asset_id === asset &&
    contract.worker_path === PATH, "launch contract scope");
  need(/^[0-9a-f]{40}$/.test(contract.worker_blob) && contract.worker_blob === blob, "worker review missing");
  need(/^[0-9a-f]{64}$/.test(contract.profile_sha256) &&
    crypto.createHash("sha256").update(profile).digest("hex") === contract.profile_sha256, "profile review missing");
  need(["private_release","actions_artifact"].includes(contract.restore_source), "restore source not reviewed");
  const deps=contract.dependency_blobs;
  need(deps && typeof deps==="object" && !Array.isArray(deps) && Object.keys(deps).length===DEPENDENCIES.length && typeof blobFor==="function", "dependency inventory");
  for (const path of DEPENDENCIES) need(/^[0-9a-f]{40}$/.test(deps[path]) && blobFor(path)===deps[path], "dependency review missing: "+path);
}
function selectPrior(list, detail, jobs, active) {
  need(list && Array.isArray(list.workflow_runs) && list.workflow_runs.length === 1, "missing latest prior run");
  const p = list.workflow_runs[0];
  need(p && detail && Number.isSafeInteger(p.id) && p.id > 0 && p.id === detail.id, "prior identity changed");
  for (const v of [p,detail]) {
    need(v.workflow_id === 424712879 && v.path === PATH && v.head_branch === "main" &&
      v.event === "workflow_dispatch" && v.repository?.id === 1408120919 &&
      v.head_repository?.id === 1408120919 && v.actor?.id === 41898282 &&
      v.actor?.login === "github-actions[bot]" && v.run_attempt === 1 &&
      /^[0-9a-f]{40}$/.test(v.head_sha) &&
      /^Morwen VRoid \/ vrm_export request:[1-9][0-9]{0,19}$/.test(v.display_title) &&
      v.status === "completed" && ["success","failure","cancelled","timed_out","startup_failure"].includes(v.conclusion),
      "prior run not qualified");
  }
  need(p.head_sha === detail.head_sha && p.display_title === detail.display_title && p.conclusion === detail.conclusion, "prior metadata changed");
  need(jobs && jobs.total_count === 4 && Array.isArray(jobs.jobs) && jobs.jobs.length === 4 &&
    new Set(jobs.jobs.map(j=>j.name)).size === 4 &&
    ["VRM export and private transfer (reopen)","matrix.lane","blender-transfer-protected","complete-morwen-transfer"].every(n=>jobs.jobs.some(j=>j.name===n)) &&
    jobs.jobs.every(j=>j.run_id===p.id && j.run_attempt===1 && j.status==="completed" && typeof j.conclusion==="string"),
    "prior jobs not terminated");
  need(active && ACTIVE.every(s=>active[s]?.total_count===0 &&
    Array.isArray(active[s]?.workflow_runs) && active[s].workflow_runs.length===0), "active or uncertain worker");
  return p.id;
}
module.exports={verifyContract,selectPrior,ACTIVE,PATH,DEPENDENCIES};
