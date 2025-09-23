#!/usr/bin/env bash
docker rm api-bantay || true

# if apple m1 chip
if [[ `uname -m` == 'arm64' ]]; then
    docker build --platform linux/x86_64 -t api-bantay:latest .
else
    docker build -t api-bantay:latest .
fi
