#!/bin/bash
# Quick verification script for async crawl deployment

echo "============================================================"
echo "ASYNC CRAWL - DEPLOYMENT VERIFICATION"
echo "============================================================"
echo ""

# Get Railway URL from user
read -p "Enter your Railway app URL (e.g., https://your-app.railway.app): " RAILWAY_URL

echo ""
echo "Testing async crawl endpoints..."
echo "------------------------------------------------------------"

# Test 1: Check if async endpoint exists
echo "1. Checking if async endpoints are available..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/admin/crawl-status?job_ids=test")

if [ "$HTTP_CODE" = "404" ]; then
    echo "   ✗ FAIL: Async endpoints not found (404)"
    echo "   → USE_ASYNC_CRAWL might be false"
    echo "   → Check Railway logs for worker startup"
    exit 1
elif [ "$HTTP_CODE" = "400" ]; then
    echo "   ✓ PASS: Async endpoints exist (returns 400 for invalid job_ids)"
else
    echo "   ⚠ WARNING: Unexpected status code: $HTTP_CODE"
fi

echo ""
echo "2. Checking frontend..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ PASS: Frontend loads successfully"
else
    echo "   ✗ FAIL: Frontend returned $HTTP_CODE"
    exit 1
fi

echo ""
echo "============================================================"
echo "VERIFICATION COMPLETE ✓"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Open your admin panel: $RAILWAY_URL"
echo "2. Navigate to ESP Management"
echo "3. Select 1-2 URLs and click 'Crawl Selected'"
echo "4. You should see a progress tracker with real-time updates!"
echo ""
echo "To run full test suite:"
echo "  python3 backend/test_async_crawl.py"
echo ""
