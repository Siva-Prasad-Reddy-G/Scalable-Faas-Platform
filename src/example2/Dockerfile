FROM python:3.9-slim

RUN apt-get update && apt-get install -y procps
RUN apt install -y stress-ng

RUN mkdir /app
# Set the working directory in the container
WORKDIR /app

ADD . /app/
# Copy the function code into the container
COPY function.py .

# Install any dependencies
RUN pip install -r requirements.txt
RUN pip install prometheus_client
RUN pip install psutil

EXPOSE 8000
# Define the command to run the function
CMD ["python", "/app/function.py"]

