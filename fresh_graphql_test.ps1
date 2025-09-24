# PowerShell version of fresh_graphql_test.py
# Test script for Omada GraphQL API using exact query from working_raw_graph_query.txt

param(
    [string]$ImpersonateUser = "ROBWOL@54MV4C.ONMICROSOFT.COM"
)

# Function to load environment variables from .env file
function Load-EnvFile {
    param([string]$Path = ".env")
    
    if (Test-Path $Path) {
        Write-Host "[ENV] Loading environment variables from $Path" -ForegroundColor Yellow
        Get-Content $Path | ForEach-Object {
            if ($_ -match '^([^#][^=]*?)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "[ENV] Set $name" -ForegroundColor Green
            }
        }
    } else {
        Write-Error "Environment file $Path not found"
        exit 1
    }
}

# Function to get OAuth2 token from Azure AD
function Get-OAuthToken {
    param(
        [string]$TenantId,
        [string]$ClientId,
        [string]$ClientSecret,
        [string]$Scope
    )
    
    Write-Host "[TOKEN] Getting OAuth2 token..." -ForegroundColor Yellow
    
    $tokenUrl = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"
    
    $body = @{
        grant_type    = "client_credentials"
        client_id     = $ClientId
        client_secret = $ClientSecret
        scope         = $Scope
    }
    
    try {
        $response = Invoke-RestMethod -Uri $tokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
        Write-Host "[TOKEN] [SUCCESS] Got new token: $($response.access_token.Substring(0, 50))..." -ForegroundColor Green
        return $response.access_token
    }
    catch {
        Write-Error "[TOKEN] [ERROR] Failed to get token: $($_.Exception.Message)"
        Write-Error "Response: $($_.Exception.Response)"
        throw
    }
}

