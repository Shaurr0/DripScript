import React, { useEffect, useMemo, useState } from 'react';

const getChallengeTotals = () => {
  try {
    const data = JSON.parse(localStorage.getItem('fitcheck_challenges_v1') || '{}');
    const catalog = {
      'capsule-7': 20,
      'color-block': 10,
      'accessory-min': 10,
      'fit-friday': 15,
    };
    let joined = 0, completed = 0, points = 0;
    Object.entries(data).forEach(([id, st]) => {
      if (st.joined) joined += 1;
      if (st.completed) { completed += 1; points += (catalog[id] || 0); }
    });
    return { joined, completed, points };
  } catch {
    return { joined: 0, completed: 0, points: 0 };
  }
};

const getQuizBest = () => {
  try { return Number(localStorage.getItem('quiz_best') || 0); } catch { return 0; }
};

const levelFromXP = (xp) => {
  const level = Math.floor(1 + Math.sqrt(xp / 50)); // simple curve
  const nextLevelXP = (level + 1) ** 2 * 50 - 50;
  const currentLevelXP = level ** 2 * 50 - 50;
  const intoLevel = xp - currentLevelXP;
  const span = Math.max(1, nextLevelXP - currentLevelXP);
  const pct = Math.min(100, Math.round((intoLevel / span) * 100));
  return { level, pct };
};

const Progress = () => {
  const [stats, setStats] = useState({ challenges: { joined: 0, completed: 0, points: 0 }, quizBest: 0, xp: 0 });

  const refresh = () => {
    const challenges = getChallengeTotals();
    const quizBest = getQuizBest();
    const xp = challenges.points * 5 + quizBest * 3; // combine signals
    setStats({ challenges, quizBest, xp });
  };

  useEffect(() => { refresh(); }, []);

  const level = useMemo(() => levelFromXP(stats.xp), [stats.xp]);

  return (
    <div className="animate-fadeIn">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-3xl font-bold text-white">Progress</h1>
        <button onClick={refresh} className="px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm">Refresh</button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-gray-400 text-sm">Level</div>
          <div className="text-2xl font-semibold text-white">{level.level}</div>
          <div className="mt-3 h-2 bg-gray-700 rounded">
            <div className="h-2 bg-violet-600 rounded" style={{ width: `${level.pct}%` }} />
          </div>
          <div className="text-right text-gray-400 text-xs mt-1">{level.pct}%</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-gray-400 text-sm">Quiz Best</div>
          <div className="text-2xl font-semibold text-white">{stats.quizBest}</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-gray-400 text-sm">Challenges Completed</div>
          <div className="text-2xl font-semibold text-white">{stats.challenges.completed}</div>
        </div>

        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-gray-400 text-sm">Challenge Points</div>
          <div className="text-2xl font-semibold text-white">{stats.challenges.points}</div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-5">
        <h2 className="text-xl font-semibold text-white mb-3">Milestones</h2>
        <ul className="grid sm:grid-cols-2 gap-3">
          <li className={`p-3 rounded border ${stats.quizBest >= 3 ? 'bg-green-700/30 border-green-600 text-green-200' : 'bg-gray-700 border-gray-700 text-gray-300'}`}>Score 3/3 on a quiz</li>
          <li className={`p-3 rounded border ${stats.challenges.completed >= 1 ? 'bg-green-700/30 border-green-600 text-green-200' : 'bg-gray-700 border-gray-700 text-gray-300'}`}>Complete your first challenge</li>
          <li className={`p-3 rounded border ${stats.challenges.points >= 30 ? 'bg-green-700/30 border-green-600 text-green-200' : 'bg-gray-700 border-gray-700 text-gray-300'}`}>Earn 30 challenge points</li>
          <li className={`p-3 rounded border ${level.level >= 3 ? 'bg-green-700/30 border-green-600 text-green-200' : 'bg-gray-700 border-gray-700 text-gray-300'}`}>Reach Level 3</li>
        </ul>
      </div>
    </div>
  );
};

export default Progress;
