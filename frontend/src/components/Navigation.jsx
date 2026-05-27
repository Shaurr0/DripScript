import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shirt, Upload, Sparkles, Bookmark, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navigation = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [logoutError, setLogoutError] = useState('');

  const navItems = [
    { path: '/wardrobe', label: 'Wardrobe', icon: Shirt },
    { path: '/upload', label: 'Upload', icon: Upload },
    { path: '/outfits', label: 'Outfits', icon: Sparkles },
    { path: '/saved', label: 'Saved', icon: Bookmark },
  ];

  const isActive = (path) => location.pathname === path;

  const handleLogout = async () => {
    setLogoutError('');
    try {
      await logout();
    } catch (err) {
      console.error('Failed to log out:', err);
      setLogoutError('Unable to log out. Please try again.');
    }
  };

  return (
    <aside className="fixed top-0 left-0 h-screen w-64 bg-zinc-900 flex flex-col px-5 py-6 z-50">
      <Link to="/wardrobe" className="flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
          <span className="text-zinc-900 font-bold text-sm">DS</span>
        </div>
        <span className="text-white text-lg font-semibold tracking-tight">DripScript</span>
      </Link>

      <nav className="flex flex-col gap-1 flex-1">
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

      {user && (
        <div className="border-t border-zinc-700/50 pt-4 mt-4">
          <p className="text-zinc-500 text-xs truncate mb-3 px-3">
            {user.displayName || user.email || 'Signed in'}
          </p>
          {logoutError && (
            <p className="text-xs text-red-400 mb-2 px-3">{logoutError}</p>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors w-full"
          >
            <LogOut size={18} strokeWidth={1.5} />
            <span>Logout</span>
          </button>
        </div>
      )}
    </aside>
  );
};

export default Navigation;
