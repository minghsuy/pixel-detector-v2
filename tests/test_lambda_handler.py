"""
Minimal test for Lambda handler - just make sure it doesn't crash
"""
import pytest
import json
import sys
import os

# Add project root to path so we can import lambda_handler
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_handler import lambda_handler


class MockContext:
    """Mock Lambda context for testing"""
    request_id = "test-request-id"
    memory_limit_in_mb = 2048
    

def test_lambda_handler_imports():
    """Test that we can at least import the handler"""
    assert lambda_handler is not None


def test_lambda_handler_with_mock_data():
    """Test Lambda handler returns mock data when scanner unavailable"""
    # This will work even without full pixel_detector installed
    event = {
        'body': json.dumps({'domain': 'example.com'})
    }
    
    result = lambda_handler(event, MockContext())
    
    assert result['statusCode'] in [200, 500]
    assert 'body' in result
    
    body = json.loads(result['body'])
    assert 'domain' in body
    assert body['domain'] == 'example.com'


def test_lambda_handler_direct_invocation():
    """Test Lambda handler with direct invocation (no API Gateway)"""
    event = {
        'domain': 'test-direct.com'
    }
    
    result = lambda_handler(event, MockContext())
    
    assert result['statusCode'] in [200, 500]
    assert 'body' in result


def test_lambda_handler_empty_event():
    """Test Lambda handler with empty event uses default domain"""
    event = {}
    
    result = lambda_handler(event, MockContext())
    
    assert result['statusCode'] in [200, 500]
    body = json.loads(result['body'])
    assert body['domain'] == 'example.com'  # default


if __name__ == "__main__":
    # Quick local test
    print("Testing Lambda handler...")
    test_lambda_handler_imports()
    print("✓ Import works")
    
    test_lambda_handler_with_mock_data()
    print("✓ Mock data works")
    
    test_lambda_handler_direct_invocation()
    print("✓ Direct invocation works")
    
    test_lambda_handler_empty_event()
    print("✓ Empty event works")
    
    print("\n✅ All Lambda handler tests passed!")
