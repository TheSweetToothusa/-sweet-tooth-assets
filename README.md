# THE SWEET TOOTH - Driver's App

Delivery driver portal for managing local delivery orders from Shopify. Drivers can view orders, navigate to addresses, and capture proof of delivery (photos + signatures).

## Deploy to Render (FREE - Get Live in 5 Minutes)

1. Go to [render.com](https://render.com) and sign up (free)
2. Click **New > Web Service**
3. Connect this GitHub repo: `TheSweetToothusa/-sweet-tooth-assets`
4. Render will auto-detect the `render.yaml` config
5. Add your environment variables:
   - `SHOPIFY_ACCESS_TOKEN` = your Shopify admin API token
   - `GEMINI_API_KEY` = your Google Gemini API key
6. Click **Deploy** — your app will be live at `https://sweet-tooth-driver-app.onrender.com`

## Run Locally

1. `npm install`
2. Create `.env.local` with:
   ```
   SHOPIFY_ACCESS_TOKEN=shpat_your_token_here
   GEMINI_API_KEY=your_gemini_key_here
   ```
3. `npm run dev`
4. Open http://localhost:3000

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SHOPIFY_STORE_URL` | Shopify store domain (default: thesweettoothfl.myshopify.com) |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API access token |
| `GEMINI_API_KEY` | Google Gemini API key for AI features |
