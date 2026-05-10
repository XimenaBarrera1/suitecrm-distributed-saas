FROM nginx:1.27-alpine

COPY proxy/nginx.conf /etc/nginx/nginx.conf
