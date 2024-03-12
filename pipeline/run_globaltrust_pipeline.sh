#!/bin/bash

while getopts w:o:v: flag
do
    case "${flag}" in
        o) OUT_DIR=${OPTARG};;
        w) WORK_DIR=${OPTARG};;
        v) VENV=${OPTARG};;
    esac
done

if [ -z "$OUT_DIR" ] || [ -z "$WORK_DIR" ] || [ -z "$VENV" ]; then
  echo "Usage:   $0 -w [work_dir] -o [out_dir] -v [venv]"
  echo ""
  echo "Example: $0 -w . -o /tmp -v /home/ubuntu/venvs/fc-graph-env3/"
  echo ""
  echo "Params:"
  echo "  [work_dir]  The working directory to read .env file and execute scripts from."
  echo "  [out_dir] The output directory to write the graph file."
  echo "  [venv] The path where a python3 virtualenv has been created."
  echo ""
  exit
fi

source $WORK_DIR/.env

DB_HOST=${DB_HOST:-127.0.0.1}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-replicator}
DB_NAME=${DB_NAME:-replicator}
DB_PASSWORD=${DB_PASSWORD:-password} # psql requires PGPASSWORD to be set
DB_TEMP_LOCALTRUST=${DB_TEMP_LOCALTRUST:-tmp_lt}
DB_LOCALTRUST=${DB_LOCALTRUST}
DB_TEMP_GLOBALTRUST=${DB_TEMP_GLOBALTRUST:-tmp_gt}
DB_GLOBALTRUST=${DB_GLOBALTRUST}

# set -x
set -e
set -o pipefail

if hash psql 2>/dev/null; then
  echo "OK, you have psql in the path. We’ll use that."
  PSQL=psql
else
  echo "You don't have psql is the path. Let's try /usr/bin"
  hash /usr/bin/psql
  PSQL=/usr/bin/psql
fi

function log() {
  echo "`date` - $1"
}

source $VENV/bin/activate
pip install -r requirements.txt
python3 -m globaltrust.gen_globaltrust
deactivate

# NOTE: We could have replaced localtrust and upserted into globaltrust in python but ..
# .. separating out like this helps us run steps in isolation. 
# For example, we can comment out the below code and ..
# .. experiment with the python code (weights for example) without worrying about affecting prod.
log "Replacing $DB_LOCALTRUST"
PGPASSWORD=$DB_PASSWORD \
$PSQL -t -A -F',' -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
  -c "DROP TABLE $DB_LOCALTRUST; ALTER TABLE $DB_TEMP_LOCALTRUST RENAME TO $DB_LOCALTRUST;"

log "Upserting $DB_GLOBALTRUST "
PGPASSWORD=$DB_PASSWORD \
$PSQL -t -A -F',' -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
  -c "WITH deletions AS (
   DELETE FROM $DB_GLOBALTRUST WHERE date=(SELECT max(date) FROM $DB_TEMP_GLOBALTRUST)
)
INSERT INTO $DB_GLOBALTRUST SELECT * FROM $DB_TEMP_GLOBALTRUST;
DROP TABLE $DB_TEMP_GLOBALTRUST;"
