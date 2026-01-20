# Environment Configuration Guide

## 📝 Your .env.local File Setup

### For LOCAL TESTING (Current Setup)
Update your `.env.local` file to use the local backend:

```bash
# Firebase Configuration (keep as is)
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyB44Biuftgu8QSjmNiw4m2cIdZeAKr965s
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=buisness-cyberimpact.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=buisness-cyberimpact
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=buisness-cyberimpact.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=641113058962
NEXT_PUBLIC_FIREBASE_APP_ID=1:641113058962:web:64b7164292824c3d45c04b

# Backend API URL - FOR LOCAL TESTING
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### For PRODUCTION DEPLOYMENT
When deploying to Vercel, set this environment variable in Vercel dashboard:

```bash
NEXT_PUBLIC_API_URL=https://cyberimpact-frontend.onrender.com
```

---

## 🚀 Quick Setup Steps

### 1. Update Your Local .env.local
Change line 10 in your `.env.local` from:
```bash
NEXT_PUBLIC_API_URL=https://cyberimpact-frontend.onrender.com
```

To:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Restart Your Frontend Dev Server
```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
```

### 3. For Vercel Deployment
Go to your Vercel project → Settings → Environment Variables → Add:
- **Key**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://cyberimpact-frontend.onrender.com`
- **Environment**: Production

---

## ✅ What's Already Configured

### Backend CORS (main.py)
Your backend already accepts requests from:
- ✅ `http://localhost:3000` - Your local frontend
- ✅ `https://cyberimpact-frontend.onrender.com` - Production frontend (Render)
- ✅ `https://cyberimpact-frontend-obya.vercel.app` - Production frontend (Vercel)
- ✅ `http://localhost:8000` - Local backend

### Frontend API Config (src/config/api.ts)
Created centralized API configuration that reads from `NEXT_PUBLIC_API_URL`

---

## 🧪 Testing

### Local Testing
1. Make sure `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
2. Run backend: `uvicorn main:app --reload --port 8000`
3. Run frontend: `npm run dev`
4. Open `http://localhost:3000`

### Production Testing
1. Deploy backend to Render (already done ✅)
2. Deploy frontend to Vercel with `NEXT_PUBLIC_API_URL=https://cyberimpact-frontend.onrender.com`
3. Open your Vercel URL

---

## 🔧 Current Status

- ✅ Backend CORS configured
- ✅ Backend deployed to Render
- ✅ Frontend API config created
- ⏳ Need to update `.env.local` for local testing
- ⏳ Need to set Vercel environment variable for production
