# Use slim buster images
FROM python:3.14.0a6-slim-bookworm

# Make a working directory
RUN mkdir /app
WORKDIR /app

# First, copy the requirements.txt only as it helps with caching
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

# Copy the source code
COPY . /app

# Turn off debugging in production
ENV FLASK_DEBUG 0

# Set entrypoint
ENV FLASK_APP flask_run.py
ENV FLASK_RUN_HOST 0.0.0.0
EXPOSE 8000

# Run Flask command
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "--url-scheme=https", "--call", "lostify:create_app"]