import React, { useEffect, useState } from 'react';
import { useGame } from '../hooks/useGame';

const Upload = () => {
  const { addWardrobeItem } = useGame();
  const [message, setMessage] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    category: 'tops',
    color: '',
    vibe: 'casual',
    tags: '',
  });
  const [imagePreview, setImagePreview] = useState('');


  useEffect(() => {
    document.title = 'DripScript • Upload';
  }, []);

  const categories = ['tops', 'bottoms', 'shoes', 'accessories'];
  const vibes = ['casual', 'formal', 'sporty', 'trendy', 'vintage'];

  const handleSubmit = (event) => {
    event.preventDefault();
    setMessage(null);

    if (!imagePreview) {
      setMessage({ type: 'error', text: 'Please upload an image first.' });
      return;
    }

    addWardrobeItem({

      id: Date.now(),
      name: formData.name.trim(),
      category: formData.category,
      color: formData.color,
      vibe: formData.vibe,
      tags: formData.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
      image: imagePreview,
      hasRealImage: Boolean(imagePreview),
      dateAdded: new Date().toISOString(),
    });

    setFormData({
      name: '',
      category: 'tops',
      color: '#a8a29e',
      vibe: 'casual',
      tags: '',
    });
    setImagePreview('');
    setMessage({ type: 'success', text: 'Item added to your wardrobe.' });
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Please upload a valid image file.' });
      return;
    }

    const reader = new FileReader();
    reader.onload = async (loadEvent) => {
      const dataUrl = loadEvent.target?.result || '';
      setImagePreview(dataUrl);
      setMessage(null);

      // Strip data URL prefix to send plain base64 to backend
      const base64 = typeof dataUrl === 'string' && dataUrl.includes(',') ? dataUrl.split(',')[1] : '';
      if (!base64) {
        setMessage({ type: 'error', text: 'Could not read image data.' });
        return;
      }

      try {
        setAiLoading(true);
        setMessage({ type: 'success', text: 'AI is analyzing your item...' });

        const response = await fetch('http://localhost:8000/api/classify-clothing', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ image: base64 }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Failed to classify image.');
        }

        setFormData({
          name: data.name || '',
          category: data.category || 'tops',
          color: data.color || '',
          vibe: data.vibe || 'casual',
          tags: Array.isArray(data.tags) ? data.tags.join(', ') : '',
        });

        setMessage({ type: 'success', text: 'Item details updated from AI.' });
      } catch (err) {
        setMessage({ type: 'error', text: err.message || 'AI classification failed.' });
      } finally {
        setAiLoading(false);
      }
    };

    reader.readAsDataURL(file);
  };


  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight text-gray-900">Upload</h1>
      </div>

      <div className="rounded-md border border-gray-100 bg-white p-8 shadow-sm">
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
            <label className="block text-sm font-medium text-gray-900">Image</label>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
            />
            {aiLoading && (
              <div className="mt-3 text-sm text-gray-600">AI is analyzing your item...</div>
            )}
            {imagePreview && (
              <img src={imagePreview} alt="Preview" className="mt-3 h-48 w-full rounded-md object-cover" />
            )}
          </div>


          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
              placeholder="e.g. Black Overshirt"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900">Category</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData((prev) => ({ ...prev, category: e.target.value }))}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
            >
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900">Color</label>
            <input
              type="text"
              value={formData.color}
              onChange={(e) => setFormData((prev) => ({ ...prev, color: e.target.value }))}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
              placeholder="e.g. black"
            />
          </div>


          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900">Vibe</label>
            <select
              value={formData.vibe}
              onChange={(e) => setFormData((prev) => ({ ...prev, vibe: e.target.value }))}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
            >
              {vibes.map((vibe) => (
                <option key={vibe} value={vibe}>
                  {vibe.charAt(0).toUpperCase() + vibe.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-900">Tags</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData((prev) => ({ ...prev, tags: e.target.value }))}
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
              placeholder="minimal, layering, office"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-md bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800"
          >
            Add to Wardrobe
          </button>
        </form>
      </div>
    </div>
  );
};

export default Upload;
