#!/bin/bash

# Set defaults
SERVER_HOST="${SERVER_HOST:=0.0.0.0}"
SERVER_PORT="${SERVER_PORT:=8080}"

# Switch the command
COMMAND=$1
shift
case "${COMMAND}" in
    "api")
        uvicorn server:api --host ${SERVER_HOST} --port ${SERVER_PORT} $@
    ;;
    "shell")
        /bin/bash
    ;;
    *)
        echo "Unrecognized command: '${COMMAND}'"
        exit 1
    ;;
esac