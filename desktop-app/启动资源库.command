#!/bin/zsh
cd "${0:A:h}"
python3 server.py &
library_pid=$!
trap 'kill "$library_pid" 2>/dev/null' EXIT INT TERM
sleep 1
open "http://127.0.0.1:8765"
wait "$library_pid"
