import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Pencil, Trash2 } from 'lucide-react';
import { useGame } from '../hooks/useGame';
import Modal from '../components/Modal';

const SavedOutfits = () => {
  const { state, removeOutfit, updateOutfit } = useGame();
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [confirmOutfit, setConfirmOutfit] = useState(null);
  const [confirmError, setConfirmError] = useState('');
  const [confirmDeleting, setConfirmDeleting] = useState(false);
  const [renameOutfit, setRenameOutfit] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [renameError, setRenameError] = useState('');
  const [renameSaving, setRenameSaving] = useState(false);

  useEffect(() => {
    document.title = 'DripScript • Saved';
  }, []);

  const handleRemove = async (outfitId) => {
    setError('');
    try {
      await removeOutfit(outfitId);
    } catch (removeError) {
      setError(removeError.message || 'Failed to remove outfit.');
      throw removeError;
    }
  };

  const sortedOutfits = useMemo(() => {
    const outfits = [...state.savedOutfits];
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
      outfits.sort((a, b) => (a.color_story || '').localeCompare(b.color_story || ''));
    } else if (sortBy === 'type') {
      const firstItemName = (outfit) => {
        const first = (outfit.items || [])[0];
        return (typeof first === 'string' ? first : first?.name) || '';
      };
      outfits.sort((a, b) => firstItemName(a).localeCompare(firstItemName(b)));
    } else {
      outfits.sort((a, b) => getTimestampValue(b.timestamp) - getTimestampValue(a.timestamp));
    }
    return outfits;
  }, [sortBy, state.savedOutfits]);

  const openRename = (outfit) => {
    setRenameOutfit(outfit);
    setRenameValue(outfit.name || '');
    setRenameError('');
  };

  const handleRenameSubmit = async (event) => {
    event.preventDefault();
    if (!renameOutfit) return;
    setRenameSaving(true);
    setRenameError('');
    try {
      await updateOutfit(renameOutfit.id, { ...renameOutfit, name: renameValue.trim() });
      setRenameOutfit(null);
      setRenameValue('');
    } catch (err) {
      setRenameError(err.message || 'Failed to rename outfit.');
    } finally {
      setRenameSaving(false);
    }
  };

  if (!state.savedOutfitsLoading && state.savedOutfits.length === 0) {
    return (
      <div className="min-h-screen bg-zinc-50 px-4 py-10 sm:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="rounded-xl border border-zinc-200 bg-white p-12 text-center shadow-sm">
            <h1 className="text-xl font-semibold text-zinc-900 mb-3">No saved outfits yet</h1>
            <p className="text-sm text-zinc-600 mb-6">Generate outfits and save your favorites.</p>
            <Link
              to="/outfits"
              className="inline-flex rounded-lg bg-black px-5 py-2.5 text-sm font-semibold text-white hover:bg-zinc-900"
            >
              Generate Outfits
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 px-4 py-10 sm:px-8">
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Saved Outfits</h1>
            <span className="text-sm text-zinc-500">{state.savedOutfits.length} saved</span>
          </div>
          <select
            value={sortBy}
            onChange={(event) => setSortBy(event.target.value)}
            className="rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm text-zinc-700 shadow-sm"
          >
            <option value="newest">Newest</option>
            <option value="color">Color</option>
            <option value="type">Item Type</option>
          </select>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {state.savedOutfitsLoading ? (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={`saved-skeleton-${index}`} className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm animate-pulse">
                <div className="h-3 w-24 rounded bg-zinc-200 mb-3" />
                <div className="h-4 w-1/2 rounded bg-zinc-100 mb-2" />
                <div className="h-3 w-2/3 rounded bg-zinc-100" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {sortedOutfits.map((outfit, index) => {
              const outfitName = outfit.name?.trim() || `Outfit ${index + 1}`;
              return (
                <div
                  key={outfit.id || index}
                  className="rounded-xl border border-zinc-200 bg-white overflow-hidden flex flex-col shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md"
                >
                  <div className="bg-zinc-50 px-5 py-3 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                        {outfitName}
                      </span>
                      {outfit.occasion && (
                        <div className="text-[11px] text-zinc-400 capitalize mt-1">{outfit.occasion}</div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => openRename(outfit)}
                      className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-600 hover:bg-white"
                    >
                      <Pencil size={12} className="inline-block mr-1" />
                      Rename
                    </button>
                  </div>

                  <div className="px-5 py-4 flex-1 space-y-3">
                    <ul className="space-y-1.5">
                      {(outfit.items || []).map((item, itemIndex) => (
                        <li key={`${item.name || item}-${itemIndex}`} className="text-sm text-zinc-800">
                          {item.name || item}
                        </li>
                      ))}
                    </ul>

                    {outfit.styling_tip && (
                      <p className="text-xs text-zinc-600">
                        <span className="text-zinc-700 font-medium">Tip:</span> {outfit.styling_tip}
                      </p>
                    )}
                    {outfit.color_story && (
                      <p className="text-xs text-zinc-600">
                        <span className="text-zinc-700 font-medium">Colors:</span> {outfit.color_story}
                      </p>
                    )}
                  </div>

                  <div className="px-5 py-3 border-t border-zinc-200">
                    <button
                      type="button"
                      onClick={() => setConfirmOutfit(outfit)}
                      className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-zinc-500 hover:text-red-600 hover:bg-zinc-100 transition-colors"
                    >
                      <Trash2 size={12} />
                      Remove
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <Modal
        isOpen={Boolean(confirmOutfit)}
        title="Delete saved outfit?"
        description="This action cannot be undone."
        onClose={() => {
          setConfirmOutfit(null);
          setConfirmError('');
        }}
      >
        <p className="text-sm text-zinc-600">
          Delete <span className="font-semibold text-zinc-900">{confirmOutfit?.name || 'this outfit'}</span>?
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
              setConfirmOutfit(null);
              setConfirmError('');
            }}
            className="rounded-full border border-zinc-200 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
            disabled={confirmDeleting}
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={confirmDeleting}
            onClick={async () => {
              if (!confirmOutfit || confirmDeleting) return;
              setConfirmDeleting(true);
              try {
                await handleRemove(confirmOutfit.id);
                setConfirmOutfit(null);
              } catch (err) {
                setConfirmError(err.message || 'Failed to delete outfit.');
              } finally {
                setConfirmDeleting(false);
              }
            }}
            className="rounded-full bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-70"
          >
            {confirmDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </Modal>

      <Modal
        isOpen={Boolean(renameOutfit)}
        title="Rename outfit"
        description="Give this outfit a more memorable name."
        onClose={() => {
          if (!renameSaving) {
            setRenameOutfit(null);
            setRenameValue('');
            setRenameError('');
          }
        }}
      >
        <form onSubmit={handleRenameSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-zinc-700">Name</label>
            <input
              type="text"
              value={renameValue}
              onChange={(event) => setRenameValue(event.target.value)}
              placeholder="e.g. Workday Neutral"
              className="mt-1 w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
          {renameError && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
              {renameError}
            </div>
          )}
          <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={() => {
                setRenameOutfit(null);
                setRenameValue('');
                setRenameError('');
              }}
              className="rounded-full border border-zinc-200 px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50"
              disabled={renameSaving}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={renameSaving}
              className="rounded-full bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-70"
            >
              {renameSaving ? 'Saving...' : 'Save name'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default SavedOutfits;
