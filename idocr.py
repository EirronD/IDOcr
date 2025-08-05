import os
import re
import requests
import base64
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
id_pattern = r"(?:[A-Z]|\d)\d{2}-\d{2}-\d{6}"

app = Flask(__name__)

def extract_address(text, doc_index):
    # Address patterns
    patterns = [
        re.compile(r"Address\s*\n+\s*([\d\w\s,.()'\-]+?LAGUNA(?:,\s*\d{4})?)", re.IGNORECASE),
        re.compile(r"(?:(?<![\d.]))((?:\d+(?:\s*,\s*)?)?[\w\s,.()'\-]+?LAGUNA(?:,\s*\d{4})?)", re.IGNORECASE)
    ]
    
    for pattern in patterns:
        matches = pattern.findall(text)
        if matches:
            clean_matches = []
            for match in matches:
                clean_match = match.strip()
                
                # Remove weight/height patterns
                clean_match = re.sub(r'\b\d+\s*AIGN OFFIEL\b', '', clean_match, flags=re.IGNORECASE)  # Custom fix for the specific issue
                clean_match = re.sub(r'Weight\s*\(kg\)\s*Height\s*\(m\)\s*\d+\s*\d+\.\d+', '', clean_match, flags=re.IGNORECASE)
                
                # Remove standalone numbers that don't fit an address format
                clean_match = re.sub(r'^\s*\d+\s+(?=\D)', '', clean_match)
                
                # Normalize spaces
                clean_match = re.sub(r'\s+', ' ', clean_match).strip()

                if len(clean_match.split()) > 2:  # Ensuring it's a valid address
                    clean_matches.append(clean_match)
            
            return clean_matches
    
    return []

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

        addresses = extract_address(extracted_text, doc_index=0)

        # Extract relevant fields
        name_match = re.search(name_pattern, extracted_text)
        id_match = re.search(id_pattern, extracted_text)
        sex_match = re.search(sex_pattern, extracted_text)
        birthday_match = re.search(birthday_pattern, extracted_text)

        # Fix ID format
        id_corrected = None
        if id_match:
            id_number = id_match.group(0)
            id_corrected = "D" + id_number[1:] if id_number[0] != "D" else id_number

        # JSON response
        response_data = {
            "name": name_match.group(0) if name_match else None,
            "address": addresses[0] if addresses else None,  # Assuming we want first address
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
