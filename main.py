"""
Garbage Detection System

This script implements a real-time garbage detection system using computer vision and deep learning.
It processes video input (either from a webcam or video file) to detect and classify garbage objects.
The system uses YOLOv8 for object detection and can be configured to run in different modes:
- Webcam mode: Processes live video from the default camera
- Video file mode: Processes a pre-recorded video file
- Image mode: Processes a single image

The system supports multiple garbage categories and can be configured to run on different devices (CPU/GPU).
"""

import cv2
import torch
from ultralytics import YOLO
import time
import argparse
from pathlib import Path
import os
import numpy as np
from PIL import Image
import io
import requests
from datetime import datetime
import json
import logging
from typing import Optional, Tuple, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('garbage_detection.log'),
        logging.StreamHandler()
    ]
)

def load_model(model_path: str, device: str = 'cuda') -> YOLO:
    """
    Load the YOLO model from the specified path.

    Args:
        model_path (str): Path to the YOLO model weights file
        device (str): Device to run the model on ('cuda' or 'cpu')

    Returns:
        YOLO: Loaded YOLO model instance
    """
    try:
        model = YOLO(model_path)
        model.to(device)
        return model
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        raise

def process_frame(frame: np.ndarray, model: YOLO, conf_threshold: float = 0.25) -> Tuple[np.ndarray, list]:
    """
    Process a single frame through the YOLO model.

    Args:
        frame (np.ndarray): Input frame to process
        model (YOLO): YOLO model instance
        conf_threshold (float): Confidence threshold for detections

    Returns:
        Tuple[np.ndarray, list]: Processed frame with detections and list of detection results
    """
    results = model(frame, conf=conf_threshold)[0]
    annotated_frame = results.plot()
    return annotated_frame, results.boxes.data.tolist()

def process_image(image_path: str, model: YOLO, conf_threshold: float = 0.25) -> Tuple[np.ndarray, list]:
    """
    Process a single image through the YOLO model.

    Args:
        image_path (str): Path to the input image
        model (YOLO): YOLO model instance
        conf_threshold (float): Confidence threshold for detections

    Returns:
        Tuple[np.ndarray, list]: Processed image with detections and list of detection results
    """
    results = model(image_path, conf=conf_threshold)[0]
    annotated_image = results.plot()
    return annotated_image, results.boxes.data.tolist()

def process_video(video_path: str, model: YOLO, conf_threshold: float = 0.25) -> None:
    """
    Process a video file through the YOLO model.

    Args:
        video_path (str): Path to the input video file
        model (YOLO): YOLO model instance
        conf_threshold (float): Confidence threshold for detections
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Error opening video file: {video_path}")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame, detections = process_frame(frame, model, conf_threshold)
        cv2.imshow('Garbage Detection', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def process_webcam(model: YOLO, conf_threshold: float = 0.25) -> None:
    """
    Process live webcam feed through the YOLO model.

    Args:
        model (YOLO): YOLO model instance
        conf_threshold (float): Confidence threshold for detections
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Error opening webcam")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        processed_frame, detections = process_frame(frame, model, conf_threshold)
        cv2.imshow('Garbage Detection', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def main():
    """
    Main function to run the garbage detection system.
    Handles command line arguments and initializes the detection process.
    """
    parser = argparse.ArgumentParser(description='Garbage Detection System')
    parser.add_argument('--model', type=str, default='best.pt', help='Path to YOLO model')
    parser.add_argument('--source', type=str, help='Path to image or video file (optional)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold')
    parser.add_argument('--device', type=str, default='cuda', help='Device to run on (cuda/cpu)')
    args = parser.parse_args()

    try:
        model = load_model(args.model, args.device)
        
        if args.source:
            if args.source.lower().endswith(('.png', '.jpg', '.jpeg')):
                processed_image, detections = process_image(args.source, model, args.conf)
                cv2.imshow('Garbage Detection', processed_image)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            else:
                process_video(args.source, model, args.conf)
        else:
            process_webcam(model, args.conf)

    except Exception as e:
        logging.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 