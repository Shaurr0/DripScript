import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Heart, ShoppingBag, X } from 'lucide-react';
import { useGame } from '../hooks/useGame';

const Wardrobe = () => {
  const { state, removeWardrobeItem } = useGame();
  const [filter, setFilter] = useState('all');
  const location = useLocation();

  useEffect(() => {
    document.title = 'DripScript • Wardrobe';
  }, []);

  const categories = ['all', 'tops', 'bottoms', 'shoes', 'accessories'];
  const filteredItems = state.wardrobe.filter((item) => filter === 'all' || item.category === filter);

  const navItems = [
    { path: '/wardrobe', label: 'Wardrobe' },
    { path: '/upload', label: 'Upload' },
    { path: '/outfits', label: 'Outfits' },
    { path: '/saved', label: 'Saved' },
  ];

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="flex items-center gap-8 px-8 h-14">
          {navItems.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`relative text-sm py-4 transition-colors ${
                location.pathname === path
                  ? 'text-zinc-900 font-medium'
                  : 'text-zinc-400 hover:text-zinc-700'
              }`}
            >
              {label}
              {location.pathname === path && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-900 rounded-full" />
              )}
            </Link>
          ))}
        </div>
      </header>

      <div className="px-8 py-6">
        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 mt-8 mb-6">Wardrobe</h1>

        <div className="flex flex-wrap gap-2 mb-8">
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setFilter(category)}
              className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
                filter === category
                  ? 'bg-zinc-600 text-white'
                  : 'border border-zinc-400 text-zinc-700 bg-transparent hover:bg-zinc-100'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        {filteredItems.length > 0 ? (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="group relative bg-white rounded-xl shadow-sm border border-zinc-200/60 overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => removeWardrobeItem(item.id)}
                  className="absolute right-3 top-3 z-10 rounded-md bg-black/40 p-1 text-white opacity-0 transition-opacity hover:bg-black/60 group-hover:opacity-100"
                  aria-label={`Delete ${item.name}`}
                >
                  <X size={14} />
                </button>

                <div className="bg-[#111827] px-4 py-3">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-white">
                    {item.name}
                  </h3>
                  <p className="text-xs text-zinc-400 capitalize mt-0.5">{item.category}</p>
                </div>

                {item.hasRealImage ? (
                  <img src={item.image} alt={item.name} className="h-44 w-full object-cover" />
                ) : (
                  <div className="h-44 w-full" style={{ backgroundColor: item.color || '#d4d4d4' }} />
                )}

                <div className="flex items-center justify-between px-4 py-3 border-t border-zinc-100">
                  <button
                    type="button"
                    className="text-zinc-400 hover:text-zinc-700 transition-colors"
                    aria-label="Like"
                  >
                    <Heart size={18} strokeWidth={1.5} />
                  </button>
                  <button
                    type="button"
                    className="text-zinc-400 hover:text-zinc-700 transition-colors"
                    aria-label="Add to outfit"
                  >
                    <ShoppingBag size={18} strokeWidth={1.5} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-zinc-200/60 bg-white p-12 text-center shadow-sm">
            <h3 className="text-xl font-medium text-zinc-900 mb-4">Your wardrobe is empty</h3>
            <Link
              to="/upload"
              className="inline-flex rounded-full bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-800 transition-colors"
            >
              Upload
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Wardrobe;
