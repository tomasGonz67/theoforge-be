#Use an official Python runtime as a parent image
FROM python:3.9-slim

# Declare build-time args (they must be defined before they're used)
ARG POSTGRES_DB
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_PORT
ARG PGADMIN_DEFAULT_EMAIL
ARG PGADMIN_DEFAULT_PASSWORD
ARG PGADMIN_PORT
ARG NEO4J_USER
ARG NEO4J_PASSWORD
ARG NEO4J_HTTP_PORT
ARG NEO4J_BOLT_PORT
ARG DOCKER_IMAGE
ARG CONTAINER_NAME
ARG API_PORT
ARG DATABASE_URL
# Set runtime env vars based on those args
ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRES_PORT=${POSTGRES_PORT}
ENV PGADMIN_DEFAULT_EMAIL=${PGADMIN_DEFAULT_EMAIL}
ENV PGADMIN_DEFAULT_PASSWORD=${PGADMIN_DEFAULT_PASSWORD}
ENV PGADMIN_PORT=${PGADMIN_PORT}
ENV NEO4J_USER=${NEO4J_USER}
ENV NEO4J_PASSWORD=${NEO4J_PASSWORD}
ENV NEO4J_HTTP_PORT=${NEO4J_HTTP_PORT}
ENV NEO4J_BOLT_PORT=${NEO4J_BOLT_PORT}
ENV DOCKER_IMAGE=${DOCKER_IMAGE}
ENV CONTAINER_NAME=${CONTAINER_NAME}
ENV API_PORT=${API_PORT}
ENV DATABASE_URL=${DATABASE_URL}

#Set the working directory inside the container
WORKDIR /app

#Install curl for healthcheck and bash for entrypoint
RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

#Copy only the requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copy the application files
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini .
COPY ./entrypoint.sh /app/entrypoint.sh

#Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

#Expose the port FastAPI will run on
EXPOSE 8000

#Set the PYTHONPATH to include the /app directory
ENV PYTHONPATH=/app

#Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

RUN cat /app/entrypoint.sh

#Use our custom entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]