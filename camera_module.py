import cv2
import time

class Camera:
    def __init__(self, camera_index=0, output_dir="captures"):
        self.camera_index = camera_index
        self.output_dir = output_dir

    def capture_image(self, filename=None):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError("Cannot open camera")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture image")
        if filename is None:
            timestamp = int(time.time())
            filename = f"{self.output_dir}/capture_{timestamp}.jpg"
        else:
            filename = f"{self.output_dir}/{filename}"
        # Ensure output directory exists
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        cv2.imwrite(filename, frame)
        print(f"Image saved to {filename}")
        return filename

if __name__ == "__main__":
    camera = Camera()
    camera.capture_image()