# PowerShell script to test Omada API call with Azure token

Write-Host "Testing Omada API call..." -ForegroundColor Green

# Read values from .env file
$TENANT_ID = "542395eb-b6df-4617-af35-11deb659df7b"
$CLIENT_ID = "08eeb6a4-4aee-406f-baa5-4922993f09f3"
$CLIENT_SECRET = "2Dv8Q~W9U.k7hQN.4TBPiAzxlOLZM8ZY1JSFtaXO"
$OAUTH2_SCOPE = "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default"
$OMADA_BASE_URL = "https://pawa-poc2.omada.cloud"

$TOKEN_URL = "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"

Write-Host "Step 1: Getting Azure token..."

# Get token
$tokenBody = @{
    grant_type = "client_credentials"
    client_id = $CLIENT_ID
    client_secret = $CLIENT_SECRET
    scope = $OAUTH2_SCOPE
}

try {
    $tokenResponse = Invoke-RestMethod -Uri $TOKEN_URL -Method Post -Body $tokenBody -ContentType "application/x-www-form-urlencoded"
    $bearerToken = "Bearer $($tokenResponse.access_token)"
    Write-Host "Token obtained successfully" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Step 2: Testing Omada API call..."
    
    # Test Omada API
    $omadaUrl = "$OMADA_BASE_URL/OData/DataObjects/Identity?`$filter=FIRSTNAME eq 'Emma' and LASTNAME eq 'Taylor'"
    Write-Host "URL: $omadaUrl"
    Write-Host "Authorization: $($bearerToken.Substring(0,20))..."
    
    $headers = @{
        "Authorization" = $bearerToken
        "Content-Type" = "application/json"
        "Accept" = "application/json"
    }
    
    $omadaResponse = Invoke-RestMethod -Uri $omadaUrl -Method Get -Headers $headers
    
    Write-Host ""
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Response:"
    $omadaResponse | ConvertTo-Json -Depth 3
    
} catch {
    Write-Host ""
    Write-Host "ERROR!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)"
    
    if ($_.Exception.Response) {
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "Response Body: $errorBody"
        } catch {
            Write-Host "Could not read error response body"
        }
    }
    
    Write-Host "Message: $($_.Exception.Message)"
}

Write-Host ""
Read-Host "Press Enter to exit"