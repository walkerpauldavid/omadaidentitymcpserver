# PowerShell script to test Azure OAuth2 token request

Write-Host "Testing Azure OAuth2 token request..." -ForegroundColor Green

# Read values from .env file
$TENANT_ID = "542395eb-b6df-4617-af35-11deb659df7b"
$CLIENT_ID = "08eeb6a4-4aee-406f-baa5-4922993f09f3"
$CLIENT_SECRET = "2Dv8Q~W9U.k7hQN.4TBPiAzxlOLZM8ZY1JSFtaXO"
$OAUTH2_SCOPE = "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default"

$TOKEN_URL = "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token"

Write-Host "Making token request to: $TOKEN_URL"
Write-Host "Using scope: $OAUTH2_SCOPE"
Write-Host ""

# Prepare the body
$body = @{
    grant_type = "client_credentials"
    client_id = $CLIENT_ID
    client_secret = $CLIENT_SECRET
    scope = $OAUTH2_SCOPE
}

try {
    # Make the request
    $response = Invoke-RestMethod -Uri $TOKEN_URL -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Token Type: $($response.token_type)"
    Write-Host "Expires In: $($response.expires_in) seconds"
    Write-Host "Access Token (first 50 chars): $($response.access_token.Substring(0,50))..."
    
    # Decode JWT to show audience
    $tokenParts = $response.access_token.Split('.')
    $payload = $tokenParts[1]
    
    # Add padding if needed
    while ($payload.Length % 4) {
        $payload += "="
    }
    
    $decodedBytes = [Convert]::FromBase64String($payload)
    $decodedText = [System.Text.Encoding]::UTF8.GetString($decodedBytes)
    $tokenInfo = $decodedText | ConvertFrom-Json
    
    Write-Host ""
    Write-Host "Token Info:"
    Write-Host "  Audience (aud): $($tokenInfo.aud)"
    Write-Host "  Issuer (iss): $($tokenInfo.iss)"
    Write-Host "  App ID (azp): $($tokenInfo.azp)"
    
} catch {
    Write-Host "ERROR!" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)"
    Write-Host "Response: $($_.Exception.Response)"
    Write-Host "Message: $($_.Exception.Message)"
}

Write-Host ""
Read-Host "Press Enter to exit"