import React, { useMemo, useState } from 'react';

const ARTICLES = [
  {
    id: 'capsule-guide',
    title: 'Capsule Wardrobe: The Quickstart Guide',
    category: 'Basics',
    minutes: 4,
    body: `Build a 10–15 item capsule to unlock 30+ outfits. Start with:
    - 2 pants (black, navy)
    - 1 jean
    - 3 tops (white tee, striped knit, button‑down)
    - 1 blazer, 1 light jacket
    - 2 shoes (white sneaker, boot)
    Tip: stick to a cohesive palette so everything pairs.`
  },
  {
    id: 'color-theory',
    title: 'Color Theory for Outfits',
    category: 'Style',
    minutes: 5,
    body: `Use a dominant neutral + one accent. Harmonies:
    - Monochrome: different shades of one color
    - Analogous: neighbors on the color wheel
    - Complementary: opposite colors; keep one muted`
  },
  {
    id: 'fit-checks',
    title: 'Essential Fit Checks',
    category: 'Fit',
    minutes: 3,
    body: `Jackets: shoulder seam ends where your shoulder ends.
    Shirts: 1–2 finger gap at collar; sleeves end at wrist bone.
    Pants: hem breaks once on the shoe; waist sits comfortably.`
  },
];

const categories = ['All', ...Array.from(new Set(ARTICLES.map((a) => a.category)))];

const Content = () => {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState('All');
  const [active, setActive] = useState(ARTICLES[0]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return ARTICLES.filter((a) =>
      (cat === 'All' || a.category === cat) &&
      (q === '' || a.title.toLowerCase().includes(q) || a.body.toLowerCase().includes(q))
    );
  }, [query, cat]);

  return (
    <div className="animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-6">Content</h1>
      <div className="grid gap-6 md:grid-cols-3">
        <aside className="md:col-span-1 space-y-3">
          <div className="bg-gray-800 rounded-lg p-4">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search articles..."
              className="w-full px-3 py-2 rounded bg-gray-700 text-gray-100 placeholder-gray-400 outline-none border border-gray-700 focus:border-violet-500"
            />
            <div className="flex gap-2 flex-wrap mt-3">
              {categories.map((c) => (
                <button
                  key={c}
                  onClick={() => setCat(c)}
                  className={`px-3 py-1 rounded text-sm border transition-colors ${cat === c ? 'bg-violet-600 border-violet-500 text-white' : 'bg-gray-700 border-gray-700 text-gray-200'}`}
                >{c}</button>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-2 divide-y divide-gray-700">
            {filtered.map((a) => (
              <button
                key={a.id}
                onClick={() => setActive(a)}
                className={`w-full text-left p-3 hover:bg-gray-700 transition-colors ${active?.id === a.id ? 'bg-gray-700' : ''}`}
              >
                <div className="text-white font-medium">{a.title}</div>
                <div className="text-gray-400 text-xs mt-1">{a.category} • {a.minutes} min read</div>
              </button>
            ))}
            {filtered.length === 0 && (
              <div className="p-3 text-gray-400 text-sm">No articles match your search.</div>
            )}
          </div>
        </aside>

        <main className="md:col-span-2">
          <div className="bg-gray-800 rounded-lg p-5 border border-gray-700 min-h-[300px]">
            {active ? (
              <article>
                <h2 className="text-2xl font-semibold text-white mb-1">{active.title}</h2>
                <div className="text-gray-400 text-sm mb-4">{active.category} • {active.minutes} min read</div>
                <pre className="whitespace-pre-wrap text-gray-200 leading-relaxed">{active.body}</pre>
              </article>
            ) : (
              <div className="text-gray-400">Select an article to read.</div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Content;
