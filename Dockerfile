FROM ubuntu:latest
LABEL authors="swill"

ENTRYPOINT ["top", "-b"]