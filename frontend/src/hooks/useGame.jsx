import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchWardrobeItems,
  addWardrobeItemToFirestore,
  updateWardrobeItemInFirestore,
  deleteWardrobeItemFromFirestore,
  fetchSavedOutfits,
  addSavedOutfitToFirestore,
  updateSavedOutfitInFirestore,
  deleteSavedOutfitFromFirestore,
} from '../lib/wardrobeService';

const GameContext = createContext();
const LOCAL_WARDROBE_KEY = 'dripscript_wardrobe';
const LOCAL_SAVED_OUTFITS_KEY = 'dripscript_saved_outfits';
const RETRY_DELAY = 1500;
const MAX_RETRIES = 2;

async function withRetry(fn, retries = MAX_RETRIES) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      const isRetryable = err?.code === 'unavailable' || err?.code === 'deadline-exceeded';
      if (attempt === retries || !isRetryable) throw err;
      await new Promise((r) => setTimeout(r, RETRY_DELAY * (attempt + 1)));
    }
  }
}

const normalizeItems = (items) => {
  if (!Array.isArray(items)) return [];
  const stamp = Date.now();
  return items
    .filter((item) => item != null && typeof item === 'object')
    .map((item, index) => {
      const safeTags = Array.isArray(item.tags) ? item.tags : [];
      return {
        name: '',
        category: 'tops',
        color: '',
        pattern: 'solid',
        vibe: 'casual',
        caption: '',
        image: '',
        hasRealImage: false,
        imageHash: '',
        ...item,
        id: item.id || `${stamp}-${index}`,
        tags: safeTags,
      };
    });
};

const loadLocalList = (key) => {
  const stored = localStorage.getItem(key);
  if (!stored) return [];
  try {
    return normalizeItems(JSON.parse(stored));
  } catch (err) {
    console.error(`Failed to parse ${key} from localStorage:`, err);
    return [];
  }
};

const initialState = {
  wardrobe: [],
  savedOutfits: [],
  wardrobeLoading: false,
  savedOutfitsLoading: false,
};

