# Railway Deployment Guide for MommyShops Backend

## 🚀 Deploying to Railway

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub

### 2. Connect Repository
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose your `mommyshops` repository

### 3. Configure Environment Variables
In Railway dashboard, go to Variables tab and add:

```
PORT=8001
NVIDIA_API_KEY=your-actual-nvidia-api-key
DATABASE_URL=postgresql://user:password@host:port/database
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=mommyshops
DB_USER=postgres
DB_PASSWORD=your-db-password
API_TIMEOUT=60
MAX_FILE_SIZE=5242880
```

### 4. Deploy
- Railway will automatically detect the Python app
- It will install dependencies from `requirements.txt`
- The app will start with `python main.py`

### 5. Get Backend URL
- After deployment, Railway will provide a URL like:
  `https://your-app-name.railway.app`
- Copy this URL

### 6. Update Frontend
In Streamlit Cloud, add environment variable:
```
API_URL=https://your-app-name.railway.app
```

## 🔧 Database Setup
Railway provides PostgreSQL databases. You can:
1. Add a PostgreSQL service in Railway
2. Use the provided DATABASE_URL
3. Run database migrations

## 📝 Notes
- Railway automatically handles HTTPS
- The app runs on the PORT environment variable
- Health check endpoint: `/health`
- Root endpoint: `/`

## 🐛 Troubleshooting
- Check Railway logs for errors
- Ensure all environment variables are set
- Verify NVIDIA API key is valid
- Check database connection