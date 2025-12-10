FROM ubuntu:22.04
RUN --mount=type=secret,id=mysecretid \
    ls /run/secrets && \
    cat /run/secrets/mysecretid
