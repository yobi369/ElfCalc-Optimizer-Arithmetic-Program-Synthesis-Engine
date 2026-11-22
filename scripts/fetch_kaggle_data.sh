#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT}/data"
CACHE_DIR="${DATA_DIR}/kaggle-download"
UNPACK_DIR="${CACHE_DIR}/unpacked"
mkdir -p "${CACHE_DIR}" "${UNPACK_DIR}"

if ! command -v kaggle >/dev/null 2>&1; then
  echo "Kaggle CLI is not installed. Install it with: python -m pip install kaggle" >&2
  exit 2
fi

if [[ ! -f "${HOME}/.kaggle/kaggle.json" && -z "${KAGGLE_API_TOKEN:-}" ]]; then
  echo "Kaggle authentication is missing." >&2
  echo "Configure ~/.kaggle/kaggle.json or set KAGGLE_API_TOKEN, then accept the Santa 2026 competition rules." >&2
  exit 2
fi

echo "Downloading Santa 2026 competition files from Kaggle..."
kaggle competitions download -c santa-2026 -p "${CACHE_DIR}"

shopt -s nullglob
archives=("${CACHE_DIR}"/*.zip)
if (( ${#archives[@]} == 0 )); then
  echo "Kaggle CLI did not produce a ZIP archive in ${CACHE_DIR}" >&2
  exit 3
fi

for archive in "${archives[@]}"; do
  unzip -o "${archive}" -d "${UNPACK_DIR}" >/dev/null
done

for filename in puzzles.csv sample_submission.csv practice_puzzles.csv; do
  source_file="$(find "${UNPACK_DIR}" -type f -name "${filename}" -print -quit)"
  if [[ -n "${source_file}" ]]; then
    cp "${source_file}" "${DATA_DIR}/${filename}"
    echo "Available locally: data/${filename}"
  elif [[ "${filename}" == "practice_puzzles.csv" ]]; then
    echo "Not included in the competition download: ${filename} (optional practice file)." >&2
  else
    echo "Required file missing from Kaggle archive: ${filename}" >&2
    exit 4
  fi
done

echo
echo "Dataset files are stored under data/ (git-ignored; not committed)."
echo "Verify them with:"
echo "  sha256sum data/*.csv"
