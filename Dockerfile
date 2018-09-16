from python:3.7.0-alpine3.7

RUN apk update
RUN apk add --no-cache yasm && apk add --no-cache ffmpeg 
RUN apk add python3-dev build-base linux-headers pcre-dev 
RUN pip install uwsgi requests
RUN adduser -D -g '' uwsgi

add . /work
WORKDIR /work
run chown -R uwsgi:uwsgi /work

USER uwsgi
EXPOSE 8080

CMD ["uwsgi", "--ini", "uwsgi.ini"]

