#!/bin/bash
set -e

# Directory where the data will be stored
DATA_DIR="/var/lib/postgresql/data"
CONF_DIR="/etc/postgresql"

# Ensure the PostgreSQL environment is ready for initialization
if [ ! -s "${DATA_DIR}/PG_VERSION" ]; then
    echo "Initializing PostgreSQL data directory..."
    # Initialize database directory
    su-exec postgres initdb -D ${DATA_DIR}

    # Copy the custom configuration file to the data directory
    echo "Copying custom postgresql.conf to ${DATA_DIR}..."
    cp $CONF_DIR/postgresql.conf ${DATA_DIR}/postgresql.conf
    cp $CONF_DIR/pg_hba.conf ${DATA_DIR}/pg_hba.conf
    chown postgres:postgres ${DATA_DIR}/postgresql.conf ${DATA_DIR}/pg_hba.conf
fi

# Run the default entrypoint script with any arguments
exec docker-entrypoint.sh "$@"
