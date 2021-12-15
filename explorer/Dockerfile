from golang:buster AS openfoodfacts-estimator-explorer

ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd -g $USER_GID gouser && \
    useradd -u $USER_UID -g gouser -m gouser && \
    mkdir -p /go/src/explorer && \
    mkdir -p /go/src/explorer/binary && \
    chown -R gouser:gouser /go && \
    chmod o-rwx -R /go

WORKDIR /go/src/explorer
COPY *.go *.mod *.sum ./
RUN go install -v explorer.go
USER gouser:gouser
ENTRYPOINT ["/go/bin/explorer"]
CMD []