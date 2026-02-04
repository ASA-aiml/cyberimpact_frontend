"""
Test script for session-based repository isolation with virtual environments.

This script tests:
1. Session creation with venv
2. Repository cloning in session directory
3. Session isolation between users
4. Automatic cleanup
"""

import requests
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_REPO_URL = "https://github.com/octocat/Hello-World.git"

# Mock Firebase token (replace with actual token for real testing)
# For testing, you'll need to get a real Firebase ID token from your frontend
FIREBASE_TOKEN = "YOUR_FIREBASE_ID_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {FIREBASE_TOKEN}",
    "Content-Type": "application/json"
}

def test_session_creation_and_cleanup():
    """Test session creation, repo cloning, and cleanup"""
    print("=" * 60)
    print("TEST 1: Session Creation and Repository Cloning")
    print("=" * 60)
    
    # Step 1: Analyze repository (creates session)
    print("\n1. Creating session and analyzing repository...")
    response = requests.post(
        f"{BASE_URL}/scan/analyze",
        json={"repo_url": TEST_REPO_URL},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        print(response.json())
        return
    
    data = response.json()
    session_id = data["session_id"]
    print(f"✅ Session created: {session_id}")
    print(f"   Suggested tools: {data['suggested_tools']}")
    print(f"   Expires at: {data['session_expires_at']}")
    
    # Step 2: Check session status
    print("\n2. Checking session status...")
    response = requests.get(
        f"{BASE_URL}/api/session/{session_id}/status",
        headers=headers
    )
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"✅ Session status: {status_data['status']}")
        print(f"   Created: {status_data['created_at']}")
    else:
        print(f"❌ Failed to get session status: {response.status_code}")
    
    # Step 3: Verify session directory exists
    print("\n3. Verifying session directory structure...")
    session_dir = Path(f"/tmp/cyberimpact/{session_id}")
    venv_dir = session_dir / "venv"
    repos_dir = session_dir / "repos"
    
    if session_dir.exists():
        print(f"✅ Session directory exists: {session_dir}")
        print(f"   - venv exists: {venv_dir.exists()}")
        print(f"   - repos exists: {repos_dir.exists()}")
        
        # List repos
        if repos_dir.exists():
            repos = list(repos_dir.glob("*"))
            print(f"   - Cloned repositories: {len(repos)}")
            for repo in repos:
                print(f"     • {repo.name}")
    else:
        print(f"❌ Session directory not found: {session_dir}")
    
    # Step 4: Test heartbeat
    print("\n4. Testing session heartbeat...")
    response = requests.post(
        f"{BASE_URL}/api/session/{session_id}/heartbeat",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Heartbeat successful")
    else:
        print(f"❌ Heartbeat failed: {response.status_code}")
    
    # Step 5: Manual cleanup
    print("\n5. Testing manual cleanup...")
    response = requests.delete(
        f"{BASE_URL}/api/session/{session_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Session cleaned up successfully")
    else:
        print(f"❌ Cleanup failed: {response.status_code}")
    
    # Step 6: Verify directory is deleted
    print("\n6. Verifying cleanup...")
    time.sleep(1)  # Give it a moment to delete
    
    if not session_dir.exists():
        print(f"✅ Session directory removed: {session_dir}")
    else:
        print(f"❌ Session directory still exists: {session_dir}")
    
    print("\n" + "=" * 60)
    print("TEST 1 COMPLETED")
    print("=" * 60)

def test_concurrent_sessions():
    """Test multiple concurrent sessions"""
    print("\n" + "=" * 60)
    print("TEST 2: Concurrent Session Isolation")
    print("=" * 60)
    
    sessions = []
    
    # Create 3 sessions
    print("\n1. Creating 3 concurrent sessions...")
    for i in range(3):
        response = requests.post(
            f"{BASE_URL}/scan/analyze",
            json={"repo_url": TEST_REPO_URL},
            headers=headers
        )
        
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            sessions.append(session_id)
            print(f"✅ Session {i+1} created: {session_id}")
        else:
            print(f"❌ Failed to create session {i+1}")
    
    # List all sessions
    print("\n2. Listing all active sessions...")
    response = requests.get(f"{BASE_URL}/api/sessions", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} active sessions")
        for session in data['sessions']:
            print(f"   • {session['session_id']}")
    else:
        print(f"❌ Failed to list sessions")
    
    # Verify isolation
    print("\n3. Verifying session isolation...")
    for session_id in sessions:
        session_dir = Path(f"/tmp/cyberimpact/{session_id}")
        if session_dir.exists():
            print(f"✅ Isolated directory exists: {session_id[:8]}...")
        else:
            print(f"❌ Directory missing: {session_id[:8]}...")
    
    # Cleanup all sessions
    print("\n4. Cleaning up all sessions...")
    for session_id in sessions:
        response = requests.delete(
            f"{BASE_URL}/api/session/{session_id}",
            headers=headers
        )
        if response.status_code == 200:
            print(f"✅ Cleaned up: {session_id[:8]}...")
        else:
            print(f"❌ Failed to cleanup: {session_id[:8]}...")
    
    print("\n" + "=" * 60)
    print("TEST 2 COMPLETED")
    print("=" * 60)

def test_full_scan_workflow():
    """Test complete workflow: analyze -> execute -> cleanup"""
    print("\n" + "=" * 60)
    print("TEST 3: Full Scan Workflow")
    print("=" * 60)
    
    # Step 1: Analyze
    print("\n1. Analyzing repository...")
    response = requests.post(
        f"{BASE_URL}/scan/analyze",
        json={"repo_url": TEST_REPO_URL},
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Analysis failed: {response.status_code}")
        return
    
    data = response.json()
    session_id = data["session_id"]
    suggested_tools = data["suggested_tools"]
    print(f"✅ Analysis complete. Session: {session_id}")
    print(f"   Tools: {suggested_tools}")
    
    # Step 2: Execute scan
    print("\n2. Executing security scan...")
    response = requests.post(
        f"{BASE_URL}/scan/execute",
        json={
            "session_id": session_id,
            "selected_tools": suggested_tools[:2]  # Use first 2 tools
        },
        headers=headers
    )
    
    if response.status_code == 200:
        scan_data = response.json()
        print(f"✅ Scan completed successfully")
        print(f"   Results: {list(scan_data.get('results', {}).keys())}")
    else:
        print(f"❌ Scan failed: {response.status_code}")
        print(response.json())
    
    # Step 3: Cleanup
    print("\n3. Cleaning up session...")
    response = requests.delete(
        f"{BASE_URL}/api/session/{session_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ Session cleaned up")
    else:
        print(f"❌ Cleanup failed")
    
    print("\n" + "=" * 60)
    print("TEST 3 COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🧪 SESSION-BASED REPOSITORY ISOLATION TESTS")
    print("=" * 60)
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    print("⚠️  Replace FIREBASE_TOKEN with a valid Firebase ID token")
    print("=" * 60)
    
    if FIREBASE_TOKEN == "YOUR_FIREBASE_ID_TOKEN_HERE":
        print("\n❌ ERROR: Please set a valid Firebase ID token in the script")
        print("   You can get one by logging in through the frontend and")
        print("   copying the token from the browser's developer console.")
        exit(1)
    
    try:
        # Run tests
        test_session_creation_and_cleanup()
        time.sleep(2)
        
        test_concurrent_sessions()
        time.sleep(2)
        
        test_full_scan_workflow()
        
        print("\n✅ ALL TESTS COMPLETED")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend server")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
