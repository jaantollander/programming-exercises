FROM golang:1.23.4-alpine3.21 AS builder
WORKDIR /opt/app
COPY ./app/main.go ./app/go.mod .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o main .

#FROM alpine:3.21
#RUN apk --no-cache add ca-certificates
#COPY --from=builder /opt/app .
#ENTRYPOINT ["/main"]

FROM scratch
COPY --from=builder /opt/app .
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs
ENTRYPOINT ["/main"]
