import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useGame } from '../hooks/useGame';

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

const Outfits = () => {
  const { state, saveOutfit } = useGame();
  const [occasion, setOccasion] = useState('casual');
  const [weather, setWeather] = useState(null);
  const [weatherError, setWeatherError] = useState('');
  const [loadingWeather, setLoadingWeather] = useState(true);
  const [loadingOutfits, setLoadingOutfits] = useState(false);
  const [error, setError] = useState('');
  const [outfits, setOutfits] = useState([]);

  const occasions = useMemo(
    () => ['casual', 'formal', 'work', 'party', 'sporty', 'date'],
    [],
  );

  useEffect(() => {
    document.title = 'DripScript • Outfits';
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setWeatherError('Geolocation is not supported in this browser.');
      setLoadingWeather(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const response = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current_weather=true`,
          );
          if (!response.ok) {
            throw new Error('Failed to load weather.');
          }

          const data = await response.json();
          const current = data.current_weather;
          setWeather({
            temperature: current.temperature,
            condition: WEATHER_CODE_MAP[current.weathercode] || 'Unknown',
          });
        } catch (fetchError) {
          setWeatherError('Unable to fetch weather data.');
        } finally {
          setLoadingWeather(false);
        }
      },
      () => {
        setWeatherError('Location permission was denied.');
        setLoadingWeather(false);
      },
    );
  }, []);

  const generateOutfits = async () => {
    setError('');
    setOutfits([]);

    if (state.wardrobe.length === 0) {
      setError('Please add wardrobe items before requesting outfits.');
      return;
    }

    setLoadingOutfits(true);
    try {
      const response = await fetch('http://localhost:8000/api/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wardrobe: state.wardrobe,
          occasion,
          weather,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Could not generate outfits.');
      }
      setOutfits(Array.isArray(data.outfits) ? data.outfits : []);
    } catch (requestError) {
      setError(
        requestError.message.includes('fetch')
          ? 'Backend is unreachable at http://localhost:8000.'
          : requestError.message,
      );
    } finally {
      setLoadingOutfits(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-gray-900">Outfits</h1>
      </div>

      <div className="rounded-md border border-gray-100 bg-white p-8 shadow-sm space-y-6">
        <div>
          <h2 className="text-sm font-medium text-gray-900 mb-2">Current weather</h2>
          {loadingWeather ? (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 size={14} className="animate-spin" />
              Loading weather
            </div>
          ) : weather ? (
            <p className="text-gray-900">
              {weather.temperature}°C • {weather.condition}
            </p>
          ) : (
            <p className="text-gray-500">{weatherError || 'Weather unavailable.'}</p>
          )}
        </div>

        <div>
          <h2 className="text-sm font-medium text-gray-900 mb-3">Occasion</h2>
          <div className="flex flex-wrap gap-2">
            {occasions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setOccasion(option)}
                className={`rounded-md border px-4 py-2 text-sm capitalize ${
                  option === occasion
                    ? 'bg-gray-900 text-white border-gray-900'
                    : 'border-gray-200 text-gray-500 hover:text-gray-900'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={generateOutfits}
          disabled={loadingOutfits}
          className="inline-flex items-center gap-2 rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800 disabled:opacity-70"
        >
          {loadingOutfits && <Loader2 size={14} className="animate-spin" />}
          Generate outfits
        </button>

        {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
      </div>

      {outfits.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {outfits.map((outfit, index) => (
            <div key={outfit.id || index} className="rounded-md border border-gray-100 bg-white p-8 shadow-sm">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Outfit {index + 1}</h3>
              <p className="text-sm text-gray-500 capitalize mb-4">Occasion: {outfit.occasion || occasion}</p>
              <ul className="space-y-2 mb-4">
                {(outfit.items || []).map((item, itemIndex) => (
                  <li key={`${item.name || item}-${itemIndex}`} className="text-sm text-gray-900">
                    {item.name || item}
                  </li>
                ))}
              </ul>

              {outfit.styling_tip && (
                <p className="text-sm text-gray-700 mb-2">
                  <span className="font-medium text-gray-900">Styling tip:</span> {outfit.styling_tip}
                </p>
              )}
              {outfit.color_story && (
                <p className="text-sm text-gray-700 mb-2">
                  <span className="font-medium text-gray-900">Color story:</span> {outfit.color_story}
                </p>
              )}
              {outfit.why_it_works && (
                <p className="text-sm text-gray-700">
                  <span className="font-medium text-gray-900">Why it works:</span> {outfit.why_it_works}
                </p>
              )}
              
              <div className="h-4" />

              <button
                type="button"
                onClick={() => saveOutfit({ ...outfit, id: outfit.id || Date.now() + index })}
                className="rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800"
              >
                Save Outfit
              </button>
            </div>
          ))}
        </div>
      )}

      {!loadingOutfits && outfits.length === 0 && state.wardrobe.length === 0 && (
        <div className="rounded-md border border-gray-100 bg-white p-8 text-center shadow-sm">
          <p className="text-gray-900 mb-4">Your wardrobe is empty.</p>
          <Link to="/upload" className="inline-flex rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white">
            Upload
          </Link>
        </div>
      )}
    </div>
  );
};

export default Outfits;
