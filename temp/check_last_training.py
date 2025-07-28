# File: temp/check_last_training.py
# بررسی آخرین training job و نتایج آن

import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "testuser2@example.com"
TEST_USER_PASSWORD = "TestPassword123!"

def get_auth_token():
    """دریافت auth token"""
    login_data = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    response = requests.post(
        f"{API_BASE_URL}/auth/login", 
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def check_training_jobs():
    """بررسی training jobs"""
    token = get_auth_token()
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Checking Training Jobs...")
    print("=" * 30)
    
    # Get training jobs
    response = requests.get(f"{API_BASE_URL}/ml/training/jobs", headers=headers)
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"✅ Found {len(jobs)} training jobs")
        
        for job in jobs:
            print(f"\n📋 Job: {job.get('job_id')}")
            print(f"   Symbol: {job.get('crypto_symbol')}")
            print(f"   Status: {job.get('status')}")
            print(f"   Message: {job.get('message')}")
            print(f"   Started: {job.get('started_at')}")
            print(f"   Completed: {job.get('completed_at')}")
            
            # Show metrics if available
            if job.get('training_metrics'):
                print(f"   Training Metrics: {job.get('training_metrics')}")
            if job.get('validation_metrics'):
                print(f"   Validation Metrics: {job.get('validation_metrics')}")
            if job.get('model_performance'):
                print(f"   Model Performance: {job.get('model_performance')}")
                
    else:
        print(f"❌ Failed to get jobs: {response.status_code}")
        print(f"   Details: {response.text}")

def check_models():
    """بررسی models"""
    token = get_auth_token()
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Checking Models...")
    print("=" * 25)
    
    # Get models
    response = requests.get(f"{API_BASE_URL}/ml/models/list", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"✅ Found {len(models)} models")
        
        for model in models:
            print(f"\n📋 Model: {model.get('model_id')}")
            print(f"   Symbol: {model.get('crypto_symbol')}")
            print(f"   Type: {model.get('model_type')}")
            print(f"   Active: {model.get('is_active')}")
            print(f"   Created: {model.get('created_at')}")
            
    else:
        print(f"❌ Failed to get models: {response.status_code}")
        print(f"   Details: {response.text}")

def main():
    print("🔍 Last Training Job Investigation")
    print("=" * 40)
    
    check_training_jobs()
    check_models()
    
    print(f"\n💡 Analysis:")
    print("   If training jobs show 'completed' but models list is empty,")
    print("   then the issue is in model registration process.")

if __name__ == "__main__":
    main()