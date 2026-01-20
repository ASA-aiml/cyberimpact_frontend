# CORS and Deployment Configuration

## ✅ Backend CORS Configuration

The backend (`main.py`) is now configured to accept requests from:

- ✅ `http://localhost:3000` - Local frontend development
- ✅ `https://cyberimpact-frontend.onrender.com` - Production frontend (Render)
- ✅ `https://cyberimpact-frontend-obya.vercel.app` - Production frontend (Vercel)
- ✅ `http://localhost:8000` - Local backend

**No additional backend changes needed!** The CORS middleware will automatically allow requests from these origins.

---

## 🔧 Frontend Configuration

### Option 1: Using the API Config File (Recommended)

I've created `src/config/api.ts` with centralized API endpoints. To use it:

1. **Update your components** to import from the config:
   ```typescript
   import { API_ENDPOINTS } from '@/config/api';
   
   // Instead of: "http://localhost:8000/scan/analyze"
   // Use: API_ENDPOINTS.scanAnalyze
   ```

2. **Set environment variable for production:**
   
   **For Vercel:**
   - Go to your project settings
   - Add environment variable: `NEXT_PUBLIC_API_URL`
   - Value: Your production backend URL (e.g., `https://your-backend.onrender.com`)
   
   **For Render:**
   - Go to your web service settings
   - Add environment variable: `NEXT_PUBLIC_API_URL`
   - Value: Your production backend URL

3. **For local development:**
   - No changes needed! It defaults to `http://localhost:8000`

### Option 2: Manual Update (Quick Fix)

If you want to quickly test with production backend, you can:

1. Find and replace in your components:
   ```
   Find: "http://localhost:8000"
   Replace with: "https://your-backend-url.com"
   ```

2. Files to update:
   - `src/app/page.tsx`
   - `src/components/Login.tsx`
   - `src/components/AssetInventoryUpload.tsx`
   - `src/components/FinancialDocUpload.tsx`

---

## 📝 Deployment Checklist

### Backend Deployment (Render/Railway/etc.)

- [x] CORS configured with production frontend URLs
- [ ] Set environment variables:
  - `MONGODB_URI` - Your MongoDB connection string
  - `FIREBASE_CREDENTIALS_JSON` - Firebase service account JSON
  - `GEMINI_API_KEY` - Google Gemini API key
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend Deployment (Vercel/Netlify/etc.)

- [ ] Set `NEXT_PUBLIC_API_URL` environment variable to your backend URL
- [ ] Update Firebase config if needed
- [ ] Build command: `npm run build`
- [ ] Deploy!

---

## 🧪 Testing CORS

After deployment, test CORS by:

1. Open browser console on your production frontend
2. Try making an API call
3. Check for CORS errors in console
4. If you see CORS errors, verify:
   - Backend CORS origins include your frontend URL
   - Frontend is using correct backend URL
   - Both URLs use HTTPS in production (not mixing HTTP/HTTPS)

---

## 🔒 Security Notes

- The backend requires Firebase authentication for most endpoints
- Make sure Firebase credentials are properly configured in production
- Never commit `.env` files with secrets to git
- Use environment variables for all sensitive data

---

## 📚 Environment Variables Reference

### Backend (.env)
```bash
MONGODB_URI=mongodb+srv://...
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}
GEMINI_API_KEY=your_key_here
DATABASE_NAME=cyberimpact_db
MAX_FILE_SIZE=10485760
```

### Frontend (Vercel/Render Environment Variables)
```bash
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
# ... other Firebase config
```

---

## ✅ Current Status

- ✅ Backend CORS configured for all origins
- ✅ API config file created for frontend
- ⏳ Frontend components need to be updated to use API config (optional but recommended)
- ⏳ Environment variables need to be set in production deployments
