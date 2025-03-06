/app/Dockerfile
#Use an official Python runtime as a parent image
FROM python:3.9-slim

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
COPY ./entrypoint.sh .

#Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

#Expose the port FastAPI will run on
EXPOSE 8000

#Set the PYTHONPATH to include the /app directory
ENV PYTHONPATH=/app

#Add healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

#Use our custom entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]