#!/usr/bin/env bash
# Install packages from requirements.txt one-by-one and log failures.
# Usage: ./scripts/install_requirements_safe.sh [requirements-file]

set -euo pipefail

REQ_FILE="${1:-requirements.txt}"
LOG="install_errors.log"

: > "$LOG"
echo "Installing packages from $REQ_FILE (one-by-one). Errors will be logged to $LOG"

while IFS= read -r line || [ -n "$line" ]; do
  # Strip comments and whitespace
  pkg="$(echo "$line" | sed -E 's/#.*$//' | xargs)"
  if [ -z "$pkg" ]; then
    continue
  fi

  echo "Installing: $pkg"
  if ! pip install --no-cache-dir "$pkg"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - FAILED: $pkg" >> "$LOG"
  fi
done < "$REQ_FILE"

if [ -s "$LOG" ]; then
  echo "Installation completed with some failures. See $LOG"
  exit 1
else
  echo "All packages installed successfully."
fi
