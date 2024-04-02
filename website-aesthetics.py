import os
import requests
from bs4 import BeautifulSoup
from collections import Counter
import cv2
import numpy as np
import io
from PIL import Image
import time

def is_clothing_image(image_url, alt_text):
    print(f"Alt text: {alt_text}")  # Print the alt text for each image
    # Placeholder for logic to determine if an image is a clothing image
    return True

def save_image(image_content, image_url, alt_text, output_dir, info_file):
    try:
        # Generate a file name from the image URL (or you can use a UUID or a counter for uniqueness)
        file_name = image_url.split('/')[-1].split("?")[0]  # Basic way to generate a file name
        if not file_name:  # In case the URL doesn't provide a useful name
            file_name = "image_{}.jpg".format(int(time.time()))  # Fallback file name
        
        # Check for valid image file extensions
        if not any(file_name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            file_name += '.jpg'  # Default to .jpg if the URL lacks an extension

        file_path = os.path.join(output_dir, file_name)
        
        # Open the image and save it
        image = Image.open(io.BytesIO(image_content))
        image.save(file_path)
        
        # Write the file name and alt text to the info file
        with open(info_file, 'a') as f:
            f.write(f"{file_name}, {alt_text}\n")

        print(f"Saved {file_name} with alt text: {alt_text}")
    except Exception as e:
        print(f"Error saving image {image_url}: {e}")

def analyze_image_colors(image_content):
    image = Image.open(io.BytesIO(image_content))
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    pixels = np.float32(image.reshape(-1, 3))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, palette = cv2.kmeans(pixels, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    dominant_color = palette[np.argmax(np.bincount(labels.flatten()))]
    return dominant_color

def analyze_colors(content):
    soup = BeautifulSoup(content, 'html.parser')
    image_tags = soup.find_all('img')
    colors = []

    for img in image_tags:
        src = img.get('src')
        alt_text = img.get('alt', '')  # Fetch the alt text
        if not src:
            continue

        # Use the alt text to determine if the image is related to clothing
        if is_clothing_image(src, alt_text):  # Pass the alt text to the function
            if src.startswith('http'):
                try:
                    response = requests.get(src, stream=True, timeout=5)
                    if response.status_code == 200:
                        image_content = response.content
                        dominant_color = analyze_image_colors(image_content)
                        colors.append(tuple(dominant_color))
                    else:
                        print(f"Skipping image, HTTP status code: {response.status_code}")
                except requests.RequestException as e:
                    print(f"Error fetching image {src}: {e}")
            elif src.startswith('data:image'):
                print("Skipping base64 encoded image")
            else:
                print(f"Skipping unsupported image URL format: {src}")

    color_counts = Counter(colors)
    most_common_colors = color_counts.most_common()
    return most_common_colors

def retrieve_website_content(url):
    try:
        response = requests.get(url, timeout=5)  # Added timeout
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve website content, HTTP status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error retrieving website: {e}")
        return None

def retrieve_website(url, timestamp):
    api_url = f"http://archive.org/wayback/available?url={url}&timestamp={timestamp}"
    try:
        response = requests.get(api_url, timeout=5)  # Added timeout
        if response.status_code == 200:
            data = response.json()
            if 'archived_snapshots' in data and 'closest' in data['archived_snapshots']:
                snapshot_url = data['archived_snapshots']['closest']['url']
                content = retrieve_website_content(snapshot_url)
                if content:
                    most_common_colors = analyze_colors(content)
                    for color, count in most_common_colors:
                        print(f"Color: {color}, Count: {count}")
                    return snapshot_url
        else:
            print(f"Failed to retrieve archive snapshot, HTTP status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error retrieving archive snapshot: {e}")
    return None

url = "https://www.nike.com"
for year in range(2020, 2024):
    timestamp = f"{year}0101"
    print(f"Processing {url} for year {year}...")
    snapshot_url = retrieve_website(url, timestamp)
    if snapshot_url:
        print(f"Website snapshot for {url} in {year}: {snapshot_url}")
    else:
        print(f"No website snapshot found for {url} in {year}")
    time.sleep(10)  # Rate limiting - sleep for 10 seconds between requests to avoid overwhelming the server

