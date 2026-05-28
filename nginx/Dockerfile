FROM nginx:1.25-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY conf.d/prod.conf /etc/nginx/conf.d/
EXPOSE 80