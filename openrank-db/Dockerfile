FROM postgres:16-alpine

# Install necessary packages
RUN apk --no-cache add bash sudo

# Copy the custom PostgreSQL configuration file
COPY ./config/postgresql.conf /etc/postgresql/postgresql.conf
COPY ./config/pg_hba.conf /etc/postgresql/pg_hba.conf

# # Copy initialization scripts
# COPY ./scripts /docker-entrypoint-initdb.d/

# # Ensure scripts are executable
# RUN chmod +x /docker-entrypoint-initdb.d/*.sh

# Copy entrypoint script to handle the custom configuration
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Set permissions for the entrypoint script
RUN chmod +x /usr/local/bin/entrypoint.sh

# Use the custom entrypoint script
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["postgres"]
