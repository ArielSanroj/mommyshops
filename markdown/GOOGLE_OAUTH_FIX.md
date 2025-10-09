# 🔧 Google OAuth Redirect URI Fix

## Problem
You're getting the error: **Error 400: redirect_uri_mismatch**

This happens because the redirect URI configured in your Google Cloud Console doesn't match the one your application is trying to use.

## Solution

### 1. Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (the one associated with your Google OAuth credentials)
3. Navigate to **APIs & Services** > **Credentials**
4. Find your OAuth 2.0 Client ID and click on it
5. In the **Authorized redirect URIs** section, add:
   ```
   https://web-production-f23a5.up.railway.app/auth/google/callback
   ```
6. Keep the existing localhost URI for development:
   ```
   http://localhost:8000/auth/google/callback
   ```
7. Click **Save**

### 2. Environment Variables

The following environment variables need to be set in your Railway deployment:

```bash
GOOGLE_REDIRECT_URI=https://web-production-f23a5.up.railway.app/auth/google/callback
RAILWAY_ENVIRONMENT=true
```

### 3. Code Changes Made

✅ **Updated `google_auth_integration.py`**:
- Added dynamic redirect URI detection based on environment
- Production: `https://web-production-f23a5.up.railway.app/auth/google/callback`
- Development: `http://localhost:8000/auth/google/callback`

✅ **Updated `railway.env`**:
- Added `GOOGLE_REDIRECT_URI` for production
- Added `RAILWAY_ENVIRONMENT=true` flag

✅ **Updated `.env.example`**:
- Updated example with production URL

### 4. Deploy Changes

After updating the Google Cloud Console:

1. Commit and push your changes:
   ```bash
   git add .
   git commit -m "Fix Google OAuth redirect URI for production"
   git push origin main
   ```

2. Railway will automatically redeploy your application

### 5. Test the Fix

1. Go to your application: `https://web-production-f23a5.up.railway.app`
2. Try to sign in with Google
3. The OAuth flow should now work correctly

## Troubleshooting

If you still get the error:

1. **Check Google Cloud Console**: Make sure both URIs are added:
   - `http://localhost:8000/auth/google/callback` (for development)
   - `https://web-production-f23a5.up.railway.app/auth/google/callback` (for production)

2. **Check Railway Environment Variables**: Ensure the environment variables are set in your Railway dashboard

3. **Wait for Propagation**: Google's changes can take a few minutes to propagate

4. **Check Logs**: Look at your Railway deployment logs for any errors

## Development vs Production

- **Development**: Uses `http://localhost:8000/auth/google/callback`
- **Production**: Uses `https://web-production-f23a5.up.railway.app/auth/google/callback`

The code automatically detects the environment and uses the appropriate redirect URI.