# Function to test GraphQL contexts query
function Test-GraphQLContexts {
    param(
        [string]$AccessToken,
        [string]$GraphQLUrl,
        [string]$ImpersonateUser
    )
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "TESTING OMADA GRAPHQL CONTEXTS QUERY" -ForegroundColor Cyan
    Write-Host "=" * 80 -ForegroundColor Cyan
    
    try {
        # Try parsing the exact working Postman JSON
        $postmanPayload = '{"query":"query accessRequest {\r\n    accessRequest {\r\n        contexts(identityIds:[\"e3e869c4-369a-476e-a969-d57059d0b1e4\"]){ \r\n            id\r\n            name\r\n         }\r\n    }\r\n}","variables":{}}'
        $graphqlQuery = $postmanPayload | ConvertFrom-Json
        
        # Headers - match Postman exactly
        $headers = @{
            "Authorization"    = "Bearer $AccessToken"
            "Content-Type"     = "application/json"
            "Accept"          = "application/json"
            "impersonate_user" = $ImpersonateUser
            "User-Agent"      = "PowerShell-GraphQL-Test/1.0"
        }
        
        Write-Host ""
        Write-Host "[REQUEST] Sending GraphQL request" -ForegroundColor Yellow
        Write-Host "URL: $GraphQLUrl" -ForegroundColor Gray
        Write-Host "Headers:" -ForegroundColor Gray
        foreach ($header in $headers.GetEnumerator()) {
            if ($header.Key -eq "Authorization") {
                $tokenPreview = $header.Value.Split(' ')[1].Substring(0, 20)
                Write-Host "  $($header.Key): Bearer $tokenPreview..." -ForegroundColor Gray
            } else {
                Write-Host "  $($header.Key): $($header.Value)" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        Write-Host "GraphQL Query (raw):" -ForegroundColor Gray
        Write-Host $graphqlQuery.query.ToString() -ForegroundColor Gray
        Write-Host ""
        Write-Host "Full JSON payload:" -ForegroundColor Gray
        Write-Host ($graphqlQuery | ConvertTo-Json -Depth 10) -ForegroundColor Gray
        
        # Convert to JSON - use specific settings to match Postman
        $jsonBody = $graphqlQuery | ConvertTo-Json -Depth 10 -Compress
        
        Write-Host ""
        Write-Host "Final JSON Body being sent:" -ForegroundColor Yellow
        Write-Host $jsonBody -ForegroundColor White
        
        Write-Host ""
        Write-Host "Content-Length: $($jsonBody.Length)" -ForegroundColor Yellow
        
        try {
            # Try with Invoke-RestMethod first (better JSON handling)
            Write-Host ""
            Write-Host "[ATTEMPTING] Using Invoke-RestMethod..." -ForegroundColor Yellow
            
            $restResponse = Invoke-RestMethod -Uri $GraphQLUrl -Method Post -Body $jsonBody -Headers $headers -ContentType "application/json"
            
            Write-Host "[SUCCESS] Invoke-RestMethod worked!" -ForegroundColor Green
            
            # Convert RestMethod response to WebRequest-like format
            $response = [PSCustomObject]@{
                StatusCode = 200
                Content = ($restResponse | ConvertTo-Json -Depth 10)
                Headers = @{}
            }
        }
        catch {
            Write-Host "[INFO] Invoke-RestMethod failed, trying Invoke-WebRequest..." -ForegroundColor Yellow
            
            try {
                # Fallback to WebRequest
                $response = Invoke-WebRequest -Uri $GraphQLUrl -Method Post -Body $jsonBody -Headers $headers -ContentType "application/json" -UseBasicParsing
            }
            catch [System.Net.WebException] {
                # Capture detailed error information
                $errorResponse = $_.Exception.Response
                $statusCode = $errorResponse.StatusCode
                $statusDescription = $errorResponse.StatusDescription
                
                Write-Host ""
                Write-Host "[ERROR] HTTP Error Details:" -ForegroundColor Red
                Write-Host "Status Code: $statusCode" -ForegroundColor Red
                Write-Host "Status Description: $statusDescription" -ForegroundColor Red
                
                # Try to read the error response body
                $errorStream = $errorResponse.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorBody = $reader.ReadToEnd()
                $reader.Close()
                $errorStream.Close()
                
                Write-Host "Error Response Body:" -ForegroundColor Red
                Write-Host $errorBody -ForegroundColor Red
                
                return @{
                    status = "http_error"
                    status_code = [int]$statusCode
                    status_description = $statusDescription
                    error_body = $errorBody
                }
            }
        }
        
        Write-Host ""
        Write-Host "[RESPONSE] Status Code: $($response.StatusCode)" -ForegroundColor Yellow
        Write-Host "Response Headers:" -ForegroundColor Gray
        foreach ($header in $response.Headers.GetEnumerator()) {
            Write-Host "  $($header.Key): $($header.Value)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "Response Body:" -ForegroundColor Gray
        
        if ($response.StatusCode -eq 200) {
            $result = $response.Content | ConvertFrom-Json
            Write-Host ($result | ConvertTo-Json -Depth 10) -ForegroundColor White
            
            # Extract contexts from the query structure
            if ($result.data -and $result.data.accessRequest) {
                $contexts = $result.data.accessRequest.contexts
                
                Write-Host ""
                Write-Host "[SUCCESS] Found $($contexts.Count) contexts for identity" -ForegroundColor Green
                
                Write-Host "[CONTEXTS] Contexts found:" -ForegroundColor Green
                for ($i = 0; $i -lt $contexts.Count; $i++) {
                    $context = $contexts[$i]
                    $name = if ($context.name) { $context.name } else { "N/A" }
                    $id = if ($context.id) { $context.id } else { "N/A" }
                    Write-Host "  $($i + 1). $name (ID: $id)" -ForegroundColor White
                }
                
                return @{
                    status = "success"
                    contexts = $contexts
                    contexts_count = $contexts.Count
                    identity_id = "e3e869c4-369a-476e-a969-d57059d0b1e4"
                }
            } else {
                Write-Host "[WARNING] No contexts found in response" -ForegroundColor Yellow
                return @{
                    status = "no_contexts"
                    response = $result
                }
            }
        } else {
            $errorBody = $response.Content
            Write-Host $errorBody -ForegroundColor Red
            
            return @{
                status = "error"
                status_code = $response.StatusCode
                error = $errorBody
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "[ERROR] Exception occurred: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Exception Type: $($_.Exception.GetType().Name)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "HTTP Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
        
        return @{
            status = "exception"
            error = $_.Exception.Message
            error_type = $_.Exception.GetType().Name
        }
    }
}

# Main execution
function Main {
    try {
        Write-Host "Starting Omada GraphQL Test (PowerShell Version)" -ForegroundColor Cyan
        
        # Load environment variables
        Load-EnvFile
        
        # Get required environment variables
        $tenantId = [Environment]::GetEnvironmentVariable("TENANT_ID", "Process")
        $clientId = [Environment]::GetEnvironmentVariable("CLIENT_ID", "Process")
        $clientSecret = [Environment]::GetEnvironmentVariable("CLIENT_SECRET", "Process")
        $omadaBaseUrl = [Environment]::GetEnvironmentVariable("OMADA_BASE_URL", "Process")
        $oauth2Scope = [Environment]::GetEnvironmentVariable("OAUTH2_SCOPE", "Process")
        
        if (-not $oauth2Scope) {
            $oauth2Scope = "api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default"
        }
        
        # Validate required environment variables
        if (-not ($tenantId -and $clientId -and $clientSecret -and $omadaBaseUrl)) {
            Write-Error "Missing required environment variables: TENANT_ID, CLIENT_ID, CLIENT_SECRET, OMADA_BASE_URL"
            exit 1
        }
        
        Write-Host "[CONFIG] Tenant ID: $tenantId" -ForegroundColor Gray
        Write-Host "[CONFIG] Client ID: $clientId" -ForegroundColor Gray
        Write-Host "[CONFIG] Omada Base URL: $omadaBaseUrl" -ForegroundColor Gray
        Write-Host "[CONFIG] OAuth2 Scope: $oauth2Scope" -ForegroundColor Gray
        Write-Host "[CONFIG] Impersonate User: $ImpersonateUser" -ForegroundColor Gray
        
        # GraphQL endpoint
        $graphqlUrl = "$omadaBaseUrl/api/Domain"
        
        # Get OAuth token
        $accessToken = Get-OAuthToken -TenantId $tenantId -ClientId $clientId -ClientSecret $clientSecret -Scope $oauth2Scope
        
        # Run the test
        $result = Test-GraphQLContexts -AccessToken $accessToken -GraphQLUrl $graphqlUrl -ImpersonateUser $ImpersonateUser
        
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host "TEST SUMMARY" -ForegroundColor Cyan
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host "Status: $($result.status)" -ForegroundColor White
        
        if ($result.status -eq "success") {
            Write-Host "Contexts found: $($result.contexts_count)" -ForegroundColor Green
            Write-Host "Identity ID queried: $($result.identity_id)" -ForegroundColor Green
        } elseif ($result.status -eq "error") {
            Write-Host "HTTP Status: $($result.status_code)" -ForegroundColor Red
        }
        
    }
    catch {
        Write-Host ""
        Write-Host "FATAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Run the main function
Main