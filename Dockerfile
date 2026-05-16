FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx template (uses $PORT env var)
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy static site and PDFs
COPY index.html /usr/share/nginx/html/
COPY pictures.html /usr/share/nginx/html/
COPY changelog.html /usr/share/nginx/html/
COPY search.html /usr/share/nginx/html/
COPY search-index.json /usr/share/nginx/html/
COPY *.pdf /usr/share/nginx/html/
COPY pictures/ /usr/share/nginx/html/pictures/
COPY cheats/ /usr/share/nginx/html/cheats/
COPY diagrams/ /usr/share/nginx/html/diagrams/

# Ensure nginx can read the served files (host may have restrictive umask)
RUN chmod -R a+rX /usr/share/nginx/html

# Railway injects PORT; nginx entrypoint processes templates automatically
ENV PORT=9080
EXPOSE 9080

CMD ["/docker-entrypoint.sh", "nginx", "-g", "daemon off;"]
