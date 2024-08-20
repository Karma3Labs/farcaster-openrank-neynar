DATA_DIR=/data
cd $DATA_DIR
git clone https://github.com/Karma3Labs/farcaster-openrank-neynar

# Generate a random password
NEW_RANDOM_PASSWORD=$(openssl rand --hex 16)

#############################
# Setup .env.docker file
#############################
cat << EOF | tee ${DATA_DIR}/farcaster-openrank-neynar/serve/.env.docker
DB_USERNAME=postgres
DB_PASSWORD=${NEW_RANDOM_PASSWORD}
DB_NAME=farcaster
DB_PORT=5432
DB_HOST=postgres
POSTGRES_POOL_SIZE=5
POSTGRES_ECHO=false
POSTGRES_TIMEOUT_SECS=60

PLGRAPH_PATHPREFIX=/tmp/personal_graph

SWAGGER_BASE_URL="https://graph.cast.k3l.io"
EOF

# See what the config looks like
cat /data/farcaster-openrank-neynar/serve/.env.docker

# The docker-compose.yml has the container's /tmp mapped to /home/ubuntu/serve_files,
# either change the docker-compose file or do this (preferably the latter)
ln -s /home/ubuntu/serve_files ${DATA_DIR}/serve_files