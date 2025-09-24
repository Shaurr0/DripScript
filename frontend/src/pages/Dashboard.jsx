import React from 'react';
import { useGame } from '../hooks/useGame';

const Dashboard = () => {
  const { state } = useGame();

  return (
    <div className="animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-8">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="text-4xl mb-2">⭐</div>
          <h3 className="text-2xl font-bold text-white">{state.totalPoints}</h3>
          <p className="text-gray-400">Total Points</p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="text-4xl mb-2">🏆</div>
          <h3 className="text-2xl font-bold text-white">{state.level}</h3>
          <p className="text-gray-400">Level</p>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <div className="text-4xl mb-2">🏅</div>
          <h3 className="text-2xl font-bold text-white">{state.badges.length}</h3>
          <p className="text-gray-400">Badges Earned</p>
        </div>
      </div>

      {state.badges.length > 0 && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Your Badges</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {state.badges.map(badge => (
              <div key={badge.id} className="flex items-center space-x-3 p-3 bg-gray-700 rounded-lg">
                <span className="text-2xl">{badge.icon}</span>
                <div>
                  <h4 className="font-medium text-white">{badge.name}</h4>
                  <p className="text-gray-400 text-sm">{badge.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;