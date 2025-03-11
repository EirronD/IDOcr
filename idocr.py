import re
import cv2
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

app = Flask(__name__)

# Define regex patterns
name_pattern = r"([A-Z]+(?:\s[A-Z]+)*,\s[A-Z]+(?:\s[A-Z]+)?)"
nationality_sex_birthday_pattern = r"([A-Z]{3})\s([A-Z])\s(\d{4}/\d{2}/\d{2})"
address_pattern = r"(\d{4}\s[A-Z]+\s[A-Z]+\s[A-Z]+)"
id_pattern = r"(\d{3}-\d{2}-\d{6})"
dob_pattern = r"([A-Z]{3})\s([A-Z])\s(\d{4}/\d{2}/\d{2})"

import base64
from io import BytesIO

@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({"error": "No image data found"}), 400

    # Decode Base64 image
    image_data = base64.b64decode(data['image'])
    image = Image.open(BytesIO(image_data))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Extract text from the image using pytesseract
    extracted_text = pytesseract.image_to_string(thresh)

    # Extract information using regex
    name_match = re.search(name_pattern, extracted_text)
    dob_match = re.search(dob_pattern, extracted_text)
    address_match = re.search(address_pattern, extracted_text)
    id_match = re.search(id_pattern, extracted_text)
    match = re.search(nationality_sex_birthday_pattern, extracted_text)

    id_corrected = re.sub(r"\b0(\d{2})\b", r"D\1", id_match.group(0)) if id_match else None
    # Construct response
    response_data = {
        "name": name_match.group(0) if name_match else None,
        "address": address_match.group(0) if address_match else None,
        "id_number": id_corrected,
        "nationality": match.group(1) if match else None,
        "sex": match.group(2) if match else None,
        "birthday": match.group(3) if match else None,
    }

    return jsonify(response_data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

