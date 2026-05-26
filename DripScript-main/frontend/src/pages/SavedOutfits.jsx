import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useGame } from '../hooks/useGame';

const SavedOutfits = () => {
  const { state, removeOutfit } = useGame();

  useEffect(() => {
    document.title = 'DripScript • Saved';
  }, []);

  if (state.savedOutfits.length === 0) {
    return (
      <div className="rounded-md border border-gray-100 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold text-gray-900 mb-3">No saved outfits yet</h1>
        <Link
          to="/outfits"
          className="inline-flex rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800"
        >
          Go to Outfits
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold tracking-tight text-gray-900">Saved Outfits</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {state.savedOutfits.map((outfit, index) => (
          <div key={outfit.id || index} className="rounded-md border border-gray-100 bg-white p-8 shadow-sm">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Outfit {index + 1}</h2>
            <ul className="space-y-2 mb-6">
              {(outfit.items || []).map((item, itemIndex) => (
                <li key={`${item.name}-${itemIndex}`} className="text-sm text-gray-900">
                  {item.name}
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => removeOutfit(outfit.id)}
              className="rounded-md border border-gray-200 px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SavedOutfits;
