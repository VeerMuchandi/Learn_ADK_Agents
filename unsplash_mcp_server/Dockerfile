# check=skip=LegacyKeyValueFormat
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that the Flask app will listen on
# Cloud Run automatically sets the PORT environment variable.
# Your app should listen on 0.0.0.0 and the port specified by this variable.
ENV PORT 8080

# Run the application
CMD ["python", "app.py"]
