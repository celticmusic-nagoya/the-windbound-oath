# TWO — private Drive reader, V18
Status: transfer adapter local exact-byte tests PASS. Live Actions-to-Drive auth NOT CONFIGURED.
Do not make any Drive file or folder publicly accessible. Do not store bearer URLs, tokens, service-account keys or private file IDs in Git. Director authorized Drive transfer, not a new cost or broad publication.

## One-time administrative configuration
Use an existing approved Google Cloud project. Enable Google Drive API, IAM, Security Token Service and IAM Service Account Credentials API. Do not provision billing resources or accept additional charges without director approval.
Create a dedicated service account with no broad Cloud project role; share ONLY the approved V15C input ZIP with that account as Viewer. Do not share the entire Drive or transfer folder. The service account email is an identifier, not a private key.
Configure Workload Identity Federation for GitHub OIDC issuer https://token.actions.githubusercontent.com with the standard subject mapping google.subject=assertion.sub and attribute.repository_id=assertion.repository_id. Restrict provider condition to the immutable repository ID 1408120919, approved workflow path and specific approved ref/event; verify actual OIDC claims before enabling. Grant the restricted workload principal roles/iam.workloadIdentityUser on this dedicated service account only. Do not use a downloadable long-lived key or domain-wide delegation.
Use a protected GitHub Actions environment to hold configuration (provider resource name, service account email, approved file ID); restrict approved branch/workflow and review the scoped execution. Do not inject the identity into existing non-Drive jobs. Separate explicit Drive read scope; no automatic retry of auth failure.
Reference: https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
Reference: https://github.com/google-github-actions/auth
Reference: https://developers.google.com/workspace/drive/api/guides/manage-downloads

## Integration contract (not yet executed)
On approved exact branch and scoped job only: permissions contents:read and id-token:write. Use reviewed, immutable-pinned google-github-actions/auth release, token_format:access_token, service_account, workload_identity_provider, access_token_scopes:https://www.googleapis.com/auth/drive.readonly, create_credentials_file:false, export_environment_variables:false. Pass output access token only as masked step env TWO_DRIVE_ACCESS_TOKEN; file ID as protected environment variable TWO_DRIVE_FILE_ID. Never echo either. Do not enable id-token permission globally.
Execute tools/map_blueprint/shared_materials_v01/drive_full_input_v18.py --out "$RUNNER_TEMP/forest_input.glb". It refuses missing auth, redirects, unexpected archive membership, oversized input, SHA mismatch and overwrite. No ZIP-provided scripts executed.
Only on success run existing official-checksum Blender 5.3 installer and reviewed import_v15c_full_native_v16.py on extracted GLB. Preserve native .blend, matched render PNGs and QA; do not declare adoption.
Current exact locks: ZIP 45872066 bytes SHA256 ab35c88f7cf53781edf0dd2aec2e75074adb7308abb5b0f40fc1e565c64a7dca; GLB 47420560 bytes SHA256 09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1. Offline adapter tested exact source extraction, missing credentials refusal and wrong input refusal. Authenticated runner request and full native import still NOT_RUN.
