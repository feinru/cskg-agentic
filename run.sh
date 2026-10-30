#!/bin/bash
set -e

VIRTUOSO_HOST="${VIRTUOSO_HOST:-localhost}"

if [ -f ".venv/bin/python" ] && [ -z "$PYTHON" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

STEP="${1:-all}"

run_fetch() {
  $PYTHON modules/fetcher/main.py
}

run_parse() {
  $PYTHON modules/parser/main.py
}

run_link() {
  $PYTHON modules/linking/main.py
}

run_validate() {
  $PYTHON modules/validation/main.py
}

run_load() {
  mkdir -p sparql/data sparql/data/ontology
  cp -u ontology/*.ttl sparql/data/ontology/ 2>/dev/null || cp ontology/*.ttl sparql/data/ontology/
  cp -u modules/parser/output/*.ttl sparql/data/ 2>/dev/null || cp modules/parser/output/*.ttl sparql/data/
  for f in modules/linking/output/*.ttl; do
    [ -e "$f" ] || continue
    filename=$(basename "$f")
    case "$filename" in
      *_to_*|*_simulated*) ;;
      *) cp -u "$f" sparql/data/ 2>/dev/null || cp "$f" sparql/data/ ;;
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
}

case "$STEP" in
  fetch)
    run_fetch
    ;;
  parse)
    run_parse
    ;;
  link)
    run_link
    ;;
  validate|validation)
    run_validate
    ;;
  load)
    run_load
    ;;
  all)
    run_fetch
    run_parse
    run_link
    run_validate
    run_load
    ;;
  *)
    echo "Unknown step: $STEP"
    echo "Usage: ./run.sh [all|fetch|parse|link|validate|load]"
    exit 1
    ;;
esac

echo ""
echo "Done successfully!"

