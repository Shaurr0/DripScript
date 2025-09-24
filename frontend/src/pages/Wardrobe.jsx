import React, { useState } from 'react';
import { useGame } from '../hooks/useGame';

const Wardrobe = () => {
  const { state, addWardrobeItem } = useGame();
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Demo data function
  const loadDemoData = () => {
    const demoItems = [
      {
        id: Date.now() + 1,
        name: 'Black Hoodie',
        category: 'tops',
        color: 'black',
        vibe: 'casual',
        tags: ['comfortable', 'winter'],
        image: '🖤',
        dateAdded: new Date().toISOString(),
      },
      {
        id: Date.now() + 2,
        name: 'Blue Jeans',
        category: 'bottoms',
        color: 'blue',
        vibe: 'casual',
        tags: ['denim', 'versatile'],
        image: '💙',
        dateAdded: new Date().toISOString(),
      },
      {
        id: Date.now() + 3,
        name: 'White Sneakers',
        category: 'shoes',
        color: 'white',
        vibe: 'sporty',
        tags: ['athletic', 'comfortable'],
        image: '🤍',
        dateAdded: new Date().toISOString(),
      },
      {
        id: Date.now() + 4,
        name: 'Red Dress',
        category: 'dresses',
        color: 'red',
        vibe: 'formal',
        tags: ['elegant', 'dinner'],
        image: '❤️',
        dateAdded: new Date().toISOString(),
      },
      {
        id: Date.now() + 5,
        name: 'Denim Jacket',
        category: 'tops',
        color: 'blue',
        vibe: 'trendy',
        tags: ['layering', 'style'],
        image: '💎',
        dateAdded: new Date().toISOString(),
      }
    ];

    demoItems.forEach(item => addWardrobeItem(item));
  };

  const filteredItems = state.wardrobe.filter(item => {
    const matchesFilter = filter === 'all' || item.category === filter;
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesFilter && matchesSearch;
  });

  const categories = ['all', 'tops', 'bottoms', 'dresses', 'shoes', 'accessories'];

  return (
    <div className="animate-fadeIn">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Your Wardrobe</h1>
        {state.wardrobe.length === 0 && (
          <button
            onClick={loadDemoData}
            className="btn-primary"
          >
            Load Demo Data
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 rounded-lg p-6 card-hover">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">👗</span>
            <div>
              <p className="text-gray-400 text-sm">Total Items</p>
              <p className="text-2xl font-bold text-white">{state.wardrobe.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 card-hover">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🌈</span>
            <div>
              <p className="text-gray-400 text-sm">Colors</p>
              <p className="text-2xl font-bold text-white">
                {new Set(state.wardrobe.map(item => item.color)).size}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 card-hover">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🎭</span>
            <div>
              <p className="text-gray-400 text-sm">Vibes</p>
              <p className="text-2xl font-bold text-white">
                {new Set(state.wardrobe.map(item => item.vibe)).size}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 card-hover">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">🏷️</span>
            <div>
              <p className="text-gray-400 text-sm">Tags</p>
              <p className="text-2xl font-bold text-white">
                {new Set(state.wardrobe.flatMap(item => item.tags)).size}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="flex space-x-2 overflow-x-auto">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setFilter(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors duration-200 ${
                filter === category
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Search by name or tags..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input-primary flex-1"
        />
      </div>

      {/* Items Grid */}
      {filteredItems.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredItems.map(item => (
            <div key={item.id} className="bg-gray-800 rounded-lg p-6 card-hover">
              <div className="text-center mb-4">
                {item.hasRealImage ? (
                  <img 
                    src={item.image} 
                    alt={item.name}
                    className="w-24 h-24 mx-auto mb-2 rounded-lg object-cover"
                  />
                ) : (
                  <div className="text-6xl mb-2">{item.image}</div>
                )}
                <h3 className="text-xl font-semibold text-white">{item.name}</h3>
                <p className="text-gray-400 text-sm capitalize">{item.category}</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Color:</span>
                  <span className="text-white capitalize">{item.color}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">Vibe:</span>
                  <span className="text-white capitalize">{item.vibe}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">
                  {item.tags.map(tag => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-purple-600/20 text-purple-300 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">👗</div>
          <h3 className="text-xl font-semibold text-white mb-2">
            {state.wardrobe.length === 0 ? 'Your wardrobe is empty' : 'No items match your filters'}
          </h3>
          <p className="text-gray-400 mb-6">
            {state.wardrobe.length === 0 
              ? 'Start building your digital wardrobe by uploading your first clothing item!'
              : 'Try adjusting your search or filter criteria.'
            }
          </p>
          {state.wardrobe.length === 0 && (
            <div className="space-x-4">
              <button onClick={loadDemoData} className="btn-primary">
                Load Demo Data
              </button>
              <button className="btn-secondary">
                Upload First Item
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Wardrobe;