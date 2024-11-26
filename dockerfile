# Use an official Python runtime as a base image
FROM python:3.12.4

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install dependencies globally
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose Redis ports
EXPOSE 6379  

# Default command to run your application
CMD ["python3", "MultipleVMSimple/VQE.py"]
