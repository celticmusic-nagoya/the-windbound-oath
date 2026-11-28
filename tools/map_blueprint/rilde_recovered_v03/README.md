Recovered V03 baseline, NOT original, not adopted. Copy sources to a disposable scratch directory before running (scripts write beside themselves). Python 3.13.5, NumPy 2.3.5, trimesh 4.11.1, SciPy, Matplotlib. From tools/map_blueprint copy rilde_terrain_recovery/ and rilde_recovered_v03/ to scratch; copy recover_rilde_bridge_v03.py as scratch/rilde_recovery/recover_bridge.py. Run in scratch:

```sh
python rilde_terrain_recovery/recover_tiles.py
python rilde_terrain_recovery/recover_water.py
python rilde_recovery/recover_bridge.py
python rilde_terrain_recovery/assemble_recovery.py
python rilde_recovered_v03/restore_access.py
```

Expected reconstructed V03 SHA-256: 52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea. This differs from recorded original V03; do not replace it. Scripts reproduced the output byte-for-byte in a fresh directory. See regional receipt for per-stage limitations.
