# Authorized supplemental evidence

The original REQA FAIL remains unchanged. These are new executions under the explicit director waiver.

Reconstruct the lossless full execution archive (all 4,641 original files including three complete native supplemental videos):

```sh
cat authorized-execution.tar.gz.part01 authorized-execution.tar.gz.part02 > authorized-execution.tar.gz
tar -xzf authorized-execution.tar.gz
```

`execution-index.json` records each original file SHA/size. Duplicate contents are stored as safe archive-internal tar hardlinks. The original full archive is 15,737,673 bytes. Parts are required because the upload connector limits individual JSON requests to 16 MiB.

`visual-selected.tar.gz` includes the independent visual report, exact seek times, reproduction script and native-pixel crop sheets for PC/portrait/landscape. Full unabridged source videos are in the lossless execution archive. Other derived overview/full-frame sheets were reviewed locally and can be reproduced; they are not claimed as individually committed.
