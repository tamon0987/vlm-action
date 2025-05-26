import requests

class VisionLLMClient:
    def __init__(self, api_url, api_key=None):
        self.api_url = api_url
        self.api_key = api_key

    def analyze_image(self, image_path):
        print(f"Sending image {image_path} to LLM API...")
        files = {'image': open(image_path, 'rb')}
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        # Uncomment and modify for real API
        # response = requests.post(self.api_url, files=files, headers=headers)
        # return response.json()
        return {
            "feedback": "Simulated: Object detected at position X.",
            "suggested_action": {"action": "move_arm", "parameters": {"joint": 2, "angle": 45}}
        }

    def generate_command_from_text(self, order_text):
        print(f"Sending order '{order_text}' to LLM API...")
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        # response = requests.post(self.api_url, json={"order": order_text}, headers=headers)
        # return response.json()
        return {"angles": [0, 0, 15, 5, 0, 10], "feedback": f"Simulated LLM: Move to {order_text}"}

    def analyze_image_with_order(self, image_io, order_text):
        print(f"Sending image and order '{order_text}' to LLM API...")
        files = {'image': ('camera.jpg', image_io, 'image/jpeg')}
        data = {'order': order_text}
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        # Uncomment and modify for real API
        # response = requests.post(self.api_url, files=files, data=data, headers=headers)
        # return response.json()
        # Simulated response:
        return {
            "angles": [0, 0, 15, 5, 0, 10],
            "feedback": f"Simulated LLM: Order '{order_text}' processed with image"
        }

if __name__ == "__main__":
    llm = VisionLLMClient(api_url="https://example.com/api/vision")
    print(llm.analyze_image("test.jpg"))
    print(llm.generate_command_from_text("Pick up the red object"))
    # Simulate image+order
    import io
    print(llm.analyze_image_with_order(io.BytesIO(b"fakeimage"), "Pick up the red object"))