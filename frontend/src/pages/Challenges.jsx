import React, { useEffect, useMemo, useState } from 'react';

const seedChallenges = [
  { id: 'capsule-7', title: '7‑Day Capsule Wardrobe', desc: 'Create 7 mix‑and‑match outfits from 10 items.', points: 20 },
  { id: 'color-block', title: 'Color Block Day', desc: 'Wear two bold solid colors together.', points: 10 },
  { id: 'accessory-min', title: 'Accessory Minimalist', desc: 'Style an outfit with only one accessory.', points: 10 },
  { id: 'fit-friday', title: 'Fit Friday', desc: 'Dress up a casual look with a sharp layer.', points: 15 },
];

const STORAGE_KEY = 'fitcheck_challenges_v1';

const Challenges = () => {
  const available = useMemo(() => seedChallenges, []);
  const [joined, setJoined] = useState({});

  useEffect(() => {
    try {
      const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
      setJoined(data);
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(joined));
    } catch {}
  }, [joined]);

  const toggleJoin = (id) => {
    setJoined((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), joined: !(prev[id]?.joined) } }));
  };

  const toggleComplete = (id) => {
    setJoined((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), completed: !(prev[id]?.completed) } }));
  };

  const totals = useMemo(() => {
    let active = 0, completed = 0, points = 0;
    available.forEach((c) => {
      if (joined[c.id]?.joined) active += 1;
      if (joined[c.id]?.completed) { completed += 1; points += c.points; }
    });
    return { active, completed, points };
  }, [available, joined]);

  return (
    <div className="animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-6">Challenges</h1>
      <div className="bg-gray-800 rounded-lg p-4 md:p-6 mb-6 grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
        <div className="bg-gray-700 rounded p-4"><div className="text-sm text-gray-400">Active</div><div className="text-2xl text-white font-semibold">{totals.active}</div></div>
        <div className="bg-gray-700 rounded p-4"><div className="text-sm text-gray-400">Completed</div><div className="text-2xl text-white font-semibold">{totals.completed}</div></div>
        <div className="bg-gray-700 rounded p-4"><div className="text-sm text-gray-400">Points</div><div className="text-2xl text-white font-semibold">{totals.points}</div></div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {available.map((c) => {
          const state = joined[c.id] || {};
          return (
            <div key={c.id} className="bg-gray-800 rounded-lg p-5 border border-gray-700">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-semibold text-white">{c.title}</h3>
                <span className="text-sm text-violet-300">+{c.points} pts</span>
              </div>
              <p className="text-gray-400 mb-4">{c.desc}</p>
              <div className="flex gap-2">
                <button onClick={() => toggleJoin(c.id)} className={`px-4 py-2 rounded font-medium transition-colors ${state.joined ? 'bg-gray-600 text-gray-300' : 'bg-violet-600 hover:bg-violet-500 text-white'}`}>
                  {state.joined ? 'Joined' : 'Join'}
                </button>
                <button onClick={() => toggleComplete(c.id)} disabled={!state.joined} className={`px-4 py-2 rounded font-medium transition-colors ${!state.joined ? 'bg-gray-500 text-gray-300 cursor-not-allowed' : state.completed ? 'bg-green-600 hover:bg-green-500 text-white' : 'bg-gray-600 hover:bg-gray-500 text-gray-200'}`}>
                  {state.completed ? 'Completed' : 'Mark Complete'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Challenges;
