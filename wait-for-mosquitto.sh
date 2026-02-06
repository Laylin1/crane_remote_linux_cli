#!/bin/bash
set -e

host="$1"
port="$2"
shift 2
cmd="$@"

echo "Waiting for DNS for $host..."
until getent hosts "$host"; do
  sleep 1
done

echo "DNS resolved, waiting for $host:$port..."
until nc -z "$host" "$port"; do
  sleep 1
done

echo "$host:$port is available, starting app..."
exec "$@"
