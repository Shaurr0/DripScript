# FitCheck - Wardrobe AI 🎯

A comprehensive **AI-powered personal stylist** web application with **Google Gemini AI integration**. Upload outfit pictures, get personalized recommendations powered by cutting-edge AI, and track your style journey with gamification elements.

## 🆕 **Latest Updates**
- ✅ **Google Gemini AI Integration** - Real visual analysis of clothing items
- ✅ **Fixed Image Upload** - Seamless drag & drop functionality  
- ✅ **Enhanced Color Detection** - Accurate color recognition from actual images
- ✅ **Smart Fallback System** - Works even when AI is offline
- ✅ **Improved UI/UX** - Better feedback and user experience

## 🚀 Project Structure

```
hackbattle/
├── frontend/          # React + Vite frontend application
├── backend/           # Python backend services and APIs
├── ai-ml/            # AI/ML models and clothing analysis
├── shared/           # Shared utilities and configurations
└── docs/            # Documentation and guides
```

## ✨ Features

### Core Features
- **📸 Upload System** - Drag & drop image upload with auto-color detection
- **👗 Wardrobe Gallery** - Grid view with filtering by category, vibe, and tags
- **🤖 AI Recommendations** - Smart outfit suggestions based on weather, vibe, and wardrobe
- **🌤️ Weather Integration** - Live weather and AQI data for contextual recommendations

### Gamification & Engagement
- **🏆 Points System** - Earn points for uploading, getting recommendations, and completing activities
- **🏅 Badges & Achievements** - Unlock badges for milestones and accomplishments
- **📊 Progress Dashboard** - Track your style journey with detailed analytics
- **🧠 Style Quiz** - Interactive personality quiz to discover your style preferences

## 🛠 Tech Stack

### Frontend
- **React 18** with Hooks and Context API
- **Vite** for fast development and building
- **Tailwind CSS** with custom animations
- **React Router DOM** for navigation
- **Local Storage** for demo persistence

### Backend
- **Python 3.8+** for AI/ML processing
- **Flask** (ready for API integration)
- **Transformers** for NLP (optional)
- **NumPy/Pandas** for data processing

### AI/ML Components
- **Clothing Classification** - NLP-based clothing type detection
- **Style Analysis** - Vibe and formality prediction
- **Weather Integration** - Context-aware recommendations
- **Color Coordination** - Smart color matching algorithms

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+ and pip
- Git
- **Google Gemini API Key** (recommended - free tier available)
- **OpenWeatherMap API Key** (optional - for real weather data)

### 1. Clone and Setup
```bash
git clone https://github.com/Shaurr0/DripScript.git
cd DripScript
```

### 2. API Setup (Required for AI Features)

#### Get Google Gemini API Key (FREE)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key (starts with `AIza...`)

#### Get OpenWeatherMap API Key (Optional)
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Get your API key from the dashboard

#### Configure Environment Variables
```bash
# Backend
cp backend/.env.template backend/.env
# Edit backend/.env and add your API keys

# Frontend
cp frontend/.env.template frontend/.env
# Edit frontend/.env and add your API keys
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`

### 4. Backend Setup (For AI Features)
```bash
cd backend
pip install -r config/requirements.txt
python combined_server.py
```
The AI-powered backend will be available at `http://localhost:5000`

### 4. Load Demo Data
1. Open the frontend application
2. Navigate to the Wardrobe page
3. Click "Load Demo Data" to populate with sample items
4. Explore all features!

## 📱 Application Flow

1. **Start with Wardrobe** - Load demo data and explore the interface
2. **Upload Items** - Add clothing items with drag & drop
3. **Get Recommendations** - AI-powered outfit suggestions
4. **Earn Achievements** - Complete tasks to unlock badges
5. **Track Progress** - View detailed analytics and insights

## 🎮 Gamification System

### Points & Levels
- Upload items: +10 points
- Get recommendations: +5 points
- Complete quiz: +25 points
- Complete challenges: +50 points

### Available Badges
- 🎯 **Getting Started** - Upload your first item
- 👔 **Wardrobe Builder** - Upload 10 items
- 🏆 **Fashion Collector** - Upload 25 items
- 🧠 **Style Explorer** - Complete your first quiz
- ✨ **Style Expert** - Complete 5 quizzes

## 🔧 Development

### Frontend Development
```bash
cd frontend
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Backend Development
```bash
cd backend
python -m pip install -r config/requirements.txt
python api/server.py  # Start development server
```

### AI/ML Development
```bash
cd ai-ml
python clothing_ai.py  # Test AI components
```

## 📁 Key Files

### Frontend
- `frontend/src/App.jsx` - Main React application
- `frontend/src/hooks/useGame.jsx` - Game state management
- `frontend/src/pages/` - Application pages
- `frontend/src/components/` - Reusable components

### Backend
- `backend/config/config.py` - Configuration settings
- `backend/services/` - Weather and environment services
- `ai-ml/clothing_ai.py` - AI clothing analysis

## 🎯 Demo Features

- **Instant Setup** - No backend required for demo
- **Sample Data** - Pre-built clothing items and scenarios
- **Full Functionality** - All features work in demo mode
- **Gamification** - Complete achievement system
- **Responsive Design** - Works on all devices

## 🚀 Deployment

### Frontend (Netlify/Vercel)
```bash
cd frontend
npm run build
# Deploy dist/ folder
```

### Backend (Heroku/Railway)
```bash
cd backend
# Follow platform-specific deployment guides
```

## 🔮 Future Enhancements

- Real image upload and processing
- Advanced AI clothing recognition
- Social sharing and community features
- Shopping integration and price tracking
- AR try-on capabilities
- Mobile app development

## 🏆 Hackathon Ready

- ✅ **Complete MVP** - All core features implemented
- ✅ **Engaging UX** - Gamification and smooth animations  
- ✅ **Modern Tech** - React + Python AI/ML stack
- ✅ **Demo Ready** - Includes sample data and flows
- ✅ **Scalable** - Easy to extend and integrate
- ✅ **Mobile Responsive** - Works on all devices

## 📄 License

Built for hackathon purposes. Feel free to use and modify as needed.

---

**Ready to impress the judges! 🚀**