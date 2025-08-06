"""
Simple Lambda handler for Pixel Detector v0.3
Goal: Learn AWS Lambda, not build enterprise infrastructure
"""
import json
import asyncio
import os
from datetime import datetime

# This will fail on first import, that's OK - we'll handle it
try:
    from pixel_detector import PixelScanner
    SCANNER_AVAILABLE = True
except ImportError:
    SCANNER_AVAILABLE = False
    print("WARNING: PixelScanner not available - Lambda will return mock data")


def lambda_handler(event, context):
    """
    Minimal Lambda handler that actually works.
    No fancy error handling, no complex features - just scanning.
    """
    print(f"Lambda invoked at {datetime.now()}")
    print(f"Event: {json.dumps(event)}")
    
    # Parse the request (handle both API Gateway and direct invocation)
    if isinstance(event.get('body'), str):
        try:
            body = json.loads(event['body'])
        except:
            body = {}
    else:
        body = event
    
    domain = body.get('domain', 'example.com')
    
    # If running locally without full setup, return mock data
    if not SCANNER_AVAILABLE:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'mock',
                'domain': domain,
                'message': 'Scanner not available - returning mock data',
                'pixels_detected': 1,
                'pixel_types': ['google_analytics']
            })
        }
    
    # Real scanning
    try:
        # Run async scanner in sync Lambda context
        scanner = PixelScanner()
        result = asyncio.run(scanner.scan_domain(domain))
        
        response_data = {
            'status': 'success',
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'pixels_detected': len(result.pixels_detected),
            'pixel_types': [p.type for p in result.pixels_detected],
            'scan_time': result.scan_metadata.page_load_time if result.scan_metadata else None
        }
        
        # Log for CloudWatch
        print(f"Scan complete: {json.dumps(response_data)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Scan-Time': str(response_data.get('scan_time', 0))
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        error_response = {
            'status': 'error',
            'domain': domain,
            'error': str(e),
            'error_type': type(e).__name__
        }
        print(f"Error scanning {domain}: {error_response}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_response)
        }


# For local testing
if __name__ == "__main__":
    test_event = {
        'body': json.dumps({'domain': 'mountsinai.org'})
    }
    
    class MockContext:
        request_id = "local-test"
        
    result = lambda_handler(test_event, MockContext())
    print(f"Result: {json.dumps(result, indent=2)}")
