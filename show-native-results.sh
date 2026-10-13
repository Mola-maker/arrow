#!/bin/bash
set -euo pipefail
phase=${1:?before or after}
validation_dir=/home/omarchy/validation-arrow
rm -f "$validation_dir/view-ready-$phase"
printf 'Apache Arrow: Parquet metadata comparison %s\n' "${phase^^}"
printf 'Native Arch Linux / Omarchy; kernel %s\n' "$(uname -r)"
"$validation_dir/venv/bin/python" "$validation_dir/reproduce_arrow_metadata_none.py" \
  --output "$validation_dir/$phase.json" | tee "$validation_dir/$phase.log"
if [[ $phase == "after" ]]; then
  printf '\nSource metadata regression suite:\n'
  PATH="$validation_dir/bin:$PATH" PARQUET_TEST_DATA="$validation_dir/parquet-data" \
    "$validation_dir/venv/bin/python" -m pytest \
    "$validation_dir/venv/lib/python3.14/site-packages/pyarrow/tests/parquet/test_metadata.py" \
    -q --enable-s3 -rs | tee "$validation_dir/metadata-tests.log"
fi
printf '\nActual _parquet Cython extension compiled from source with g++\n'
touch "$validation_dir/view-ready-$phase"
read -rp 'Validation finished. Press Enter to close.'
