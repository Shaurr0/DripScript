import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Bookmark, Sparkles } from 'lucide-react';
import { useGame } from '../hooks/useGame';
import { useAuth } from '../context/AuthContext';
import { apiPostJson, createAbortController } from '../lib/apiClient';
import ItemImage from '../components/ItemImage';
import { getFilenameFromUrl, getHammingDistance } from '../lib/similarity';

const WEATHER_CODE_MAP = {
  0: 'Clear',
  1: 'Mainly clear',
  2: 'Partly cloudy',
  3: 'Overcast',
  45: 'Fog',
  48: 'Fog',
  51: 'Drizzle',
  53: 'Drizzle',
  55: 'Drizzle',
  61: 'Rain',
  63: 'Rain',
  65: 'Rain',
  71: 'Snow',
  73: 'Snow',
  75: 'Snow',
  80: 'Rain showers',
  81: 'Rain showers',
  82: 'Rain showers',
  95: 'Thunderstorm',
};

const STYLE_FILTERS = [
  { key: 'casual', label: 'Casual' },
  { key: 'formal', label: 'Formal' },
  { key: 'streetwear', label: 'Streetwear' },
  { key: 'monochrome', label: 'Monochrome' },
];

const Outfits = () => {
  const { state, saveOutfit } = useGame();
  const { user } = useAuth();
  const [styleFilter, setStyleFilter] = useState('casual');
  const [weather, setWeather] = useState(null);
  const [weatherError, setWeatherError] = useState('');
  const [loadingWeather, setLoadingWeather] = useState(true);
  const [loadingOutfits, setLoadingOutfits] = useState(false);
  const [error, setError] = useState('');
  const [outfits, setOutfits] = useState([]);
  const [savedIds, setSavedIds] = useState(new Set());
  const [savingIds, setSavingIds] = useState(new Set());
  const [warnings, setWarnings] = useState([]);
  const abortRef = useRef(null);

  useEffect(() => {
    document.title = 'DripScript • Outfits';
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setWeatherError('Geolocation not supported.');
      setLoadingWeather(false);
      return;
    }

    const controller = new AbortController();

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const response = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`,
            { signal: controller.signal },
          );
          if (!response.ok) throw new Error('Failed to load weather.');
          const data = await response.json();
          const current = data.current_weather;
          setWeather({
            temperature: current.temperature,
            condition: WEATHER_CODE_MAP[current.weathercode] || 'Unknown',
          });
        } catch (err) {
          if (err.name !== 'AbortError') {
            setWeatherError('Unable to fetch weather.');
          }
        } finally {
          setLoadingWeather(false);
        }
      },
      () => {
        setWeatherError('Location denied.');
        setLoadingWeather(false);
      },
    );

    return () => controller.abort();
  }, []);

  const getDeduplicatedWardrobe = (wardrobe) => {
    const seenFiles = new Set();
    const seenHashes = new Set();
    const seenUrls = new Set();
    const deduplicated = [];

    for (const item of wardrobe) {
      if (item.image) {
        if (seenUrls.has(item.image)) continue;
        seenUrls.add(item.image);

        const filename = getFilenameFromUrl(item.image).toLowerCase();
        if (filename) {
          if (seenFiles.has(filename)) continue;
          seenFiles.add(filename);
        }
      }

      if (item.imageHash) {
        let isDuplicateHash = false;
        for (const seenHash of seenHashes) {
          if (getHammingDistance(item.imageHash, seenHash) <= 8) {
            isDuplicateHash = true;
            break;
          }
        }
        if (isDuplicateHash) continue;
        seenHashes.add(item.imageHash);
      }

      deduplicated.push(item);
    }
    return deduplicated;
  };

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  const generateOutfits = async () => {
    setError('');
    setOutfits([]);
    setWarnings([]);

    const deduplicatedWardrobe = getDeduplicatedWardrobe(state.wardrobe || []);
    if (deduplicatedWardrobe.length === 0) {
      setError('Add wardrobe items first.');
      return;
    }

    if (!user) {
      setError('Please log in to generate outfits.');
      return;
    }

    if (abortRef.current) abortRef.current.abort();
    const controller = createAbortController();
    abortRef.current = controller;

    setLoadingOutfits(true);
    try {
      const token = await user.getIdToken();
      const data = await apiPostJson(
        '/api/recommendations',
        {
          wardrobe: deduplicatedWardrobe,
          occasion: styleFilter,
          weather,
          saved_outfits: (state.savedOutfits || []).map((o) => ({
            items: o.items || [],
            occasion: o.occasion || '',
          })),
        },
        { token, signal: controller.signal, timeout: 60000 },
      );

      setOutfits(Array.isArray(data.outfits) ? data.outfits : []);
      if (Array.isArray(data.warnings) && data.warnings.length > 0) {
        setWarnings(data.warnings);
      }
    } catch (requestError) {
      if (requestError.message !== 'Request was cancelled.') {
        setError(requestError.message);
      }
    } finally {
      setLoadingOutfits(false);
    }
  };

  const handleSave = async (outfit, index) => {
    const id = outfit.id || `${Date.now()}-${index}`;
    if (savedIds.has(id) || savingIds.has(id)) return;

    setError('');
    setSavingIds((prev) => new Set([...prev, id]));
    try {
      const saved = await saveOutfit({ ...outfit, id, occasion: styleFilter });
      const savedId = saved?.id || id;
      setSavedIds((prev) => new Set([...prev, savedId]));
    } catch (saveError) {
      setError(saveError.message || 'Failed to save outfit.');
    } finally {
      setSavingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const wardrobeItemMap = useMemo(() => {
    const map = {};
    state.wardrobe.forEach((item) => {
      if (item.name) map[item.name.toLowerCase()] = item;
    });
    return map;
  }, [state.wardrobe]);

  const getItemImage = (itemName) => {
    if (!itemName) return null;
    const item = wardrobeItemMap[itemName.toLowerCase()];
    return item?.hasRealImage ? item.image : null;
  };

  const getItemColor = (itemName) => {
    if (!itemName) return null;
    const item = wardrobeItemMap[itemName.toLowerCase()];
    return item?.color || null;
  };

  return (
    <div className="min-h-screen bg-zinc-50 px-8 py-10">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">AI Outfits</h1>
          <Link
            to="/saved"
            className="text-sm text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            View Saved
          </Link>
        </div>

        <div className="rounded-xl border border-zinc-200 bg-white p-6 space-y-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-zinc-700 mb-1">Weather</h2>
              {loadingWeather ? (
                <div className="flex items-center gap-2 text-zinc-500 text-sm">
                  <Loader2 size={12} className="animate-spin" />
                  Detecting...
                </div>
              ) : weather ? (
                <p className="text-zinc-900 text-sm">
                  {weather.temperature}°C &middot; {weather.condition}
                </p>
              ) : (
                <p className="text-zinc-500 text-sm">{weatherError}</p>
              )}
            </div>
            <div className="text-right">
              <p className="text-sm text-zinc-500">{state.wardrobe.length} items in wardrobe</p>
            </div>
          </div>

          <div>
            <h2 className="text-sm font-medium text-zinc-700 mb-3">Style</h2>
            <div className="flex flex-wrap gap-2">
              {STYLE_FILTERS.map(({ key, label }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setStyleFilter(key)}
                  className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
                    key === styleFilter
                      ? 'bg-zinc-900 text-white'
                      : 'border border-zinc-300 text-zinc-600 hover:border-zinc-400 hover:text-zinc-800'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="button"
            onClick={generateOutfits}
            disabled={loadingOutfits || state.wardrobe.length === 0}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loadingOutfits ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Sparkles size={14} />
            )}
            Generate Outfits
          </button>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {warnings.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700 space-y-1">
              {warnings.map((w, i) => (
                <p key={i}>{w}</p>
              ))}
            </div>
          )}
        </div>

        {loadingOutfits && (
          <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <Loader2 size={24} className="animate-spin text-zinc-500" />
              <p className="text-sm text-zinc-500">Generating {styleFilter} outfits...</p>
            </div>
          </div>
        )}

        {outfits.length > 0 && (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {outfits.map((outfit, index) => {
              const outfitId = outfit.id || `${Date.now()}-${index}`;
              const isSaved = savedIds.has(outfitId);
              const isSaving = savingIds.has(outfitId);

              return (
                <div
                  key={outfitId}
                  className="rounded-xl border border-zinc-200 bg-white overflow-hidden flex flex-col shadow-sm"
                >
                  <div className="bg-zinc-50 px-5 py-3 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                      Outfit {index + 1}
                    </span>
                    <span className="text-xs text-zinc-400 capitalize">{styleFilter}</span>
                  </div>

                  <div className="px-5 py-4 flex-1 space-y-3">
                    <div className="flex flex-wrap gap-1.5">
                      {(outfit.items || []).map((itemName, i) => {
                        const img = getItemImage(itemName);
                        const color = getItemColor(itemName);
                        return (
                          <div key={`${itemName}-${i}`} className="flex items-center gap-2 w-full">
                            <ItemImage
                              src={img}
                              alt={itemName}
                              fallbackColor={color}
                              className="w-8 h-8 rounded object-cover border border-zinc-200"
                            />
                            <span className="text-sm text-zinc-800">{itemName}</span>
                          </div>
                        );
                      })}
                    </div>

                    {outfit.styling_tip && (
                      <p className="text-xs text-zinc-600 leading-relaxed">
                        <span className="text-zinc-700 font-medium">Tip:</span> {outfit.styling_tip}
                      </p>
                    )}
                    {outfit.color_story && (
                      <p className="text-xs text-zinc-600 leading-relaxed">
                        <span className="text-zinc-700 font-medium">Colors:</span> {outfit.color_story}
                      </p>
                    )}
                    {outfit.why_it_works && (
                      <p className="text-xs text-zinc-600 leading-relaxed">
                        <span className="text-zinc-700 font-medium">Why:</span> {outfit.why_it_works}
                      </p>
                    )}
                  </div>

                  <div className="px-5 py-3 border-t border-zinc-200">
                    <button
                      type="button"
                      onClick={() => { void handleSave(outfit, index); }}
                      disabled={isSaved || isSaving}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                        isSaved
                          ? 'bg-zinc-100 text-zinc-400 cursor-default'
                          : 'bg-zinc-900 text-white hover:bg-zinc-800 disabled:opacity-50'
                      }`}
                    >
                      <Bookmark size={12} fill={isSaved ? 'currentColor' : 'none'} />
                      {isSaving ? 'Saving...' : isSaved ? 'Saved' : 'Save'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!loadingOutfits && outfits.length === 0 && state.wardrobe.length === 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm">
            <p className="text-zinc-600 mb-4">Your wardrobe is empty. Upload items to generate outfits.</p>
            <Link
              to="/upload"
              className="inline-flex rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-zinc-800"
            >
              Upload Items
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Outfits;
