#!/bin/bash
set -e

VIRTUOSO_HOST="${VIRTUOSO_HOST:-localhost}"

if [ -f ".venv/bin/python" ] && [ -z "$PYTHON" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

$PYTHON modules/fetcher/main.py
$PYTHON modules/parser/main.py
$PYTHON modules/linking/main.py
$PYTHON modules/validation/main.py

mkdir -p sparql/data
cp modules/parser/output/*.ttl sparql/data/
for f in modules/linking/output/*.ttl; do
  [ -e "$f" ] || continue
  filename=$(basename "$f")
  case "$filename" in
    *_to_*|*_simulated*) ;;
    *) cp "$f" sparql/data/ ;;
  esac
done

if ! curl -s -f "http://${VIRTUOSO_HOST}:8890/sparql" > /dev/null; then
  echo ""
  echo "[SPARQL] Waiting for Virtuoso on ${VIRTUOSO_HOST}:8890..."
  until curl -s -f "http://${VIRTUOSO_HOST}:8890/sparql" > /dev/null; do
    sleep 2
  done
  sleep 3
fi

$PYTHON sparql/load.py

echo ""
echo "Done successfully!"

