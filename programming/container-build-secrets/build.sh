#!/usr/bin/env bash
: ${BUILDER:=${1:-docker}}  # podman, buildah
$BUILDER build \
    --secret "id=mysecretid,src=$PWD/mysecret" \
    .
