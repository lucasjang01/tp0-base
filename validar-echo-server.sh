#!/bin/bash

MESSAGE="hello"
NETWORK="tp0_testing_net"
SERVER="server"
PORT="12345"

RESPONSE=$(docker run --rm --network "$NETWORK" busybox sh -c "echo '$MESSAGE' | nc '$SERVER' '$PORT'")

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
