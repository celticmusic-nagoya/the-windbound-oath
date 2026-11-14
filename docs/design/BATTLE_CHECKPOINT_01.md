# BATTLE-CHECKPOINT-01 (Draft / Not ready for CONTINUE)
- Approved UX: CONTINUE / LOAD / TITLE.
- A valid CONTINUE must restore the exact pre-battle field state, party HP/MP, inventory, equipment, flags, encounter position, and enemy trigger without modifying 20 numbered slots.
- Storage module: js/battle-checkpoint.js. It uses a distinct sessionStorage key; capture and inspect fail closed.
- NOT WIRED to battle entry: the current serialization omits live field/battle resource and encounter return context. Capturing it now would give an incorrect restoration. CONTINUE therefore remains disabled.
- LOAD opens the existing title slot picker after clean reload; TITLE returns to title.
- Next implementation: create a verified, versioned full pre-battle snapshot from live state; add an atomic restoration route and end-to-end browser tests for normal/solo/Raider and repeated defeat. Do not activate CONTINUE until all gates pass.
- G1 canonical settings protected; G2/G4 Android NOT RUN; G3 storage unit tests pending.
