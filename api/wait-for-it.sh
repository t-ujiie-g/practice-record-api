#!/bin/bash
# wait-for-it.sh
# https://github.com/vishnubob/wait-for-it

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until nc -z "$host" "$port"; do
  >&2 echo "$host:$port に接続できません - 待機中"
  sleep 1
done

>&2 echo "$host:$port に接続できました"
exec $cmd