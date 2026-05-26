import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Search, Shirt, Upload, Sparkles, Bookmark } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/wardrobe', label: 'Wardrobe', icon: Shirt },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/outfits', label: 'Outfits', icon: Sparkles },
    { path: '/saved', label: 'Saved', icon: Bookmark },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="fixed top-0 left-0 h-screen w-64 bg-zinc-900 flex flex-col px-5 py-6 z-50">
      <Link to="/wardrobe" className="flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
          <span className="text-zinc-900 font-bold text-sm">DS</span>
        </div>
        <span className="text-white text-lg font-semibold tracking-tight">DripScript</span>
      </Link>

      <div className="relative mb-8">
        <input
          type="text"
          placeholder="Search..."
          className="w-full bg-zinc-800 text-zinc-300 rounded-lg px-4 py-2 text-sm border border-zinc-700/50 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-600"
        />
        <Search size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500" />
      </div>

      <nav className="flex flex-col gap-1">
        {navItems.map(({ path, label, icon: Icon }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
              isActive(path)
                ? 'bg-zinc-200/90 text-zinc-900 font-medium'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Icon size={18} strokeWidth={isActive(path) ? 2 : 1.5} />
            <span>{label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  );
};

export default Navigation;
