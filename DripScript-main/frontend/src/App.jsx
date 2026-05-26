import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import Wardrobe from './pages/Wardrobe';
import Upload from './pages/Upload';
import Outfits from './pages/Outfits';
import SavedOutfits from './pages/SavedOutfits';
import { GameProvider } from './hooks/useGame';
import './index.css';

function App() {
  return (
    <GameProvider>
      <Router>
        <div className="flex min-h-screen">
          <Navigation />
          <main className="flex-1 ml-64 bg-zinc-50 overflow-y-auto min-h-screen">
            <Routes>
              <Route path="/" element={<Navigate to="/wardrobe" replace />} />
              <Route path="/wardrobe" element={<Wardrobe />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/outfits" element={<Outfits />} />
              <Route path="/saved" element={<SavedOutfits />} />
              <Route path="/recommend" element={<Navigate to="/outfits" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </GameProvider>
  );
}

export default App;
