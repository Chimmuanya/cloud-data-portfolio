#!/usr/bin/env bash
# scripts/create_diagram_entry.sh <project-folder> "<diagram-basename>"
# Creates diagram folder and placeholder drawio file and README entry
set -euo pipefail
PROJECT="${1:-}"
NAME="${2:-architecture}"
if [ -z "$PROJECT" ]; then
  echo "Usage: $0 <project-folder> <diagram-basename>"
  exit 1
fi

DIRO="${PROJECT}/diagrams"
EXPO="${DIRO}/exported"
mkdir -p "${DIRO}" "${EXPO}"

# Create canonical drawio placeholder (XML is valid drawio file header)
DRAWIO_FILE="${DIRO}/${NAME}.drawio"
if [ ! -f "${DRAWIO_FILE}" ]; then
  cat > "${DRAWIO_FILE}" <<XML
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net">
  <diagram name="${NAME}"> <!-- open in draw.io and edit -->
  </diagram>
</mxfile>
XML
  echo "Created ${DRAWIO_FILE}"
else
  echo "${DRAWIO_FILE} already exists"
fi

# Create exported README hint
cat > "${EXPO}/README.md" <<MD
Place PNG/SVG or pipeline-exported artifacts here when exporting from draw.io.
Naming convention:
  - ${NAME}_v001.png
  - ${NAME}_v002.png
Include a short caption file: ${NAME}_caption.md
MD

echo "Diagram placeholder and exported folder created."
