import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useGame } from '../hooks/useGame';

const Navigation = () => {
  const location = useLocation();
  const { state } = useGame();

  const navItems = [
    { path: '/wardrobe', label: 'Wardrobe', icon: '👗' },
    { path: '/upload', label: 'Upload', icon: '📸' },
    { path: '/recommend', label: 'Recommend', icon: '🤖' },
    { path: '/dashboard', label: 'Dashboard', icon: '🏆' },
    { path: '/quiz', label: 'Quiz', icon: '🧠' },
    { path: '/challenges', label: 'Challenges', icon: '🎯' },
    { path: '/progress', label: 'Progress', icon: '📊' },
    { path: '/content', label: 'Content', icon: '💡' },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-gray-800 shadow-lg border-b border-gray-700">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          {/* Logo */}
          <Link to="/wardrobe" className="flex items-center space-x-2">
            <span className="text-2xl">🎯</span>
            <span className="text-xl font-bold text-white">FitCheck</span>
          </Link>

          {/* Navigation Items */}
          <div className="flex space-x-1 overflow-x-auto">
            {navItems.map(({ path, label, icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 whitespace-nowrap ${
                  isActive(path)
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                <span>{icon}</span>
                <span>{label}</span>
              </Link>
            ))}
          </div>

          {/* User Stats */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-white">
              <span className="text-yellow-400">⭐</span>
              <span className="font-semibold">{state.totalPoints}</span>
            </div>
            <div className="flex items-center space-x-2 text-white">
              <span className="text-purple-400">🏅</span>
              <span className="font-semibold">{state.badges.length}</span>
            </div>
            <div className="text-sm text-gray-300">
              Level {state.level}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;