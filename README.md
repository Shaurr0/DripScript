# DripScript
A wardrobe management and outfit recommendation tool. Upload your clothes, let the AI figure out what they are, and get outfit suggestions based on weather and occasion.

## What it does
- Upload clothing images and get them auto-tagged (category, color, style)
- Build a digital wardrobe from your uploads
- Get outfit recommendations that factor in weather and occasion
- Save outfits you like for later

## Tech Stack

**Frontend** — React 18, Vite, Tailwind CSS, shadcn/ui, Framer Motion

**Backend** — Python 3, Flask, Flask-CORS

**AI** — Cohere API (command-r-plus model) for clothing classification and outfit recommendations

**Weather** — OpenWeatherMap API (optional, falls back to mock data if not configured)

**Storage** — Firebase for cloud persistence (optional), local state by default

## Project Structure

DripScript/
├── frontend/
│   ├── src/
│   │   ├── pages/          # Upload, Wardrobe, Outfits, SavedOutfits
│   │   ├── components/     # Navigation, shadcn UI components
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/            # Firebase config, utilities
│   └── public/
├── backend/
│   ├── combined_server.py  # Flask API entry point
│   ├── services/
│   │   └── ai_service.py   # Cohere integration, weather, recommendations
│   └── config/
│       ├── config.py
│       └── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.9+
- A Cohere API key (free tier works)

### Backend

cd backend
pip install -r config/requirements.txt


Create `backend/.env`:

COHERE_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here   # optional


Start the server:

python combined_server.py

The API runs on `http://localhost:5000`.

### Frontend
cd frontend
npm install
npm run dev


Opens on `http://localhost:5173`. Make sure the backend is running first.

## API Endpoints

**GET /api/health**
Returns service status and whether the Cohere API key is configured.

**POST /api/classify-clothing**
Accepts a clothing image upload. Returns the detected category, color, style, and tags.

**POST /api/recommendations**
Takes the user's wardrobe, current weather, and occasion as input. Returns styled outfit suggestions with styling notes.

## How the AI works

The backend sends structured prompts to Cohere's `command-r-plus` model. Since Cohere doesn't support vision, clothing classification relies on filename inference combined with text-based analysis. If the API key isn't configured or a request fails, the system falls back to rule-based heuristics (filename parsing, keyword matching) so the app still functions without an API key.

Outfit recommendations take the full wardrobe, current weather, and selected occasion as context, then ask the model to assemble coordinated outfits with styling notes.

## Configuration

Both `frontend/.env.template` and `backend/.env.template` document the available environment variables. Copy them to `.env` and fill in your keys.

Firebase is optional and disabled by default. Set `VITE_USE_FIREBASE=true` in the frontend `.env` if you want cloud persistence.