"""
test_insertdata_client.py

Client untuk testing InsertdataController endpoints
Bisa dijalankan langsung untuk test sebelum camera.py dijalankan
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================
# CONFIGURATION
# ============================================================
BACKEND_URL = "http://localhost:8000/api"
INSERTDATA_URL = f"{BACKEND_URL}/insertdata"
TIMEOUT = 10

# ANSI Colors untuk output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(msg: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def print_json(data: Dict[str, Any]):
    """Pretty print JSON"""
    print(json.dumps(data, indent=2, default=str))


# ============================================================
# TEST FUNCTIONS
# ============================================================

def test_backend_health() -> bool:
    """Test backend health endpoint"""
    print_section("TEST 1: Backend Health Check")
    
    try:
        response = requests.get(f"http://localhost:8000/health", timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        print_success("Backend is running!")
        print_json(data)
        return True
    
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend at http://localhost:8000")
        print_error("Make sure FastAPI is running: python backend/main.py")
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_set_buffer(
    grade: str = "A",
    score: float = 82.5,
    length: float = 12.5,
    diameter: float = 8.3,
    weight: float = 450.0,
    ratio: float = 1.51,
    filename: str = None
) -> bool:
    """Test set grading data to buffer"""
    print_section("TEST 2: Set Grading Data to Buffer")
    
    if filename is None:
        filename = f"test_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    params = {
        "grade": grade,
        "score": score,
        "length": length,
        "diameter": diameter,
        "weight": weight,
        "ratio": ratio,
        "filename": filename
    }
    
    print_info(f"Setting buffer with parameters:")
    print_json(params)
    
    try:
        response = requests.post(
            f"{INSERTDATA_URL}/grading-buffer",
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Data set to buffer successfully!")
        print_json(data)
        return True
    
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code}")
        try:
            print_json(e.response.json())
        except:
            print_error(e.response.text)
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_buffer_status() -> bool:
    """Test get buffer status"""
    print_section("TEST 3: Check Buffer Status")
    
    try:
        response = requests.get(
            f"{INSERTDATA_URL}/buffer-status",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Buffer status retrieved!")
        print_json(data)
        
        if data.get('has_data'):
            print_success("Buffer has valid data - ready to insert")
            return True
        else:
            print_error("Buffer is empty or invalid")
            return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_insert_from_buffer() -> bool:
    """Test insert data from buffer to database"""
    print_section("TEST 4: Insert Data from Buffer to Database")
    
    print_info("Inserting data to database...")
    
    try:
        response = requests.post(
            f"{INSERTDATA_URL}/insert-from-buffer",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Data inserted to database successfully!")
        print_json(data)
        
        # Print key info
        print(f"\n{Colors.BOLD}Inserted Record:{Colors.END}")
        print(f"  ID: {data.get('id')}")
        print(f"  File: {data.get('filename')}")
        print(f"  Grade: {data.get('final_grade')}")
        print(f"  Score: {data.get('fuzzy_score')}")
        print(f"  Length: {data.get('length_cm')} cm")
        print(f"  Diameter: {data.get('diameter_cm')} cm")
        print(f"  Weight: {data.get('weight_est_g')} g\n")
        
        return True
    
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code}")
        try:
            print_json(e.response.json())
        except:
            print_error(e.response.text)
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_direct_insert(
    grade: str = "B",
    score: float = 65.0,
    length: float = 10.2,
    diameter: float = 7.5,
    weight: float = 300.0,
    ratio: float = 1.36,
    filename: str = None
) -> bool:
    """Test direct insert (bypass buffer)"""
    print_section("TEST 5: Direct Insert to Database (Bypass Buffer)")
    
    if filename is None:
        filename = f"direct_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    payload = {
        "filename": filename,
        "length_cm": length,
        "diameter_cm": diameter,
        "weight_est_g": weight,
        "ratio": ratio,
        "fuzzy_score": score,
        "grade_by_weight": grade,
        "final_grade": grade
    }
    
    print_info("Direct insert payload:")
    print_json(payload)
    
    try:
        response = requests.post(
            f"{INSERTDATA_URL}/grading-from-camera",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Direct insert successful!")
        print_json(data)
        return True
    
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code}")
        try:
            print_json(e.response.json())
        except:
            print_error(e.response.text)
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_batch_insert() -> bool:
    """Test batch insert multiple records"""
    print_section("TEST 6: Batch Insert Multiple Records")
    
    batch_data = [
        {
            "filename": f"batch_photo_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            "length_cm": 11.5,
            "diameter_cm": 8.0,
            "weight_est_g": 400.0,
            "ratio": 1.44,
            "fuzzy_score": 70.0,
            "grade_by_weight": "A",
            "final_grade": "A"
        },
        {
            "filename": f"batch_photo_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            "length_cm": 9.8,
            "diameter_cm": 7.2,
            "weight_est_g": 280.0,
            "ratio": 1.36,
            "fuzzy_score": 55.0,
            "grade_by_weight": "B",
            "final_grade": "B"
        },
        {
            "filename": f"batch_photo_3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            "length_cm": 8.5,
            "diameter_cm": 6.5,
            "weight_est_g": 180.0,
            "ratio": 1.31,
            "fuzzy_score": 40.0,
            "grade_by_weight": "C",
            "final_grade": "C"
        }
    ]
    
    print_info(f"Batch inserting {len(batch_data)} records...")
    
    try:
        response = requests.post(
            f"{INSERTDATA_URL}/batch-insert",
            json=batch_data,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Batch insert successful!")
        print_json(data)
        
        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Total: {data.get('total')}")
        print(f"  Inserted: {data.get('inserted')}")
        print(f"  Failed: {data.get('failed')}\n")
        
        return True
    
    except requests.exceptions.HTTPError as e:
        print_error(f"HTTP Error: {e.response.status_code}")
        try:
            print_json(e.response.json())
        except:
            print_error(e.response.text)
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_clear_buffer() -> bool:
    """Test clear buffer"""
    print_section("TEST 7: Clear Buffer")
    
    try:
        response = requests.delete(
            f"{INSERTDATA_URL}/clear-buffer",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        print_success("Buffer cleared successfully!")
        print_json(data)
        return True
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# ============================================================
# MAIN TEST SUITE
# ============================================================

def run_full_test_suite():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║  InsertdataController - Complete Test Suite            ║")
    print("║  Testing Camera → Backend → Database Integration       ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Set Buffer", test_set_buffer),
        ("Buffer Status", test_buffer_status),
        ("Insert from Buffer", test_insert_from_buffer),
        ("Direct Insert", test_direct_insert),
        ("Batch Insert", test_batch_insert),
        ("Clear Buffer", test_clear_buffer),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "PASS" if result else "FAIL"
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {e}")
            results[test_name] = "ERROR"
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    errors = sum(1 for v in results.values() if v == "ERROR")
    
    for test_name, status in results.items():
        if status == "PASS":
            print(f"{Colors.GREEN}✓ {test_name}: {status}{Colors.END}")
        elif status == "FAIL":
            print(f"{Colors.YELLOW}⚠ {test_name}: {status}{Colors.END}")
        else:
            print(f"{Colors.RED}✗ {test_name}: {status}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Result: {passed} PASSED, {failed} FAILED, {errors} ERROR{Colors.END}\n")
    
    if passed == len(tests):
        print_success("All tests passed! ✨")
        print_info("Your integration is ready for production use.\n")
    else:
        print_error(f"Some tests failed. Please check the errors above.\n")


if __name__ == "__main__":
    run_full_test_suite()
