#!/bin/bash
# This script is a no-op placeholder; actual replica init happens
# in the docker-compose entrypoint override (pg_basebackup).
echo "Replica data directory initialised via pg_basebackup."
