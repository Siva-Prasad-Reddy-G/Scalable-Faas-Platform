FROM python:3.9-slim

RUN mkdir /app
# Set the working directory in the container
WORKDIR /app

ADD . /app/
# Copy the function code into the container
COPY function.py .

# Install any dependencies
RUN pip install -r requirements.txt

EXPOSE 5000
# Define the command to run the function
CMD ["python", "/app/function.py"]

