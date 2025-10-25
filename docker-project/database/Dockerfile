FROM postgres:15

# Set environment variables
ENV POSTGRES_USER=root
ENV POSTGRES_PASSWORD=530NWC0Gm3pt4O
ENV POSTGRES_DB=webapp_db

# Copy initialization scripts
COPY init.sql /docker-entrypoint-initdb.d/

# Expose the PostgreSQL port
EXPOSE 5432