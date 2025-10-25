#!/bin/bash

# Complete Travel API Testing Script
# Tests all endpoints and pages

echo "==================================="
echo "TRAVEL PLANNER - COMPLETE TEST SUITE"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test user ID (admin from database)
USER_ID="b00abbd0-bad9-414b-ab87-c46b422f3780"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -n "Testing: $name... "
    
    if [ -z "$data" ]; then
        response=$(docker compose exec -T api curl -s -w "\n%{http_code}" -X $method \
            -H "Cookie: user_id=$USER_ID" \
            "http://localhost:8000$url")
    else
        response=$(docker compose exec -T api curl -s -w "\n%{http_code}" -X $method \
            -H "Content-Type: application/json" \
            -H "Cookie: user_id=$USER_ID" \
            -d "$data" \
            "http://localhost:8000$url")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC} (Status: $status_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Expected: $expected_status, Got: $status_code)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "==================================="
echo "1. HEALTH CHECK"
echo "==================================="
test_endpoint "Health Check" "GET" "/api/travel/health" "" "200"
echo ""

echo "==================================="
echo "2. TRIPS ENDPOINTS"
echo "==================================="
test_endpoint "List Trips (Empty)" "GET" "/api/travel/trips" "" "200"

# Create trip
TRIP_DATA='{
  "name": "Paris Weekend",
  "description": "Quick trip to Paris",
  "start_date": "2025-12-15",
  "end_date": "2025-12-17",
  "destination_city": "Paris",
  "destination_country": "France",
  "timezone": "Europe/Paris",
  "budget_total": 1500,
  "budget_currency": "EUR",
  "status": "planning"
}'
test_endpoint "Create Trip" "POST" "/api/travel/trips" "$TRIP_DATA" "201"

# Get trip ID from response
TRIP_ID=$(docker compose exec -T api curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Cookie: user_id=$USER_ID" \
    -d "$TRIP_DATA" \
    "http://localhost:8000/api/travel/trips" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

echo "Created Trip ID: $TRIP_ID"

test_endpoint "Get Trip by ID" "GET" "/api/travel/trips/$TRIP_ID" "" "200"
test_endpoint "List Trips (With Data)" "GET" "/api/travel/trips" "" "200"

# Update trip
UPDATE_DATA='{"status": "confirmed"}'
test_endpoint "Update Trip" "PUT" "/api/travel/trips/$TRIP_ID" "$UPDATE_DATA" "200"

echo ""

echo "==================================="
echo "3. ACTIVITIES ENDPOINTS"
echo "==================================="
test_endpoint "List Activities (Empty)" "GET" "/api/travel/trips/$TRIP_ID/activities" "" "200"

# Create activity
ACTIVITY_DATA='{
  "name": "Eiffel Tower Visit",
  "description": "Visit the iconic Eiffel Tower",
  "start_date": "2025-12-15",
  "start_time": "10:00",
  "end_date": "2025-12-15",
  "end_time": "13:00",
  "category": "sightseeing",
  "priority": "must_see",
  "location": "Champ de Mars",
  "latitude": 48.8584,
  "longitude": 2.2945,
  "estimated_cost": 25,
  "estimated_duration": 3
}'
test_endpoint "Create Activity" "POST" "/api/travel/trips/$TRIP_ID/activities" "$ACTIVITY_DATA" "201"

# Get activity ID
ACTIVITY_ID=$(docker compose exec -T api curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Cookie: user_id=$USER_ID" \
    -d "$ACTIVITY_DATA" \
    "http://localhost:8000/api/travel/trips/$TRIP_ID/activities" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

echo "Created Activity ID: $ACTIVITY_ID"

test_endpoint "Get Activity by ID" "GET" "/api/travel/trips/$TRIP_ID/activities/$ACTIVITY_ID" "" "200"
test_endpoint "List Activities (With Data)" "GET" "/api/travel/trips/$TRIP_ID/activities" "" "200"

# Update activity
ACTIVITY_UPDATE='{"priority": "high"}'
test_endpoint "Update Activity" "PUT" "/api/travel/trips/$TRIP_ID/activities/$ACTIVITY_ID" "$ACTIVITY_UPDATE" "200"

echo ""

echo "==================================="
echo "4. ACCOMMODATIONS ENDPOINTS"
echo "==================================="
test_endpoint "List Accommodations (Empty)" "GET" "/api/travel/trips/$TRIP_ID/accommodations" "" "200"

# Create accommodation
ACCOMMODATION_DATA='{
  "name": "Hotel de Paris",
  "accommodation_type": "hotel",
  "address": "123 Rue de Rivoli",
  "city": "Paris",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "check_in_date": "2025-12-15",
  "check_in_time": "15:00",
  "check_out_date": "2025-12-17",
  "check_out_time": "11:00",
  "total_cost": 600,
  "currency": "EUR",
  "confirmation_number": "ABC123",
  "booking_status": "confirmed"
}'
test_endpoint "Create Accommodation" "POST" "/api/travel/trips/$TRIP_ID/accommodations" "$ACCOMMODATION_DATA" "201"

# Get accommodation ID
ACCOMMODATION_ID=$(docker compose exec -T api curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Cookie: user_id=$USER_ID" \
    -d "$ACCOMMODATION_DATA" \
    "http://localhost:8000/api/travel/trips/$TRIP_ID/accommodations" | grep -o '"id":[0-9]*' | grep -o '[0-9]*' | head -1)

echo "Created Accommodation ID: $ACCOMMODATION_ID"

test_endpoint "Get Accommodation by ID" "GET" "/api/travel/trips/$TRIP_ID/accommodations/$ACCOMMODATION_ID" "" "200"
test_endpoint "List Accommodations (With Data)" "GET" "/api/travel/trips/$TRIP_ID/accommodations" "" "200"

echo ""

echo "==================================="
echo "5. ANALYTICS ENDPOINTS"
echo "==================================="
test_endpoint "Trip Summary" "GET" "/api/travel/trips/$TRIP_ID/summary" "" "200"
test_endpoint "Daily Itinerary" "GET" "/api/travel/trips/$TRIP_ID/itinerary/daily" "" "200"

echo ""

echo "==================================="
echo "6. DELETE OPERATIONS"
echo "==================================="
test_endpoint "Delete Activity" "DELETE" "/api/travel/trips/$TRIP_ID/activities/$ACTIVITY_ID" "" "200"
test_endpoint "Delete Accommodation" "DELETE" "/api/travel/trips/$TRIP_ID/accommodations/$ACCOMMODATION_ID" "" "200"
test_endpoint "Delete Trip" "DELETE" "/api/travel/trips/$TRIP_ID" "" "200"

echo ""

echo "==================================="
echo "TEST SUMMARY"
echo "==================================="
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed!${NC}"
    exit 1
fi
