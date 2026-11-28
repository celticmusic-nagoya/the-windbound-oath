# W120: bounded visibility-only correction, called by the exact pinned W110 adapter.
# No guide geometry mutation or relaxed tolerance. All screenshots stay in private evidence.
eyes W110-before-brush 5 0
ready=W110-before-brush
hidden=0
if "$py" tools/w110_camera_register.py support "$anchor" evidence/W110-before-brush-rows.json "$registration" "$anchor" "$design" evidence/W110-fit.json 2>evidence/W110-fit-error.txt; then
  echo BASE_GUIDE_FIT_PASS > evidence/W110-visibility-status.txt
else
  # Only the exact observed W118 error can trigger a visibility change.
  grep -Fxq 'ValueError: F06 unsupported at scale-adjusted tolerance' evidence/W110-fit-error.txt
  test "$(tail -n 1 evidence/W110-fit-error.txt)" = 'ValueError: F06 unsupported at scale-adjusted tolerance'
  # The five eye icons and target group are verified immediately before the single click.
  check_group W110-before-brush >/dev/null
  "$gui" click 0.26953125 0.61848958
  "$gui" move 0.70 0.10
  sleep 2
  capture_state W110-isolated
  check_group W110-isolated >/dev/null
  eyes W110-isolated 5 4
  "$py" tools/w109_visibility.py change evidence/W110-before-brush.png evidence/W110-isolated.png evidence/W110-isolated-change.json
  # Use the immutable W108 reference, not the previous transformed registration.
  "$py" tools/w110_camera_register.py register "$eye_reference" evidence/W110-isolated.png "$fixture/W108-face-registration.json" evidence/W110-isolated-registration.json
  "$py" tools/w110_camera_register.py support evidence/W110-isolated.png evidence/W110-isolated-rows.json evidence/W110-isolated-registration.json evidence/W110-isolated.png "$design" evidence/W110-fit.json
  # Original stroke guard and original save/reopen code remain in force.
  registration=evidence/W110-isolated-registration.json
  anchor=evidence/W110-isolated.png
  # The original worker uses the before-brush row path for its stroke guard.
  # Keep that original row receipt intact; route only the stroke call to the fresh row.
  ready=W110-isolated
  hidden=4
  echo ISOLATED_GUIDE_FIT_PASS > evidence/W110-visibility-status.txt
fi
