DATA_DIR=/data
# change the permission of data directory
sudo chown -R ubuntu:ubuntu $DATA_DIR
cd ${DATA_DIR}
mkdir -p ${DATA_DIR}/serve_files_wip
cd ${DATA_DIR}/serve_files_wip
wget -P ${DATA_DIR}/serve_files_wip -O personal_graph.parquet --content-disposition https://k3l-openrank-farcaster.s3.amazonaws.com/personal_graph.parquet
cd ${DATA_DIR}
mkdir -p ${DATA_DIR}/serve_files
mv ${DATA_DIR}/serve_files_wip/personal_graph.parquet ${DATA_DIR}/serve_files/
touch ${DATA_DIR}/serve_files/personal_graph_SUCCESS