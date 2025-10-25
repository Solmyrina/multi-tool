#!/bin/bash

# Create SSL directory if it doesn't exist
mkdir -p /home/one_control/docker-project/ssl

# Generate private key
openssl genrsa -out /home/one_control/docker-project/ssl/server.key 2048

# Generate certificate signing request
openssl req -new -key /home/one_control/docker-project/ssl/server.key \
    -out /home/one_control/docker-project/ssl/server.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=localhost"

# Generate self-signed certificate valid for 365 days
openssl x509 -req -days 365 \
    -in /home/one_control/docker-project/ssl/server.csr \
    -signkey /home/one_control/docker-project/ssl/server.key \
    -out /home/one_control/docker-project/ssl/server.crt \
    -extensions v3_req \
    -extfile <(cat <<EOF
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = 37.60.244.6
EOF
)

# Remove CSR file as it's no longer needed
rm /home/one_control/docker-project/ssl/server.csr

# Set appropriate permissions
chmod 600 /home/one_control/docker-project/ssl/server.key
chmod 644 /home/one_control/docker-project/ssl/server.crt

echo "SSL certificates generated successfully!"
echo "Certificate: /home/one_control/docker-project/ssl/server.crt"
echo "Private Key: /home/one_control/docker-project/ssl/server.key"