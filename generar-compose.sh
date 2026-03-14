#!/bin/bash
# generar-compose.sh
# Uso: ./generar-compose.sh <archivo_salida> <num_clientes>
# Genera un archivo Docker Compose con la cantidad de clientes especificada.

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <output_file> <num_clients>"
    exit 1
fi

OUTPUT_FILE="$1"
NUM_CLIENTS="$2"

if ! [[ "$NUM_CLIENTS" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: num_clients must be a positive integer"
    exit 1
fi

python3 generar-compose.py "$OUTPUT_FILE" "$NUM_CLIENTS" 2>/dev/null
