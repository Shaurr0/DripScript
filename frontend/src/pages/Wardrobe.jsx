import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Pencil, Search, Trash2 } from 'lucide-react';
import { useGame } from '../hooks/useGame';
import { useAuth } from '../context/AuthContext';
import { uploadWardrobeImage } from '../lib/storageService';
import { checkForDuplicate, computeImageHash, precomputeWardrobeHashes } from '../lib/similarity';
import ItemImage from '../components/ItemImage';
import Modal from '../components/Modal';

const formatCardTitle = (item) => {
  const name = (item.name || '').trim();
  const wordCount = name.split(/\s+/).length;
  if (name && wordCount <= 4 && !name.includes(' of ') && !name.includes(' on ')) {
    return name;
  }
  const color = item.color ? item.color.charAt(0).toUpperCase() + item.color.slice(1) : '';
  const category = item.category ? item.category.charAt(0).toUpperCase() + item.category.slice(1) : '';
  if (color && category) return `${color} ${category}`;
  if (color && item.vibe) return `${color} ${item.vibe.charAt(0).toUpperCase() + item.vibe.slice(1)}`;
  if (category) return category;
  return name || 'Stylish Item';
};

const Wardrobe = () => {
  const { state, removeWardrobeItem, updateWardrobeItem } = useGame();
  const { user } = useAuth();
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [confirmItem, setConfirmItem] = useState(null);
  const [confirmError, setConfirmError] = useState('');
  const [confirmDeleting, setConfirmDeleting] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [editImageFile, setEditImageFile] = useState(null);
  const [editError, setEditError] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const location = useLocation();

  useEffect(() => {
    document.title = 'DripScript • Wardrobe';
  }, []);

  useEffect(() => {
    if (state?.wardrobe && state.wardrobe.length > 0) {
      precomputeWardrobeHashes(state.wardrobe);
    }
  }, [state?.wardrobe]);

  const categories = ['all', 'tops', 'bottoms', 'dresses', 'shoes', 'accessories'];
  const filteredItems = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return state.wardrobe.filter((item) => {
      if (filter !== 'all' && item.category !== filter) {
        return false;
      }
      if (!normalizedQuery) {
        return true;
      }
      const tags = Array.isArray(item.tags) ? item.tags.join(' ') : '';
      const haystack = `${item.name || ''} ${item.color || ''} ${item.category || ''} ${tags}`.toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [filter, searchQuery, state.wardrobe]);

  const sortedItems = useMemo(() => {
    const items = [...filteredItems];
    const getTimestampValue = (value) => {
      if (!value) return 0;
      if (typeof value === 'string' || typeof value === 'number') {
        return new Date(value).getTime() || Number(value) || 0;
      }
      if (typeof value.toDate === 'function') {
        return value.toDate().getTime();
      }
      if (typeof value.seconds === 'number') {
        return value.seconds * 1000;
      }
      return 0;
    };

    if (sortBy === 'color') {
      items.sort((a, b) => (a.color || '').localeCompare(b.color || ''));
    } else if (sortBy === 'type') {
      items.sort((a, b) => (a.category || '').localeCompare(b.category || ''));
    } else {
      items.sort((a, b) => getTimestampValue(b.timestamp) - getTimestampValue(a.timestamp));
    }
    return items;
  }, [filteredItems, sortBy]);

  const navItems = [
    { path: '/wardrobe', label: 'Wardrobe' },
    { path: '/upload', label: 'Upload' },
    { path: '/outfits', label: 'Outfits' },
    { path: '/saved', label: 'Saved' },
  ];

  const handleConfirmDelete = async () => {
    if (!confirmItem || confirmDeleting) return;
    setConfirmError('');
    setConfirmDeleting(true);
    try {
      await removeWardrobeItem(confirmItem.id);
      setConfirmItem(null);
    } catch (err) {
      setConfirmError(err.message || 'Failed to delete item.');
    } finally {
      setConfirmDeleting(false);
    }
  };

  const openEditModal = (item) => {
    setEditingItem(item);
    setEditForm({
      name: item.name || '',
      category: item.category || 'tops',
      color: item.color || '',
      vibe: item.vibe || 'casual',
      tags: Array.isArray(item.tags) ? item.tags.join(', ') : '',
      pattern: item.pattern || '',
      caption: item.caption || '',
      image: item.image || '',
      hasRealImage: Boolean(item.hasRealImage),
    });
    setEditImageFile(null);
    setEditError('');
  };

  const handleEditSubmit = async (event) => {
    event.preventDefault();
    if (!editingItem || !editForm) return;
    setEditSaving(true);
    setEditError('');
    try {
      let imageUrl = editForm.image || '';
      let hasRealImage = Boolean(editForm.hasRealImage);
      let imageHash = editingItem.imageHash || '';

      if (editImageFile) {
        if (!user) {
          throw new Error('Please log in to replace the image.');
        }
        // Exclude the current item from duplicate check
        const otherItems = (state.wardrobe || []).filter((item) => item.id !== editingItem.id);
        const { isDuplicate, hash } = await checkForDuplicate(editImageFile, otherItems);
        if (isDuplicate) {
          throw new Error('Item already exists in wardrobe');
        }
        imageHash = hash || '';

        const token = await user.getIdToken();
        imageUrl = await uploadWardrobeImage(user.uid, editImageFile, token);
        hasRealImage = true;
      }

      const updates = {
        name: editForm.name.trim(),
        category: editForm.category,
        color: editForm.color.trim(),
        vibe: editForm.vibe,
        tags: editForm.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
        pattern: editForm.pattern.trim(),
        caption: editForm.caption.trim(),
        image: imageUrl,
        hasRealImage,
        imageHash,
      };
      await updateWardrobeItem(editingItem.id, updates);
      setEditingItem(null);
      setEditForm(null);
      setEditImageFile(null);
    } catch (err) {
      setEditError(err.message || 'Failed to update item.');
    } finally {
      setEditSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="flex items-center gap-6 px-4 sm:px-8 h-14">
          {navItems.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`relative text-sm py-4 transition-colors ${
                location.pathname === path
                  ? 'text-zinc-900 font-medium'
                  : 'text-zinc-400 hover:text-zinc-700'
              }`}
            >
              {label}
              {location.pathname === path && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-zinc-900 rounded-full" />
              )}
            </Link>
          ))}
        </div>
      </header>

      <div className="px-4 pb-10 pt-6 sm:px-8">
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-zinc-900 mt-6 mb-4">Wardrobe</h1>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search by name, color, category, tags"
                className="w-full rounded-full border border-zinc-200 bg-white py-2.5 pl-9 pr-4 text-sm text-zinc-900 shadow-sm transition focus:border-zinc-300 focus:outline-none"
              />
            </div>
            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value)}
              className="rounded-full border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-700 shadow-sm"
            >
              <option value="newest">Newest</option>
              <option value="color">Color</option>
              <option value="type">Item Type</option>
            </select>
          </div>
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category}
                type="button"
                onClick={() => setFilter(category)}
                className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
                  filter === category
                    ? 'bg-zinc-900 text-white'
                    : 'border border-zinc-300 text-zinc-700 bg-white hover:bg-zinc-100'
                }`}
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {state.wardrobeLoading ? (
          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={`skeleton-${index}`}
                className="rounded-2xl border border-zinc-200/60 bg-white p-4 shadow-sm animate-pulse"
              >
                <div className="h-4 w-1/2 rounded bg-zinc-200 mb-3" />
                <div className="h-3 w-1/3 rounded bg-zinc-100 mb-4" />
                <div className="aspect-[4/3] w-full rounded-xl bg-zinc-200" />
              </div>
            ))}
          </div>
        ) : sortedItems.length > 0 ? (
          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {sortedItems.map((item) => (
              <div
                key={item.id}
                className="group relative rounded-2xl border border-zinc-200/60 bg-white shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md"
              >
                <div className="absolute right-3 top-3 z-10 flex items-center gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                  <button
                    type="button"
                    onClick={() => openEditModal(item)}
                    className="rounded-md bg-white/90 p-1.5 text-zinc-600 shadow-sm transition hover:bg-white"
                    aria-label={`Edit ${item.name}`}
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmItem(item)}
                    className="rounded-md bg-white/90 p-1.5 text-zinc-600 shadow-sm transition hover:bg-white"
                    aria-label={`Delete ${item.name}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div className="bg-[#111827] px-4 py-3 rounded-t-2xl">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-white">
                    {formatCardTitle(item)}
                  </h3>
                  <p className="text-xs text-zinc-400 capitalize mt-0.5">{item.category}</p>
                </div>

                <div className="aspect-[4/3] w-full overflow-hidden bg-zinc-100">
                  <ItemImage
                    src={item.hasRealImage ? item.image : null}
                    alt={item.name}
                    fallbackColor={item.color || '#d4d4d4'}
                    className="h-full w-full object-cover"
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-8 rounded-2xl border border-zinc-200/60 bg-white p-10 text-center shadow-sm">
            <h3 className="text-xl font-medium text-zinc-900 mb-3">
              {searchQuery ? 'No matching items' : 'Your wardrobe is empty'}
            </h3>
            <p className="text-sm text-zinc-600 mb-6">
              {searchQuery ? 'Try a different search or clear filters.' : 'Upload your first item to get started.'}
            </p>
            <Link
              to="/upload"
              className="inline-flex rounded-full bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-zinc-800 transition-colors"
            >
              Upload
            </Link>
          </div>
        )}
      </div>

      <Modal
        isOpen={Boolean(confirmItem)}
        title="Delete wardrobe item?"
        description="This action cannot be undone."
        onClose={() => {
          setConfirmItem(null);
          setConfirmError('');
        }}
      >
        <p className="text-sm text-zinc-600">
          Delete <span className="font-semibold text-zinc-900">{confirmItem?.name || 'this item'}</span> from your wardrobe?
        </p>
        {confirmError && (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
            {confirmError}
          </div>
        )}
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={() => {
              setConfirmItem(null);
              setConfirmError('');
            }}
            className="rounded-full border border-zinc-200 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
            disabled={confirmDeleting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirmDelete}
            disabled={confirmDeleting}
            className="rounded-full bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-70"
          >
            {confirmDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={Boolean(editingItem)}
        title="Edit wardrobe item"
        description="Update details or replace the image."
        onClose={() => {
          if (!editSaving) {
            setEditingItem(null);
            setEditForm(null);
            setEditImageFile(null);
            setEditError('');
          }
        }}
      >
        {editForm && (
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-zinc-700">Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, name: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-zinc-700">Category</label>
                <select
                  value={editForm.category}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, category: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                >
                  {categories.filter((cat) => cat !== 'all').map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.charAt(0).toUpperCase() + cat.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-zinc-700">Color</label>
                <input
                  type="text"
                  value={editForm.color}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, color: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-zinc-700">Vibe</label>
                <input
                  type="text"
                  value={editForm.vibe}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, vibe: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-zinc-700">Pattern</label>
                <input
                  type="text"
                  value={editForm.pattern}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, pattern: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-zinc-700">Tags</label>
                <input
                  type="text"
                  value={editForm.tags}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, tags: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                  placeholder="minimal, layering, office"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-zinc-700">Caption</label>
                <textarea
                  rows="2"
                  value={editForm.caption}
                  onChange={(event) => setEditForm((prev) => ({ ...prev, caption: event.target.value }))}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-zinc-700">Replace image</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(event) => setEditImageFile(event.target.files?.[0] || null)}
                  className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                />
                {editImageFile && (
                  <p className="mt-2 text-xs text-zinc-500">New image selected: {editImageFile.name}</p>
                )}
                {editForm.image && !editImageFile && (
                  <div className="mt-3 flex items-center gap-3">
                    <img
                      src={editForm.image}
                      alt={editForm.name || 'Preview'}
                      className="h-16 w-16 rounded-lg object-cover"
                    />
                    <button
                      type="button"
                      onClick={() => setEditForm((prev) => ({ ...prev, image: '', hasRealImage: false }))}
                      className="rounded-full border border-zinc-200 px-3 py-1 text-xs text-zinc-600 hover:bg-zinc-50"
                    >
                      Remove image
                    </button>
                  </div>
                )}
              </div>
            </div>
            {editError && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                {editError}
              </div>
            )}
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => {
                  setEditingItem(null);
                  setEditForm(null);
                  setEditImageFile(null);
                  setEditError('');
                }}
                className="rounded-full border border-zinc-200 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
                disabled={editSaving}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={editSaving}
                className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-70"
              >
                {editSaving ? 'Saving...' : 'Save changes'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default Wardrobe;
