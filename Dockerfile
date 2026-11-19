FROM nginx:alpine

COPY hackathon/site/ /usr/share/nginx/html/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Railway routes traffic to $PORT; nginx templates substitute it at startup
ENV PORT=8080
EXPOSE 8080
