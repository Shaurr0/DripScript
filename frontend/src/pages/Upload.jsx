import React, { useEffect, useRef, useState } from 'react';
import { useGame } from '../hooks/useGame';
import { useAuth } from '../context/AuthContext';
import { uploadWardrobeImage } from '../lib/storageService';
import { apiPostJson, createAbortController } from '../lib/apiClient';
import { checkForDuplicate, precomputeWardrobeHashes } from '../lib/similarity';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const Upload = () => {
  const { state, addWardrobeItem } = useGame();
  const { user } = useAuth();
  const [message, setMessage] = useState(null);
  const [aiStatus, setAiStatus] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [aiMeta, setAiMeta] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: 'tops',
    color: '',
    vibe: 'casual',
    tags: '',
    caption: '',
  });
  const [imagePreview, setImagePreview] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const aiAbortRef = useRef(null);

  useEffect(() => {
    document.title = 'DripScript • Upload';
  }, []);

  useEffect(() => () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
  }, [imagePreview]);

  useEffect(() => {
    return () => {
      if (aiAbortRef.current) aiAbortRef.current.abort();
    };
  }, []);

  useEffect(() => {
    if (state?.wardrobe && state.wardrobe.length > 0) {
      precomputeWardrobeHashes(state.wardrobe);
    }
  }, [state?.wardrobe]);

  const categories = ['tops', 'bottoms', 'dresses', 'shoes', 'accessories'];
  const vibes = ['casual', 'formal', 'sporty', 'trendy', 'vintage'];

  const readFileAsBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const dataUrl = loadEvent.target?.result || '';
      const base64 = typeof dataUrl === 'string' && dataUrl.includes(',') ? dataUrl.split(',')[1] : '';
      if (!base64) {
        reject(new Error('Could not read image data.'));
        return;
      }
      resolve(base64);
    };
    reader.onerror = () => reject(new Error('Could not read image data.'));
    reader.readAsDataURL(file);
  });

  const applySuggestion = (field) => {
    if (!aiSuggestions) return;
    if (field === 'tags') {
      const tagList = Array.isArray(aiSuggestions.tags) ? aiSuggestions.tags : [];
      if (tagList.length === 0) return;
      setFormData((prev) => ({ ...prev, tags: tagList.join(', ') }));
      return;
    }
    const suggestionValue = aiSuggestions[field];
    if (!suggestionValue) return;
    if (field === 'category' && !categories.includes(suggestionValue)) return;
    if (field === 'vibe' && !vibes.includes(suggestionValue)) return;
    setFormData((prev) => ({ ...prev, [field]: suggestionValue }));
  };

  const handleGetAiSuggestions = async () => {
    if (aiLoading) return;

    setAiStatus(null);
    setAiSuggestions(null);
    setAiMeta(null);

    if (!imageFile) {
      setAiStatus({ type: 'error', text: 'Please upload an image first.' });
      return;
    }

    if (!user) {
      setAiStatus({ type: 'error', text: 'Please log in to use AI suggestions.' });
      return;
    }

    if (aiAbortRef.current) aiAbortRef.current.abort();
    const controller = createAbortController();
    aiAbortRef.current = controller;

    try {
      setAiLoading(true);
      const base64 = await readFileAsBase64(imageFile);
      const token = await user.getIdToken();
      const data = await apiPostJson(
        '/api/suggest-clothing',
        { image: base64, filename: imageFile.name },
        { token, signal: controller.signal, timeout: 45000 },
      );

      const suggestions = data.suggestions || {};
      setAiSuggestions(suggestions);
      setAiMeta(data);

      const hasAnySuggestions = Object.values(suggestions).some((value) => (
        Array.isArray(value) ? value.length > 0 : Boolean(value)
      ));

      if (data.low_confidence || !hasAnySuggestions) {
        setAiStatus({
          type: 'info',
          text: data.timed_out
            ? 'AI suggestions timed out. Try again or enter details manually.'
            : 'AI could not confidently suggest details. Please fill them in manually.',
        });
      } else {
        setAiStatus({ type: 'success', text: 'AI suggestions are ready.' });
        if (suggestions.category && categories.includes(suggestions.category)) {
          setFormData((prev) => ({ ...prev, category: suggestions.category }));
        }
      }
    } catch (err) {
      if (err.message !== 'Request was cancelled.') {
        setAiStatus({ type: 'error', text: err.message || 'AI suggestions failed.' });
      }
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (uploading) return;

    setMessage(null);
    setAiStatus(null);

    if (!imagePreview || !imageFile) {
      setMessage({ type: 'error', text: 'Please upload an image first.' });
      return;
    }

    if (!user) {
      setMessage({ type: 'error', text: 'Please log in to upload items.' });
      return;
    }

    try {
      setUploading(true);
      setMessage({ type: 'success', text: 'Checking for duplicates...' });

      const { isDuplicate, hash: imageHash } = await checkForDuplicate(imageFile, state.wardrobe || []);
      if (isDuplicate) {
        setMessage({ type: 'error', text: 'Item already exists in wardrobe' });
        setUploading(false);
        return;
      }

      setMessage({ type: 'success', text: 'Uploading image...' });
      const token = await user.getIdToken();
      const imageUrl = await uploadWardrobeImage(user.uid, imageFile, token);

      await addWardrobeItem({
        name: formData.name.trim(),
        category: formData.category,
        color: formData.color,
        vibe: formData.vibe,
        tags: formData.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
        caption: formData.caption,
        image: imageUrl,
        hasRealImage: Boolean(imageUrl),
        imageHash: imageHash || '',
      });

      setFormData({
        name: '',
        category: 'tops',
        color: '',
        vibe: 'casual',
        tags: '',
        caption: '',
      });
      setImagePreview('');
      setImageFile(null);
      setAiSuggestions(null);
      setAiMeta(null);
      setMessage({ type: 'success', text: 'Item added to your wardrobe.' });
    } catch (err) {
      const code = err?.code || '';
      let errorMessage = err?.message || 'Failed to upload image.';
      if (code === 'permission-denied') {
        errorMessage = 'Permission denied while saving to Firestore. Check Firestore rules for users/{uid}/wardrobe.';
      } else if (code === 'unauthenticated') {
        errorMessage = 'Session expired. Please log in again.';
      }
      setMessage({ type: 'error', text: errorMessage });
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Please upload a valid image file.' });
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setMessage({ type: 'error', text: 'Image must be under 10MB.' });
      return;
    }

    setImageFile(file);
    setMessage(null);
    setAiStatus(null);
    setAiSuggestions(null);
    setAiMeta(null);
    const previewUrl = URL.createObjectURL(file);
    setImagePreview((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return previewUrl;
    });
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Upload</h1>
      </div>

      <div className="rounded-md border border-zinc-100 bg-white p-8 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-6">
          {message && (
            <div
              className={`rounded-md border px-4 py-3 text-sm ${
                message.type === 'success'
                  ? 'border-green-200 bg-green-50 text-green-700'
                  : 'border-red-200 bg-red-50 text-red-700'
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-900">Image</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm"
            />
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                onClick={handleGetAiSuggestions}
                disabled={aiLoading || !imageFile}
                className="rounded-md border border-zinc-200 px-3 py-2 text-sm font-medium text-zinc-900 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {aiLoading ? 'Fetching AI suggestions...' : 'Get AI Suggestions'}
              </button>
              <span className="text-xs text-zinc-500">
                AI suggestions are optional. Review and apply only what looks right.
              </span>
            </div>
            {aiStatus && (
              <div
                className={`rounded-md border px-3 py-2 text-xs ${
                  aiStatus.type === 'success'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : aiStatus.type === 'info'
                      ? 'border-blue-200 bg-blue-50 text-blue-700'
                      : 'border-red-200 bg-red-50 text-red-700'
                }`}
              >
                {aiStatus.text}
                {aiMeta?.confidence ? ` (confidence ${aiMeta.confidence.toFixed(2)})` : ''}
              </div>
            )}
            {aiLoading && (
              <div className="h-1 w-full overflow-hidden rounded-full bg-zinc-100">
                <div className="h-1 w-2/3 animate-pulse rounded-full bg-zinc-400" />
              </div>
            )}
            {imagePreview && (
              <img src={imagePreview} alt="Preview" className="mt-3 h-48 w-full rounded-md object-cover" />
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-900">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm"
              placeholder="e.g. Black Overshirt"
            />
            {aiSuggestions?.name && (
              <div className="flex items-center justify-between text-xs text-zinc-500">
                <span>
                  <span className="font-medium text-zinc-700">AI Suggestion:</span> {aiSuggestions.name}
                </span>
                <button
                  type="button"
                  onClick={() => applySuggestion('name')}
                  className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
                >
                  Use
                </button>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-900">Color</label>
            <input
              type="text"
              value={formData.color}
              onChange={(e) => setFormData((prev) => ({ ...prev, color: e.target.value }))}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm"
              placeholder="e.g. black"
            />
            {aiSuggestions?.color && (
              <div className="flex items-center justify-between text-xs text-zinc-500">
                <span>
                  <span className="font-medium text-zinc-700">AI Suggestion:</span> {aiSuggestions.color}
                </span>
                <button
                  type="button"
                  onClick={() => applySuggestion('color')}
                  className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
                >
                  Use
                </button>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-900">Vibe</label>
            <select
              value={formData.vibe}
              onChange={(e) => setFormData((prev) => ({ ...prev, vibe: e.target.value }))}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm"
            >
              {vibes.map((vibe) => (
                <option key={vibe} value={vibe}>
                  {vibe.charAt(0).toUpperCase() + vibe.slice(1)}
                </option>
              ))}
            </select>
            {aiSuggestions?.vibe && (
              <div className="flex items-center justify-between text-xs text-zinc-500">
                <span>
                  <span className="font-medium text-zinc-700">AI Suggestion:</span>{' '}
                  {aiSuggestions.vibe.charAt(0).toUpperCase() + aiSuggestions.vibe.slice(1)}
                </span>
                <button
                  type="button"
                  onClick={() => applySuggestion('vibe')}
                  className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
                >
                  Use
                </button>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-zinc-900">Tags</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData((prev) => ({ ...prev, tags: e.target.value }))}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm"
              placeholder="minimal, layering, office"
            />
            {Array.isArray(aiSuggestions?.tags) && aiSuggestions.tags.length > 0 && (
              <div className="flex items-center justify-between text-xs text-zinc-500">
                <span>
                  <span className="font-medium text-zinc-700">AI Suggestion:</span>{' '}
                  {aiSuggestions.tags.join(', ')}
                </span>
                <button
                  type="button"
                  onClick={() => applySuggestion('tags')}
                  className="rounded-md border border-zinc-200 px-2 py-1 text-xs text-zinc-700 hover:bg-zinc-50"
                >
                  Use
                </button>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={uploading}
            className="w-full rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {uploading ? 'Uploading...' : 'Add to Wardrobe'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Upload;
