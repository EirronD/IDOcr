import re
import cv2
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import os
import base64
from io import BytesIO

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

app = Flask(__name__)

name_pattern = r"([A-Z]+(?:\s[A-Z]+)*,\s[A-Z]+(?:\s[A-Z]+)?)"
nationality_pattern = r"\b[A-Z]{3}\b"
sex_pattern = r"\b[M|F]\b"
birthday_pattern = r"\b\d{4}[/\-]\d{2}[/\-]\d{2}\b"
# address_pattern = r"([A-Z]+(?:\s[A-Z]+)*,\s*[A-Z]+(?:\s[A-Z]+)*,\s*[A-Z]+)"
address_pattern = r"([A-Z\s]+(?:,\s*[A-Z\s]+)*)"
id_pattern = r"(?:D|\d)\d{2}-\d{2}-\d{6}"
dob_pattern = r"([A-Z]{3})\s([A-Z])\s(\d{4}/\d{2}/\d{2})"


@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({"error": "No image data found"}), 400

    try:
        image_data = base64.b64decode(data['image'])
        image = Image.open(BytesIO(image_data))
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        cv2.imwrite("debug_image.jpg", image)

        extracted_text = pytesseract.image_to_string(
            image, config="--psm 6 -l eng")

        print(extracted_text)

        name_match = re.search(name_pattern, extracted_text)
        address_match = re.search(address_pattern, extracted_text)
        id_match = re.search(id_pattern, extracted_text)

        nationality_match = re.search(nationality_pattern, extracted_text)

        sex_match = re.search(sex_pattern, extracted_text)
        birthday_match = re.search(birthday_pattern, extracted_text)

        id_corrected = None

        if id_match:
            id_number = id_match.group(0)
            id_corrected = "D" + \
                id_number[1:] if id_number[0] != "D" else id_number

        response_data = {
            "name": name_match.group(0) if name_match else None,
            "address": address_match.group(0) if address_match else None,
            "id_number": id_corrected,
            "nationality": nationality_match.group(0) if nationality_match else None,
            "sex": sex_match.group(0) if sex_match else None,
            "birthday": birthday_match.group(0) if birthday_match else None,
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
