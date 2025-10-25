# Bug Fix: Strategies JSON Conversion Error

## Issue
**Error Message**: 
```
Error loading strategies: The JSON value could not be converted to System.Collections.Generic.Dictionary`2[System.String,System.Object]. Path: $[0].parameters | LineNumber: 0 | BytePositionInLine: 172.
```

## Root Cause

The API returns strategy parameters as an **array of objects** with structured fields:
```json
{
  "parameters": [
    {
      "name": "rsi_period",
      "type": "int",
      "defaultValue": 14,
      "description": "Period for RSI calculation"
    }
  ]
}
```

But the Blazor UI model expected a **Dictionary<string, object>**:
```csharp
public class Strategy
{
    public Dictionary<string, object>? Parameters { get; set; }
}
```

## Solution

### 1. Created New Model Class
Added `StrategyParameter` class to properly deserialize the API response:

```csharp
public class StrategyParameter
{
    public string Name { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public object? DefaultValue { get; set; }
    public string Description { get; set; } = string.Empty;
}
```

### 2. Updated Strategy Model
Changed the `Parameters` property from Dictionary to List:

```csharp
public class Strategy
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public List<StrategyParameter>? Parameters { get; set; }  // ← Changed from Dictionary
}
```

### 3. Updated Strategies.razor Display Logic
Changed from Key-Value iteration to object property access:

**Before**:
```razor
@foreach (var param in strategy.Parameters)
{
    <MudChip>@param.Key: @param.Value</MudChip>
}
```

**After**:
```razor
@foreach (var param in strategy.Parameters)
{
    <MudChip>@param.Name: @param.DefaultValue (@param.Type)</MudChip>
}
```

## Files Modified

1. **`/blazor-ui/Models/ApiModels.cs`**
   - Added `StrategyParameter` class
   - Updated `Strategy.Parameters` property type

2. **`/blazor-ui/Components/Pages/Strategies.razor`**
   - Updated foreach loop to use object properties instead of Key/Value

## Testing

### API Response (Verified):
```bash
curl -s http://localhost:5002/strategies | jq '.[0]'
```

### Blazor UI (Verified):
- ✅ Strategies page loads without errors
- ✅ All 3 strategies display correctly
- ✅ Parameters show with proper formatting: "rsi_period: 14 (int)"
- ✅ HTTP 200 responses in logs

### Test Results:
```
✅ GET /strategies - HTTP 200 OK
✅ JSON deserialization successful
✅ Page renders correctly
✅ No console errors
```

## Impact

- **Affected Pages**: Strategies page (`/strategies`)
- **User Impact**: Users can now view strategy parameters correctly
- **Breaking Changes**: None (model change is internal)
- **Deployment**: Requires rebuild and restart of Blazor UI container

## Status

✅ **FIXED** - Deployed on 2025-10-09

## Prevention

For future API integrations:
1. Always check API response format first with `curl` or Postman
2. Match model properties exactly to API response structure
3. Test JSON deserialization with sample data before UI implementation
4. Consider using OpenAPI/Swagger code generation for type safety

---

**Resolution Time**: ~5 minutes  
**Complexity**: Low  
**Risk**: Low (isolated to Strategies page)
