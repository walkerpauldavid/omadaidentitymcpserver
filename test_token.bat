@echo off
REM Test Azure OAuth2 token request using curl

echo Testing Azure OAuth2 token request...
echo.

REM Read values from .env file (you may need to adjust these)
set TENANT_ID=542395eb-b6df-4617-af35-11deb659df7b
set CLIENT_ID=08eeb6a4-4aee-406f-baa5-4922993f09f3
set CLIENT_SECRET=2Dv8Q~W9U.k7hQN.4TBPiAzxlOLZM8ZY1JSFtaXO
set OAUTH2_SCOPE=api://08eeb6a4-4aee-406f-baa5-4922993f09f3/.default

set TOKEN_URL=https://login.microsoftonline.com/%TENANT_ID%/oauth2/v2.0/token

echo Making token request to: %TOKEN_URL%
echo Using scope: %OAUTH2_SCOPE%
echo.

curl -X POST "%TOKEN_URL%" ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "grant_type=client_credentials&client_id=%CLIENT_ID%&client_secret=%CLIENT_SECRET%&scope=%OAUTH2_SCOPE%" ^
  --verbose

echo.
echo Done.
pause