const gameReducer = (state, action) => {
  switch (action.type) {
    case 'LOAD_WARDROBE':
      return {
        ...state,
        wardrobe: action.payload,
        wardrobeLoading: false,
      };

    case 'SET_WARDROBE_LOADING':
      return {
        ...state,
        wardrobeLoading: action.payload,
      };

    case 'LOAD_SAVED_OUTFITS':
      return {
        ...state,
        savedOutfits: action.payload,
        savedOutfitsLoading: false,
      };

    case 'ADD_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: [action.payload, ...state.wardrobe],
      };

    case 'REMOVE_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: state.wardrobe.filter((item) => item.id !== action.payload),
      };

    case 'UPDATE_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: state.wardrobe.map((item) => (
          item.id === action.payload.id ? { ...item, ...action.payload } : item
        )),
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

    case 'UPDATE_OUTFIT':
      return {
        ...state,
        savedOutfits: state.savedOutfits.map((outfit) => (
          outfit.id === action.payload.id ? { ...outfit, ...action.payload } : outfit
        )),
      };

    case 'CLEAR_WARDROBE':
      return {
        ...state,
        wardrobe: [],
      };

    case 'CLEAR_SAVED_OUTFITS':
      return {
        ...state,
        savedOutfits: [],
        savedOutfitsLoading: false,
      };

    case 'SET_SAVED_OUTFITS_LOADING':
      return {
        ...state,
        savedOutfitsLoading: action.payload,
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
  const { user } = useAuth();
  const useFirebase = import.meta.env.VITE_USE_FIREBASE === 'true';
  const useCloudPersistence = useFirebase && Boolean(user);

  // Fetch wardrobe from Firestore when user logs in
  useEffect(() => {
    if (!useCloudPersistence) {
      console.warn('[Wardrobe] Using local storage persistence', {
        useFirebase,
        hasUser: Boolean(user),
      });
      dispatch({ type: 'SET_WARDROBE_LOADING', payload: true });
      dispatch({ type: 'LOAD_WARDROBE', payload: loadLocalList(LOCAL_WARDROBE_KEY) });
      return;
    }

    let cancelled = false;

    async function loadWardrobe() {
      dispatch({ type: 'SET_WARDROBE_LOADING', payload: true });
      try {
        const items = await withRetry(() => fetchWardrobeItems(user.uid));
        if (!cancelled) {
          dispatch({ type: 'LOAD_WARDROBE', payload: normalizeItems(items) });
        }
      } catch (err) {
        console.error('[Wardrobe] Failed to fetch wardrobe:', err);
        if (!cancelled) {
          dispatch({ type: 'SET_WARDROBE_LOADING', payload: false });
        }
      }
    }

    loadWardrobe();
    return () => { cancelled = true; };
  }, [useCloudPersistence, user]);

  useEffect(() => {
    if (!useCloudPersistence) {
      console.warn('[Wardrobe] Using local storage for saved outfits', {
        useFirebase,
        hasUser: Boolean(user),
      });
      dispatch({ type: 'SET_SAVED_OUTFITS_LOADING', payload: true });
      dispatch({ type: 'LOAD_SAVED_OUTFITS', payload: loadLocalList(LOCAL_SAVED_OUTFITS_KEY) });
      return;
    }

    let cancelled = false;

    async function loadSavedOutfits() {
      dispatch({ type: 'SET_SAVED_OUTFITS_LOADING', payload: true });
      try {
        const outfits = await withRetry(() => fetchSavedOutfits(user.uid));
        if (!cancelled) {
          dispatch({ type: 'LOAD_SAVED_OUTFITS', payload: outfits });
        }
      } catch (err) {
        console.error('[Wardrobe] Failed to fetch saved outfits:', err);
        if (!cancelled) {
          dispatch({ type: 'CLEAR_SAVED_OUTFITS' });
        }
      }
    }

    loadSavedOutfits();
    return () => { cancelled = true; };
  }, [useCloudPersistence, user]);

  useEffect(() => {
    if (!useCloudPersistence) {
      localStorage.setItem(LOCAL_WARDROBE_KEY, JSON.stringify(state.wardrobe));
    }
  }, [state.wardrobe, useCloudPersistence]);

  useEffect(() => {
    if (!useCloudPersistence) {
      localStorage.setItem(LOCAL_SAVED_OUTFITS_KEY, JSON.stringify(state.savedOutfits));
    }
  }, [state.savedOutfits, useCloudPersistence]);

  const addWardrobeItem = useCallback(async (item) => {
    if (!useCloudPersistence) {
      console.warn('[Wardrobe] Saving item locally because cloud persistence is disabled');
      const localItem = { ...item, id: item.id || `${Date.now()}-${Math.random()}` };
      dispatch({ type: 'ADD_WARDROBE_ITEM', payload: localItem });
      return localItem;
    }

    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      const saved = await addWardrobeItemToFirestore(user.uid, item);
      dispatch({ type: 'ADD_WARDROBE_ITEM', payload: saved });
      return saved;
    } catch (err) {
      console.error('Failed to add wardrobe item:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const removeWardrobeItem = useCallback(async (itemId) => {
    if (!itemId) return;
    dispatch({ type: 'REMOVE_WARDROBE_ITEM', payload: itemId });
    if (!useCloudPersistence) return;
    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      await deleteWardrobeItemFromFirestore(user.uid, itemId);
    } catch (err) {
      console.error('Failed to delete wardrobe item from Firestore:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const updateWardrobeItem = useCallback(async (itemId, updates) => {
    if (!itemId) {
      throw new Error('Missing wardrobe item id.');
    }
    if (!useCloudPersistence) {
      const localItem = { ...updates, id: itemId };
      dispatch({ type: 'UPDATE_WARDROBE_ITEM', payload: localItem });
      return localItem;
    }
    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      const saved = await updateWardrobeItemInFirestore(user.uid, itemId, updates);
      dispatch({ type: 'UPDATE_WARDROBE_ITEM', payload: saved });
      return saved;
    } catch (err) {
      console.error('Failed to update wardrobe item:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const saveOutfit = useCallback(async (outfit) => {
    if (!useCloudPersistence) {
      console.warn('[Wardrobe] Saving outfit locally because cloud persistence is disabled');
      const localOutfit = { ...outfit, id: outfit.id || `${Date.now()}-${Math.random()}` };
      dispatch({ type: 'SAVE_OUTFIT', payload: localOutfit });
      return localOutfit;
    }

    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      const saved = await addSavedOutfitToFirestore(user.uid, outfit);
      dispatch({ type: 'SAVE_OUTFIT', payload: saved });
      return saved;
    } catch (err) {
      console.error('Failed to save outfit:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const removeOutfit = useCallback(async (outfitId) => {
    if (!outfitId) return;
    dispatch({ type: 'REMOVE_OUTFIT', payload: outfitId });
    if (!useCloudPersistence) return;
    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      await deleteSavedOutfitFromFirestore(user.uid, outfitId);
    } catch (err) {
      console.error('Failed to delete saved outfit from Firestore:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const updateOutfit = useCallback(async (outfitId, updates) => {
    if (!outfitId) {
      throw new Error('Missing saved outfit id.');
    }
    if (!useCloudPersistence) {
      const localOutfit = { ...updates, id: outfitId };
      dispatch({ type: 'UPDATE_OUTFIT', payload: localOutfit });
      return localOutfit;
    }
    if (!user) {
      throw new Error('User not authenticated.');
    }
    try {
      const saved = await updateSavedOutfitInFirestore(user.uid, outfitId, updates);
      dispatch({ type: 'UPDATE_OUTFIT', payload: saved });
      return saved;
    } catch (err) {
      console.error('Failed to update saved outfit:', err);
      throw err;
    }
  }, [useCloudPersistence, user]);

  const actions = {
    addWardrobeItem,
    removeWardrobeItem,
    updateWardrobeItem,
    saveOutfit,
    removeOutfit,
    updateOutfit,
  };

  return (
    <GameContext.Provider value={{ state, ...actions }}>
      {children}
    </GameContext.Provider>
  );
};
