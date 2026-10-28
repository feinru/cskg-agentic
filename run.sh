#!/bin/bash
set -e

VIRTUOSO_HOST="${VIRTUOSO_HOST:-localhost}"

if [ -f ".venv/bin/python" ] && [ -z "$PYTHON" ]; then
  PYTHON=".venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "1. Running Fetcher Module..."
$PYTHON modules/fetcher/main.py

echo "2. Running Parser Module..."
$PYTHON modules/parser/main.py

echo "3. Running Linking Module..."
$PYTHON modules/linking/main.py

echo "4. Running Validation Module..."
$PYTHON modules/validation/main.py

echo "5. Copying TTL files to toload directory..."
mkdir -p sparql/data
cp modules/parser/output/*.ttl sparql/data/
cp modules/linking/output/*.ttl sparql/data/

echo "6. Loading data into SPARQL Endpoint..."
if ! curl -s -f "http://${VIRTUOSO_HOST}:8890/sparql" > /dev/null; then
  echo "Waiting for Virtuoso on ${VIRTUOSO_HOST}:8890..."
  until curl -s -f "http://${VIRTUOSO_HOST}:8890/sparql" > /dev/null; do
    sleep 2
  done
  sleep 3
fi

$PYTHON sparql/load.py

echo "CSKG Pipeline completed successfully!"
