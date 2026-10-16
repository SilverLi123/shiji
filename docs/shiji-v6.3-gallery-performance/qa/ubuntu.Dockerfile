FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates sqlite3 && rm -rf /var/lib/apt/lists/*
# Official Node distribution, SHA-256 verified by build_ubuntu.py. Test-only image.
COPY node-distribution/ /usr/local/
WORKDIR /work
