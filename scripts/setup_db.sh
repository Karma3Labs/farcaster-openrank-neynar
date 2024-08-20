DATA_DIR=/data
mkdir -p ${DATA_DIR}/openrank-db/config

# Adding postgresql.conf
cat << EOF | tee ${DATA_DIR}/openrank-db/config/postgresql.conf
listen_addresses = '*'
max_connections = 20  # Increase based on expected workload
shared_buffers = 2GB  # Increase to fit higher RAM (25% of RAM)
work_mem = 128MB  # Same, can increase based on RAM available
maintenance_work_mem = 512MB  # Increase based on RAM available
dynamic_shared_memory_type = posix
wal_level = replica
max_replication_slots = 1
synchronous_commit = remote_apply
wal_log_hints = on
wal_compression = on
checkpoint_timeout = 15min  # Reduced to ensure more frequent checkpoints
max_wal_size = 4GB
min_wal_size = 80MB  # Same as before, consider lowering if needed
max_wal_senders = 2  # Reduced to lower the number of concurrent replication connections
wal_keep_size = 256MB
max_slot_wal_keep_size = 16GB
wal_sender_timeout = 5min
wal_receiver_timeout = 5min
random_page_cost = 1.1
effective_cache_size = 1GB
log_timezone = UTC
datestyle = 'iso, mdy'
timezone = UTC
lc_messages = 'en_US.utf8'
lc_monetary = 'en_US.utf8'
lc_numeric = 'en_US.utf8'
lc_time = 'en_US.utf8'
default_text_search_config = 'pg_catalog.english'
shared_preload_libraries = 'pg_stat_statements'
EOF


cat << EOF | tee ${DATA_DIR}/openrank-db/config/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     trust
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
host    all             all             172.0.0.1/8             trust
host    all             all             192.168.0.1/16          trust
# IPv6 local connections:
host    all             all             ::1/128                 trust
EOF