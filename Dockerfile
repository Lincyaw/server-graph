FROM openjdk:23-ea-17-jdk-slim-bookworm

# Install necessary packages
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv \
    graphviz

# Create and activate a virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy the app files
COPY app.py /app/app.py
COPY uploads /app/uploads
COPY plantuml.jar /app/plantuml.jar

# Set the working directory
WORKDIR /app

# Install Flask within the virtual environment
RUN pip install flask

# Expose the default Flask port
EXPOSE 5000

# Command to run the Flask app
CMD ["python3", "app.py"]
