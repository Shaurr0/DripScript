import React, { createContext, useContext, useReducer, useEffect } from 'react';

const GameContext = createContext();

const initialState = {
  wardrobe: [],
  savedOutfits: [],
};

const gameReducer = (state, action) => {
  switch (action.type) {
    case 'LOAD_WARDROBE':
      return {
        ...state,
        wardrobe: action.payload,
      };

    case 'LOAD_SAVED_OUTFITS':
      return {
        ...state,
        savedOutfits: action.payload,
      };

    case 'ADD_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: [...state.wardrobe, action.payload],
      };

    case 'REMOVE_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: state.wardrobe.filter((item) => item.id !== action.payload),
      };

    case 'SAVE_OUTFIT':
      return {
        ...state,
        savedOutfits: [...state.savedOutfits, action.payload],
      };

    case 'REMOVE_OUTFIT':
      return {
        ...state,
        savedOutfits: state.savedOutfits.filter((outfit) => outfit.id !== action.payload),
      };

    default:
      return state;
  }
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

export const GameProvider = ({ children }) => {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  useEffect(() => {
    const savedWardrobe = localStorage.getItem('dripscript_wardrobe');
    const savedOutfits = localStorage.getItem('dripscript_saved_outfits');

    if (savedWardrobe) {
      dispatch({ type: 'LOAD_WARDROBE', payload: JSON.parse(savedWardrobe) });
    }
    if (savedOutfits) {
      dispatch({ type: 'LOAD_SAVED_OUTFITS', payload: JSON.parse(savedOutfits) });
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('dripscript_wardrobe', JSON.stringify(state.wardrobe));
  }, [state.wardrobe]);

  useEffect(() => {
    localStorage.setItem('dripscript_saved_outfits', JSON.stringify(state.savedOutfits));
  }, [state.savedOutfits]);

  const actions = {
    addWardrobeItem: (item) => dispatch({ type: 'ADD_WARDROBE_ITEM', payload: item }),
    removeWardrobeItem: (itemId) => dispatch({ type: 'REMOVE_WARDROBE_ITEM', payload: itemId }),
    saveOutfit: (outfit) => dispatch({ type: 'SAVE_OUTFIT', payload: outfit }),
    removeOutfit: (outfitId) => dispatch({ type: 'REMOVE_OUTFIT', payload: outfitId }),
  };

  return (
    <GameContext.Provider value={{ state, ...actions }}>
      {children}
    </GameContext.Provider>
  );
};
