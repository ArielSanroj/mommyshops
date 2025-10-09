# 🔥 Complete Firebase Setup Guide for MommyShops

## 🚀 Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter project name: `mommyshops` (or your preferred name)
4. Enable Google Analytics (optional)
5. Click "Create project"

## 🔑 Step 2: Generate Service Account Key

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Go to **Service Accounts** tab
3. Click **"Generate new private key"**
4. Download the JSON file
5. **Rename it to:** `firebase-service-account.json`

## 📁 Step 3: Add Service Account File

### For Local Development:
```bash
# Place the file in your project root
cp ~/Downloads/firebase-service-account.json ./firebase-service-account.json
```

### For Railway (Production):
1. Go to Railway dashboard
2. Select your project
3. Go to **Variables** tab
4. Add new variable:
   - **Name:** `FIREBASE_CREDENTIALS`
   - **Value:** Copy the entire JSON content from the service account file

## 🔧 Step 4: Configure Firestore Database

1. In Firebase Console, go to **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in test mode"** (for now)
4. Select a location (choose closest to your users)
5. Click **"Done"**

## 🔒 Step 5: Set Up Security Rules

1. In Firestore Database, go to **Rules** tab
2. Replace the default rules with the content from `firestore.rules` in your project
3. Click **"Publish"**

## 🌐 Step 6: Enable Authentication

1. In Firebase Console, go to **Authentication**
2. Click **"Get started"**
3. Go to **Sign-in method** tab
4. Enable **Email/Password**
5. Enable **Google** (for OAuth)
6. Configure Google OAuth with your redirect URIs:
   - `http://localhost:8000/auth/google/callback` (development)
   - `https://web-production-f23a5.up.railway.app/auth/google/callback` (production)

## 📊 Step 7: Test Firebase Connection

Run this test script to verify Firebase is working:

```python
python3 test_firebase_connection.py
```

## 🔧 Step 8: Environment Variables

### For Local Development (.env):
```bash
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
# OR
FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"your-project-id",...}'
```

### For Railway:
```bash
FIREBASE_CREDENTIALS='{"type":"service_account","project_id":"your-project-id",...}'
RAILWAY_ENVIRONMENT=true
```

## ✅ Step 9: Verify Setup

1. **Check Firebase connection:**
   ```bash
   python3 -c "from firebase_config import is_firebase_available; print('Firebase available:', is_firebase_available())"
   ```

2. **Test user creation:**
   ```bash
   python3 -c "from firebase_config import create_user; print('Test user creation:', create_user({'email': 'test@example.com', 'password': 'test123', 'username': 'testuser'}))"
   ```

## 🚨 Troubleshooting

### Error: "Invalid service account file"
- Make sure the JSON file is valid
- Check that all required fields are present
- Verify the file path is correct

### Error: "Firebase not available"
- Check that credentials are properly set
- Verify the service account has the right permissions
- Make sure Firestore is enabled

### Error: "Permission denied"
- Check Firestore security rules
- Verify the service account has the right roles
- Make sure authentication is enabled

## 📋 Required Firebase Permissions

Your service account needs these roles:
- **Firebase Admin SDK Administrator Service Agent**
- **Cloud Datastore User**
- **Firebase Authentication Admin**

## 🎯 Next Steps

After Firebase is configured:
1. ✅ Test user registration
2. ✅ Test profile saving
3. ✅ Migrate existing user from SQLite
4. ✅ Implement dual write pattern
5. ✅ Test both registration flows

## 📞 Support

If you encounter issues:
1. Check the Firebase Console for error logs
2. Verify all environment variables are set
3. Test with the provided test scripts
4. Check Railway logs for deployment issues