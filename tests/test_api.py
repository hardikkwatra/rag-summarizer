import requests
import time
import json

# API endpoint
BASE_URL = "https://summarizer.braindrop.fun"

def test_health():
    """Test the health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["status"] in ["ok", "degraded"]

def test_summarization():
    """Test the summarization endpoint"""
    text = """
    Artificial Intelligence (AI) has made significant strides in recent years, 
    transforming various industries and aspects of daily life. From healthcare 
    to finance, AI-powered solutions are enhancing efficiency, accuracy, and 
    decision-making processes. However, the rapid advancement of AI also raises 
    ethical concerns and questions about its impact on employment and privacy.
    """
    
    # Submit summarization request
    response = requests.post(
        f"{BASE_URL}/api/summarize",
        json={"text": text}
    )
    print(f"Summarization request: {response.status_code}")
    assert response.status_code in [200, 202]
    
    task_data = response.json()
    print(json.dumps(task_data, indent=2))
    
    # Check if this is a cached result
    if task_data["task_id"].startswith("cached:"):
        print("Result was cached")
        result = task_data["task_id"].replace("cached:", "")
        print(f"Summary: {result}")
        return
    
    # Check result
    task_id = task_data["task_id"]
    max_retries = 30
    retries = 0
    
    while retries < max_retries:
        response = requests.get(f"{BASE_URL}/api/result/{task_id}")
        if response.status_code == 200:
            print("Summary result:")
            result = response.json()
            print(json.dumps(result, indent=2))
            assert "result" in result
            break
        elif response.status_code == 202:
            print(f"Task still processing... (retry {retries+1}/{max_retries})")
            retries += 1
            time.sleep(1)
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
            assert False, f"Unexpected status code: {response.status_code}"
            break
    
    assert retries < max_retries, "Task took too long to complete"

def test_invalid_parameters():
    """Test invalid parameters"""
    response = requests.post(
        f"{BASE_URL}/api/summarize",
        json={"text": "Sample text", "length": "invalid"}
    )
    print(f"Invalid parameter test: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 422

if __name__ == "__main__":
    print("Testing health endpoint...")
    test_health()
    
    print("\nTesting summarization...")
    test_summarization()
    
    print("\nTesting invalid parameters...")
    test_invalid_parameters()
    
    print("\nAll tests passed!")
