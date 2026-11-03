# Publication verification

Main normal merge: `3d1794340feb7210f209ae4beea2dc879034e92f` (#122).
Parents: main22efe87 and independently reviewedb9e24e9. No force/admin/bypass.
#107/#112 already integrated via#123/#124. Main/source adoption bytes unchanged by tester.

Pages build **built**, exact mergecommit. TLS-verifying HTTPS fetched9 index/CSS/JS/manifest
files plus6 representative Aidan/soldier/goblin PNGs: all15 SHA-256 match main.
Initial build observation window expired whilebuilding; laterbuilt was observed,
not relabelled as an initialPASS. Both observation and finalproof retained.

Public-browser direct navigation **NOT_RUN / BLOCKED_ENV_CERT**:
Chromium lacks trust for this environment proxy's certificate. Both default and
explicit inherited-proxy attempts stopped at ERR_CERT_AUTHORITY_INVALID before
applicationboot. These are environmental failures, not a claimed UI PASS or
websitecertificate diagnosis. No gameplay publicbrowser checks were reached.

Automatic approval review rejected persistent globalNSS CA installation because
it would broaden browsertrust beyond the task. The rejected command did notrun;
no globaltrust change or TLSverification disablement was used. Safer verification:
normal TLS-enabled publiccontent hashes plus already-completed localbrowser QA
of byte-identical code/assets. Required PC/Android-emulated local QA is PASS;
physical Android and directpublicbrowser remain distinct NOT_RUN limitations.

Rollback ref: `rollback/before-dev-walk-motion-01-20261102-22efe87`, remotepeeled22efe87.
If necessary, `git revert -m 1 3d1794340feb7210f209ae4beea2dc879034e92f` reverses
only the DEVtestermerge, preserving prior soldier/Aidan integration.

This post-publication evidence is a branch-only append, not another productionchange.
