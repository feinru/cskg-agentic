#!/bin/bash
# The script is not intended to be run directly, use "docker compose up --build" instead

set -e

echo "1. Running Fetcher Agent..."
python agents/fetcher/main.py

echo "2. Running Parser Agent..."
python agents/parser/main.py

echo "3. Running Linking Agent..."
python agents/linking/main.py

echo "4. Running Validation Agent..."
python agents/validation/main.py

echo "5. Copying TTL files to toload directory..."
mkdir -p sparql/data
# find all ttl files except those in venv or already in data, and copy them
find . -name "*.ttl" -not -path "*/venv/*" -not -path "*/sparql/data/*" -exec cp {} sparql/data/ \;

echo "6. Loading data into SPARQL Endpoint..."
# Wait for Virtuoso to be ready by pinging port 8890
echo "Waiting for Virtuoso to be ready on $VIRTUOSO_HOST:8890..."
until curl -s http://$VIRTUOSO_HOST:8890 > /dev/null; do
  echo "Virtuoso not ready yet, sleeping 5 seconds..."
  sleep 5
done

# Give Virtuoso a little extra time to fully initialize ISQL port 1111
echo "Virtuoso HTTP is up. Waiting 10s for ISQL port to settle..."
sleep 10

python sparql/load.py

echo "CSKG Pipeline completed successfully!"

# Keep container alive so it doesn't immediately exit when using docker compose up
tail -f /dev/null
