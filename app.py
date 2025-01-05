from flask import Flask, render_template, request, jsonify
import cv2
import torch
import numpy as np
from PIL import Image
import os
import pandas as pd
from ultralytics import YOLO
import subprocess
import base64
from io import BytesIO
import tempfile

app = Flask(__name__)

# Path model
MODEL_PATH = './models/best.pt'

# Check ultralytics version
try:
    result = subprocess.run(['pip', 'show', 'ultralytics'], capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            ultralytics_version = line.split(": ")[1]
            print(f"Ultralytics version: {ultralytics_version}")
            break
    else:
        print("Ultralytics version not found.")
except Exception as e:
    print(f"Error checking ultralytics version: {e}")


# Load YOLOv11 model
def load_model():
    try:
        print(f"Loading model from: {MODEL_PATH}")
        model = YOLO(MODEL_PATH)
        model.eval()
        print("Model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

model = load_model()

# Preprocess image
def preprocess_image(image):
    # Ubah format gambar ke RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(f"Image shape (after BGR to RGB conversion): {image.shape}")

    # Resize gambar ke size yang diharapkan model, misalnya 640x640
    image = cv2.resize(image, (640, 640))
    print(f"Resized image shape: {image.shape}")

    # Normalisasi gambar (penting untuk YOLO)
    image = image / 255.0
    print(f"Processed image shape: {image.shape}")
    return image


# Detect objects
def detect_objects(image):
    if model is None:
        print("Model not loaded, cannot perform detection.")
        return None

    # Preprocess gambar
    image = preprocess_image(image)

    # Ubah gambar menjadi tensor
    image = np.transpose(image, (2, 0, 1))
    image = np.expand_dims(image, 0)
    image = torch.from_numpy(image).float()

    # lakukan inferensi
    with torch.no_grad():
        results = model(image)

    # DEBUG: Tambahkan print untuk cek type results
    print(f"Type of results: {type(results)}")

    # Adaptasi untuk output list
    if isinstance(results, list):
        # ambil deteksi pertama dari batch pertama
        result = results[0]

        # DEBUG: print type result untuk memastikan isinya
        print(f"Type of result[0] : {type(result)}")

        if result is None or result.boxes.data.shape[0] == 0:
            print("No detections found.")
            return pd.DataFrame()  # mengembalikan DataFrame kosong

        # ubah menjadi DataFrame dari deteksi
        detections = result.boxes.data.cpu().numpy()
        print(f"Type of detections (before DataFrame): {type(detections)}")
        # pastikan detections memiliki nilai dan tidak empty
        if detections is None or len(detections) == 0:
           print("No detections found.")
           return pd.DataFrame() # mengembalikan DataFrame kosong
        
        # Ubah deteksi menjadi DataFrame pandas
        column_names = ['xmin', 'ymin', 'xmax', 'ymax', 'confidence', 'class_id']
        try:
            detections = pd.DataFrame(detections, columns=column_names)
        except Exception as e:
           print(f"Error during DataFrame construction: {e}")
           return None
        print(f"Type of detections (after conversion): {type(detections)}")
        
        print(f"Detections (before filtering):\n{detections}")
        print(f"Detections (after filtering):\n{detections}")
        
        return detections
    else:
        print("Error: Output model is not a list")
        return None


# Count objects
def count_objects(results):
    if results is None or results.empty:
        print("No results passed to count_objects.")
        return 0

    count = len(results)
    print(f"Object count: {count}")
    return count


# Function to extract frames and get average detections from video
def process_video(video_file):
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        print("Error opening video file.")
        return None

    frame_counts = []
    all_detections = []
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Use a temporary file path to avoid conflicts (use tempfile module)
    temp_output_video_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
   
   # Ensure that the codec is set correctly, use avc1 (H264) for better browser compatability
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(temp_output_video_path, fourcc, fps, (frame_width, frame_height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        original_frame = frame.copy()
        detections = detect_objects(frame)
        if detections is not None and not detections.empty:
            frame_counts.append(len(detections))
            all_detections.append(detections.to_dict('records'))

             # Calculate the scale factors for bounding boxes
            scale_x = original_frame.shape[1] / 640
            scale_y = original_frame.shape[0] / 640
            
            # Draw bounding boxes
            for _, detection in detections.iterrows():
                xmin = int(detection['xmin'] * scale_x)
                ymin = int(detection['ymin'] * scale_y)
                xmax = int(detection['xmax'] * scale_x)
                ymax = int(detection['ymax'] * scale_y)
                cv2.rectangle(original_frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Green bounding box on the original frame
        
        out.write(original_frame)

    cap.release()
    out.release()

    if len(frame_counts) > 0:
        average_count = np.mean(frame_counts)
        average_count = round(average_count) # dibulatkan
        print(f"Average Object Count: {average_count}")
        
        # Convert video to base64
        try:
            with open(temp_output_video_path, 'rb') as video_file:
                video_data = base64.b64encode(video_file.read()).decode('utf-8')
            os.remove(temp_output_video_path)  # Remove the temporary file

            return average_count, video_data
        except Exception as e:
            print(f"Error converting video to base64: {e}")
            os.remove(temp_output_video_path)
            return 0, None
    else:
        print("No detections in any of the frames")
        return 0, None



# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'})

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'})
    
    try:
        image = Image.open(file).convert('RGB')
        image_np = np.array(image)
        detections = detect_objects(image_np)
        count = count_objects(detections)
        
        # Konversi gambar menjadi base64
        
        # Calculate the scale factors for bounding boxes
        scale_x = image_np.shape[1] / 640
        scale_y = image_np.shape[0] / 640
        
         #copy image sebelum di resize untuk deteksi
        original_image = image_np.copy()

        # Draw bounding boxes
        for _, detection in detections.iterrows():
                xmin = int(detection['xmin'] * scale_x)
                ymin = int(detection['ymin'] * scale_y)
                xmax = int(detection['xmax'] * scale_x)
                ymax = int(detection['ymax'] * scale_y)
                cv2.rectangle(original_image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)  # Green bounding box on the original frame

         # Convert the processed image (with bounding box) to PIL
        processed_image = Image.fromarray(cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB))
      
         # Konversi gambar menjadi base64
        buffered = BytesIO()
        processed_image.save(buffered, format="JPEG")
        image_data = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return jsonify({'count': count, 'image_data': image_data})
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({'error': str(e)})

@app.route('/detect_video', methods=['POST'])
def detect_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'})

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No video selected'})

    try:
        video_file = file.read()
        # Save video temporarily (can be done in memory)
        temp_video_path = "temp_video.mp4"
        with open(temp_video_path, "wb") as f:
            f.write(video_file)
        
        average_count, video_data = process_video(temp_video_path)
        os.remove(temp_video_path)  # Remove the temporary file
    

        if average_count is not None:
            return jsonify({'average_count': average_count, 'video_data': video_data})
        else:
            return jsonify({'error': "Error processing video."})
    except Exception as e:
        print(f"Error during video processing: {e}")
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)