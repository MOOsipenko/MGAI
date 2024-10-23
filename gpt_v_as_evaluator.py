import base64
import json
import numpy as np
import re
import argparse
from groq import Groq
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()

# Initialize the Groq client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# TODO : Path to your image
image_path_1 = "FIRST_IMAGE_PATH.png"
image_path_2 = "SECOND_IMAGE_PATH.png"

# TODO : User preference text
user_preference = "USER_PREFERENCE_TEXT"

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Example grading structure
example_json = """
{
  "realism_and_3d_geometric_consistency": {
    "grade": 8,
    "comment": "The renders appear to have appropriate 3D geometry and lighting that is fairly consistent with real-world expectations. The proportions and perspective look realistic."
  },
  "functionality_and_activity_based_alignment": {
    "grade": 7,
    "comment": "The room includes a workspace, sleeping area, and living area as per the user preference. The L-shaped couch facing the bed partially meets the requirement for watching TV comfortably. However, there does not appear to be a TV depicted in the render, so it's not entirely clear if the functionality for TV watching is fully supported."
  },
  "layout_and_furniture": {
    "grade": 7,
    "comment": "The room has a bed that’s not centered and with space at the foot, and a large desk with a chair. However, it's unclear if the height of the bed meets the user's preference, and the layout does not clearly show the full-length mirror in relation to the wardrobe, so its placement in accordance to user preferences is uncertain."
  },
  "color_scheme_and_material_choices": {
    "grade": 9,
    "comment": "The room adheres to a light color scheme with blue and white tones as preferred by the user, without a nautical feel. The bed and other furniture choices are aligned with the color scheme specified."
  },
  "overall_aesthetic_and_atmosphere": {
    "grade": 8,
    "comment": "The room's general aesthetic is bright, clean, and relatively minimalistic, which could align with the user's preference for a light color scheme and a modern look. The chandelier is present as opposed to bright, hospital-like lighting."
  }
}
"""

# Encode images as base64
base64_image_1 = encode_image(image_path_1)
base64_image_2 = encode_image(image_path_2)

# Define the payload for the Groq-based Llama model
payload = {
    "model": "llama-3.2-11b-vision-preview",  # Using Groq's Vision model
    "messages": [
        {
            "role": "user",
            "content": f"""
            Give a grade from 1 to 10 or unknown to the following room renders based on how well they correspond together to the user preference (in triple backquotes) in the following aspects: 
            - Realism and 3D Geometric Consistency
            - Functionality and Activity-based Alignment
            - Layout and Furniture  
            - Color Scheme and Material Choices
            - Overall Aesthetic and Atmosphere
            User Preference:
            ```{user_preference}```
            Return the results in the following JSON format:
            ```json
            {example_json}
            ```
            """
        },
        {
            "role": "image",
            "image_data": f"data:image/jpeg;base64,{base64_image_1}"
        },
        {
            "role": "image",
            "image_data": f"data:image/jpeg;base64,{base64_image_2}"
        }
    ],
    "max_tokens": 1024
}

# Function to send a request to the Groq model
def send_request(payload):
    response = client.chat_completions(payload)
    return response

# Prepare grades dictionary
grades = {
    "realism_and_3d_geometric_consistency": [],
    "functionality_and_activity_based_alignment": [],
    "layout_and_furniture": [],
    "color_scheme_and_material_choices": [],
    "overall_aesthetic_and_atmosphere": []
}

# Perform multiple evaluation runs (e.g., 3 times for better grading analysis)
for _ in range(3):
    response = send_request(payload)
    grading_str = response["choices"][0]["message"]["content"]
    
    # Extract the JSON from the response
    pattern = r'```json(.*?)```'
    matches = re.findall(pattern, grading_str, re.DOTALL)
    json_content = matches[0].strip() if matches else None
    grading = json.loads(json_content) if json_content else json.loads(grading_str)
    
    for key in grades:
        grades[key].append(grading[key]["grade"])

# Calculate the mean and standard deviation of the grades
for key in grades:
    grades[key] = {
        "mean": round(sum(grades[key]) / len(grades[key]), 2),
        "std": round(np.std(grades[key]), 2)
    }

# Save the grades to a JSON file
with open(f"{'_'.join(image_path_1.split('_')[:-1])}_grades.json", "w") as f:
    json.dump(grades, f)
