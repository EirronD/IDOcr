# Use an official Python base image
FROM python:3.12

# Install Tesseract OCR and required libraries
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the Tesseract path explicitly
ENV TESSERACT_CMD=/usr/bin/tesseract

# Expose port
EXPOSE 8080

# Run the Flask app
CMD ["python", "idocr.py"]