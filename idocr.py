import re
import cv2
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract

app = Flask(__name__)

# Define regex patterns
name_pattern = r"([A-Z]+,\s[A-Z]+\s[A-Z]+)"
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

    # Extract text from the image using pytesseract
    extracted_text = pytesseract.image_to_string(image)

    # Extract information using regex
    name_match = re.search(name_pattern, extracted_text)
    dob_match = re.search(dob_pattern, extracted_text)
    address_match = re.search(address_pattern, extracted_text)
    id_match = re.search(id_pattern, extracted_text)
    match = re.search(nationality_sex_birthday_pattern, extracted_text)

    # Correct the ID number by replacing the first '0' with 'D'
    id_corrected = re.sub(r"\b0(\d{2})\b", r"D\1", id_match.group(0)) if id_match else None

    # Construct response
    response_data = {
        "name": name_match.group(0) if name_match else None,
        "date_of_birth": f"{dob_match.group(1)} {dob_match.group(2)} {dob_match.group(3)}" if dob_match else None,
        "address": address_match.group(0) if address_match else None,
        "id_number": id_corrected,
        "nationality": match.group(1) if match else None,
        "sex": match.group(2) if match else None,
        "birthday": match.group(3) if match else None,
    }

    return jsonify(response_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
