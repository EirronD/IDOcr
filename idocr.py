import os
import re
import requests
import base64
import cv2
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO

# RapidAPI Configuration
RAPIDAPI_URL = "https://image-to-text30.p.rapidapi.com/api/rapidapi/image-to-text"
HEADERS = {
    "x-rapidapi-key": "c7e771d8e2msh0613f596acae43dp135786jsnd3953cf0b167",
    "x-rapidapi-host": "image-to-text30.p.rapidapi.com"
}

# Regex patterns
name_pattern = r"\b([A-Z]+(?:\s[A-Z]+)*),\s([A-Z]+(?:\s[A-Z]+)*)\b"
sex_pattern = r"\b[M|F]\b"
birthday_pattern = r"\b\d{4}/\d{2}/\d{2}\b"
address_pattern = r"([A-Z0-9\s]+(?:\sLAGUNA|\sCITY|\sPROVINCE|\sSTREET|\sROAD))"
id_pattern = r"(?:[A-Z]|\d)\d{2}-\d{2}-\d{6}"

app = Flask(__name__)


@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        if 'image' not in data:
            return jsonify({"error": "No image data found"}), 400

        # Decode base64 image
        image_data = base64.b64decode(data['image'])
        image = Image.open(BytesIO(image_data))

        # Convert image to bytes for API request
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        image_bytes = buffered.getvalue()

        # Send image to RapidAPI OCR
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        response = requests.post(RAPIDAPI_URL, files=files, headers=HEADERS)

        if response.status_code != 200:
            return jsonify({"error": "OCR API failed", "details": response.text}), response.status_code

        extracted_text = response.json().get("text", "")
        print("Extracted Text:\n", extracted_text)

        # Extract relevant fields
        name_match = re.search(name_pattern, extracted_text)
        address_match = re.search(address_pattern, extracted_text)
        id_match = re.search(id_pattern, extracted_text)
        sex_match = re.search(sex_pattern, extracted_text)
        birthday_match = re.search(birthday_pattern, extracted_text)

        # Fix ID format
        id_corrected = None
        if id_match:
            id_number = id_match.group(0)
            id_corrected = "D" + \
                id_number[1:] if id_number[0] != "D" else id_number

        # JSON response
        response_data = {
            "name": name_match.group(0) if name_match else None,
            "address": address_match.group(0) if address_match else None,
            "id_number": id_corrected,
            "nationality": "PHL",
            "sex": sex_match.group(0) if sex_match else None,
            "birthday": birthday_match.group(0) if birthday_match else None,
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
