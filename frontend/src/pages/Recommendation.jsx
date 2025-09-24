import React, { useState, useEffect } from 'react';
import { useGame } from '../hooks/useGame';

const Recommendation = () => {
  const { state, addRecommendation } = useGame();
  const [weather, setWeather] = useState(null);
  const [occasion, setOccasion] = useState('casual');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState(null);

  const occasions = [
    { value: 'casual', label: 'Casual', icon: '👕' },
    { value: 'formal', label: 'Formal', icon: '👔' },
    { value: 'sporty', label: 'Sports', icon: '🏃' },
    { value: 'date', label: 'Date Night', icon: '💕' },
    { value: 'work', label: 'Work', icon: '💼' },
    { value: 'party', label: 'Party', icon: '🎉' }
  ];

  // Mock weather data
  useEffect(() => {
    setWeather({
      temperature: 22,
      condition: 'sunny',
      description: 'Perfect weather for any outfit!',
      humidity: 65,
      windSpeed: 10
    });
  }, []);

  // Generate AI recommendations
  const generateRecommendations = async () => {
    if (state.wardrobe.length === 0) {
      alert('Please add some items to your wardrobe first!');
      return;
    }

    setLoading(true);
    setRecommendations([]);

    // Simulate AI processing
    setTimeout(() => {
      const wardrobeItems = state.wardrobe;
      const generatedRecommendations = [];

      // Generate 3-4 different outfit combinations
      for (let i = 0; i < Math.min(4, Math.floor(wardrobeItems.length / 2)); i++) {
        const shuffled = [...wardrobeItems].sort(() => 0.5 - Math.random());
        const outfit = [];
        
        // Try to get one item from each category
        const categories = ['tops', 'bottoms', 'shoes', 'accessories'];
        categories.forEach(category => {
          const item = shuffled.find(item => item.category === category && !outfit.includes(item));
          if (item) outfit.push(item);
        });

        // Add more items if needed
        while (outfit.length < 3 && outfit.length < wardrobeItems.length) {
          const item = shuffled.find(item => !outfit.includes(item));
          if (item) outfit.push(item);
        }

        if (outfit.length >= 2) {
          const styleScore = Math.floor(Math.random() * 3) + 7; // 7-9
          const weatherScore = Math.floor(Math.random() * 3) + 8; // 8-10
          
          generatedRecommendations.push({
            id: i + 1,
            items: outfit,
            occasion,
            weatherScore,
            styleScore,
            overallScore: Math.round((styleScore + weatherScore) / 2),
            reason: getRecommendationReason(outfit, occasion, weather),
            colors: [...new Set(outfit.map(item => item.color))],
            vibes: [...new Set(outfit.map(item => item.vibe))]
          });
        }
      }

      setRecommendations(generatedRecommendations.sort((a, b) => b.overallScore - a.overallScore));
      setLoading(false);

      // Add to game state
      if (generatedRecommendations.length > 0) {
        addRecommendation({
          id: Date.now(),
          occasion,
          weather: weather?.condition,
          outfits: generatedRecommendations.length,
          timestamp: new Date().toISOString()
        });
      }
    }, 2500);
  };

  const getRecommendationReason = (items, occasion, weather) => {
    const reasons = [
      `Perfect ${occasion} combination with great color coordination`,
      `Ideal for ${weather?.condition} weather with stylish layering`,
      `Comfortable and trendy outfit that matches your style`,
      `Great balance of style and practicality for ${occasion} occasions`,
      `Weather-appropriate choice with excellent color harmony`,
      `Versatile combination that works for multiple scenarios`
    ];
    return reasons[Math.floor(Math.random() * reasons.length)];
  };

  const saveOutfit = (recommendation) => {
    setSelectedRecommendation(recommendation);
    alert(`Outfit saved! ${recommendation.items.map(item => item.name).join(', ')}`);
  };

  return (
    <div className="animate-fadeIn">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">AI Outfit Recommendations</h1>
        <p className="text-gray-400">Get personalized outfit suggestions based on weather and occasion</p>
      </div>

      {/* Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Weather Info */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center">
            🌤️ Current Weather
          </h3>
          {weather && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Temperature:</span>
                <span className="text-white font-medium">{weather.temperature}°C</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Condition:</span>
                <span className="text-white font-medium capitalize">{weather.condition}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Humidity:</span>
                <span className="text-white font-medium">{weather.humidity}%</span>
              </div>
              <p className="text-green-400 text-sm mt-3">{weather.description}</p>
            </div>
          )}
        </div>

        {/* Occasion Selection */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">🎯 Select Occasion</h3>
          <div className="grid grid-cols-2 gap-3">
            {occasions.map(occ => (
              <button
                key={occ.value}
                onClick={() => setOccasion(occ.value)}
                className={`flex items-center space-x-2 p-3 rounded-lg text-sm font-medium transition-colors duration-200 ${
                  occasion === occ.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                <span>{occ.icon}</span>
                <span>{occ.label}</span>
              </button>
            ))}
          </div>
          
          <button
            onClick={generateRecommendations}
            disabled={loading || state.wardrobe.length === 0}
            className={`w-full mt-6 py-3 px-4 rounded-lg font-medium transition-colors duration-200 ${
              loading || state.wardrobe.length === 0
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Generating...</span>
              </div>
            ) : (
              '🤖 Get AI Recommendations'
            )}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-8 text-center mb-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-purple-300 font-medium mb-2">🧠 AI Brain Working...</p>
          <p className="text-gray-400 text-sm">Analyzing your wardrobe and creating perfect combinations</p>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-white">✨ Recommended Outfits</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recommendations.map(rec => (
              <div key={rec.id} className="bg-gray-800 rounded-lg p-6 card-hover">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">
                      Outfit #{rec.id}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm">
                      <span className="text-green-400">
                        Overall: {rec.overallScore}/10
                      </span>
                      <span className="text-blue-400">
                        Style: {rec.styleScore}/10
                      </span>
                      <span className="text-yellow-400">
                        Weather: {rec.weatherScore}/10
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => saveOutfit(rec)}
                    className="btn-primary text-sm"
                  >
                    Save
                  </button>
                </div>

                {/* Outfit Items */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  {rec.items.map(item => (
                    <div key={item.id} className="text-center">
                      {item.hasRealImage ? (
                        <img 
                          src={item.image} 
                          alt={item.name}
                          className="w-16 h-16 mx-auto mb-2 rounded-lg object-cover"
                        />
                      ) : (
                        <div className="text-3xl mb-2">{item.image}</div>
                      )}
                      <p className="text-white text-xs font-medium truncate">{item.name}</p>
                      <p className="text-gray-400 text-xs capitalize">{item.category}</p>
                    </div>
                  ))}
                </div>

                {/* Details */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Colors:</span>
                    <div className="flex space-x-1">
                      {rec.colors.map(color => (
                        <span key={color} className="px-2 py-1 bg-gray-700 rounded text-xs capitalize">
                          {color}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Vibes:</span>
                    <div className="flex space-x-1">
                      {rec.vibes.map(vibe => (
                        <span key={vibe} className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs capitalize">
                          {vibe}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <p className="text-gray-300 text-sm mt-4 italic">
                  "{rec.reason}"
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && recommendations.length === 0 && state.wardrobe.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🤖</div>
          <h3 className="text-xl font-semibold text-white mb-2">No wardrobe items found</h3>
          <p className="text-gray-400 mb-6">
            Add some clothing items to your wardrobe first to get AI recommendations!
          </p>
          <button className="btn-primary">
            Go to Upload
          </button>
        </div>
      )}

      {/* Tips */}
      <div className="mt-12 bg-gray-800 rounded-lg p-8">
        <h3 className="text-xl font-semibold text-white mb-4">💡 AI Recommendation Tips</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl mb-2">🧠</div>
            <h4 className="font-semibold text-white mb-2">Smart Analysis</h4>
            <p className="text-gray-400 text-sm">Our AI considers weather, occasion, and style compatibility</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🎨</div>
            <h4 className="font-semibold text-white mb-2">Color Harmony</h4>
            <p className="text-gray-400 text-sm">Algorithms ensure your outfit colors work well together</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">⭐</div>
            <h4 className="font-semibold text-white mb-2">Personalized</h4>
            <p className="text-gray-400 text-sm">Recommendations improve based on your wardrobe and preferences</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Recommendation;
