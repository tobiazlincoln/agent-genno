FROM nginx:alpine
COPY hackathon/site/ /usr/share/nginx/html/
EXPOSE 80
