import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import Wardrobe from './pages/Wardrobe';
import Upload from './pages/Upload';
import Recommendation from './pages/Recommendation';
import Dashboard from './pages/Dashboard';
import Quiz from './pages/Quiz';
import Challenges from './pages/Challenges';
import Progress from './pages/Progress';
import Content from './pages/Content';
import { GameProvider } from './hooks/useGame';
import './index.css';

function App() {
  return (
    <GameProvider>
      <Router>
        <div className="min-h-screen bg-gray-900">
          <Navigation />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Navigate to="/wardrobe" replace />} />
              <Route path="/wardrobe" element={<Wardrobe />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/recommend" element={<Recommendation />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/quiz" element={<Quiz />} />
              <Route path="/challenges" element={<Challenges />} />
              <Route path="/progress" element={<Progress />} />
              <Route path="/content" element={<Content />} />
            </Routes>
          </main>
        </div>
      </Router>
    </GameProvider>
  );
}

export default App;