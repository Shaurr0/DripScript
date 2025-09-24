import React, { useState, useRef, useCallback } from 'react';
import { useGame } from '../hooks/useGame';

const Upload = () => {
  const { addWardrobeItem } = useGame();
  const [formData, setFormData] = useState({
    name: '',
    category: 'tops',
    color: '',
    vibe: 'casual',
    tags: '',
  });
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [aiScanning, setAiScanning] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const categories = ['tops', 'bottoms', 'dresses', 'shoes', 'accessories'];
  const vibes = ['casual', 'formal', 'sporty', 'trendy', 'vintage'];
  
  // Color to emoji mapping
  const colorEmojis = {
    black: '🖤',
    white: '🤍',
    red: '❤️',
    blue: '💙',
    green: '💚',
    yellow: '💛',
    purple: '💜',
    orange: '🧡',
    pink: '💗',
    brown: '🤎',
    gray: '🩶',
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const newItem = {
      id: Date.now(),
      name: formData.name,
      category: formData.category,
      color: formData.color,
      vibe: formData.vibe,
      tags: formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag),
      image: imagePreview || colorEmojis[formData.color] || '👕',
      hasRealImage: !!imagePreview,
      dateAdded: new Date().toISOString(),
    };

    addWardrobeItem(newItem);
    
    // Reset form
    setFormData({
      name: '',
      category: 'tops',
      color: '',
      vibe: 'casual',
      tags: '',
    });
    setImagePreview(null);
    setUploadedImage(null);
    setAiSuggestions(null);

    // Show success message
    alert('Item added to wardrobe! 🎉');
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Handle file upload - SIMPLIFIED WITHOUT FIREBASE
  const handleFileUpload = useCallback((files) => {
    if (files && files[0]) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        setUploadedImage(file);
        
        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataUrl = e.target.result;
          setImagePreview(dataUrl);
          // Always analyze using data URL pixels for best accuracy
          performAIAnalysis(file.name, dataUrl);
        };
        reader.readAsDataURL(file);
      } else {
        alert('Please upload an image file (JPG, PNG, etc.)');
      }
    }
  }, []);

  // Estimate dominant color from image using canvas (simple hue-based mapping)
  const detectDominantColor = (dataUrl) => new Promise((resolve) => {
    try {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        const w = 64, h = 64;
        canvas.width = w; canvas.height = h;
        ctx.drawImage(img, 0, 0, w, h);
        const { data } = ctx.getImageData(0, 0, w, h);
        let rSum = 0, gSum = 0, bSum = 0, count = 0;
        for (let i = 0; i < data.length; i += 4) {
          const a = data[i+3];
          if (a < 10) continue; // skip transparent
          const r = data[i], g = data[i+1], b = data[i+2];
          // skip near-white background pixels
          if (r > 240 && g > 240 && b > 240) continue;
          rSum += r; gSum += g; bSum += b; count++;
        }
        if (!count) return resolve('gray');
        const r = rSum / count, g = gSum / count, b = bSum / count;
        // Convert to HSL for hue bucketing
        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        let hue;
        if (max === min) hue = 0;
        else if (max === r) hue = (60 * ((g - b) / (max - min)) + 360) % 360;
        else if (max === g) hue = 60 * ((b - r) / (max - min)) + 120;
        else hue = 60 * ((r - g) / (max - min)) + 240;
        const l = (max + min) / 510; // 0-1
        const s = max === min ? 0 : (max - min) / (1 - Math.abs(2*l - 1)) / 255;
        // Map hue to our palette
        const pick = () => {
          if (l > 0.85) return 'white';
          if (l < 0.15) return 'black';
          if (s < 0.12) return 'gray';
          if (hue >= 20 && hue < 45) return 'orange';
          if (hue >= 45 && hue < 70) return 'yellow';
          if (hue >= 70 && hue < 170) return 'green';
          if (hue >= 170 && hue < 200) return 'cyan';
          if (hue >= 200 && hue < 255) return 'blue';
          if (hue >= 255 && hue < 290) return 'purple';
          if (hue >= 290 && hue < 330) return 'pink';
          if ((hue >= 330 && hue <= 360) || (hue >= 0 && hue < 20)) return 'red';
          return 'gray';
        };
        let color = pick();
        // Normalize cyan -> blue for our allowed set
        if (color === 'cyan') color = 'blue';
        resolve(color);
      };
      img.onerror = () => resolve('gray');
      img.src = dataUrl;
    } catch {
      resolve('gray');
    }
  });

  // Real AI Analysis using Gemini API
  const performAIAnalysis = async (fileName, dataUrl) => {
    setAiScanning(true);
    setAiSuggestions(null);

    try {
      console.log('🔍 Starting AI Analysis:', fileName);
      
      // Use the AI analyze endpoint that supports Gemini vision
      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/api/ai/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: fileName,
          // Send the full data URL; backend will strip the prefix if needed
          image_data: dataUrl || ''
        })
      });

      console.log('🌐 API Response Status:', response.status);

      if (response.ok) {
        const result = await response.json();
        console.log('📝 API Response:', result);
        
        // Backend returns { success, analysis }
        if (result.success && result.analysis) {
          // Map the AI response to our frontend format
          const aiAnalysis = result.analysis;
          let mappedColor = (aiAnalysis.color || '').toString().toLowerCase();
          if (!mappedColor || mappedColor === 'unknown') {
            mappedColor = await detectDominantColor(dataUrl);
          }
          // If filename has a strong color hint, prefer it
          const fileLower = (fileName || '').toLowerCase();
          const nameColorHints = [
            'yellow','gold','mustard','blue','navy','red','green','black','white','purple','orange','pink','brown','gray','grey'
          ];
          const hint = nameColorHints.find(c => fileLower.includes(c));
          if (hint) mappedColor = hint === 'grey' ? 'gray' : (hint === 'navy' ? 'blue' : hint);

          const suggestions = {
            name: aiAnalysis.name || (fileName ? fileName.replace(/\.[^/.]+$/, "").replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Stylish Item'),
            category: aiAnalysis.category || 'accessories',
            color: mappedColor || 'gray',
            vibe: Array.isArray(aiAnalysis.style) ? aiAnalysis.style[0] : (aiAnalysis.style || 'casual'),
            tags: aiAnalysis.occasions || aiAnalysis.occasion || ['comfortable', 'versatile', 'everyday']
          };

          setAiSuggestions(suggestions);
          console.log('✅ Gemini AI Analysis Success:', suggestions);
        } else {
          throw new Error('Invalid AI response format');
        }
      } else {
        throw new Error(`API request failed: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ AI Analysis Error:', error);
      
      // Fallback to basic analysis if AI fails
      const detected = await detectDominantColor(dataUrl);
      const fallbackSuggestions = {
        name: fileName.replace(/\.[^/.]+$/, "").replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Stylish Item',
        category: fileName.toLowerCase().includes('shirt') ? 'tops' :
                 fileName.toLowerCase().includes('jean') ? 'bottoms' :
                 fileName.toLowerCase().includes('dress') ? 'dresses' :
                 fileName.toLowerCase().includes('shoe') ? 'shoes' : 'accessories',
        color: detected || 'gray',
        vibe: 'casual',
        tags: ['comfortable', 'versatile']
      };
      
      setAiSuggestions(fallbackSuggestions);
      console.log('⚠️ Using fallback analysis:', fallbackSuggestions);
    } finally {
      setAiScanning(false);
    }
  };

  // Apply AI suggestions
  const applyAISuggestions = () => {
    if (aiSuggestions) {
      setFormData({
        name: aiSuggestions.name,
        category: aiSuggestions.category,
        color: aiSuggestions.color,
        vibe: aiSuggestions.vibe,
        tags: Array.isArray(aiSuggestions.tags) ? aiSuggestions.tags.join(', ') : aiSuggestions.tags
      });
    }
  };

  // Drag and drop handlers
  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  }, [handleFileUpload]);

  return (
    <div className="animate-fadeIn">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Upload New Item</h1>
        <p className="text-gray-400">Add a new clothing item to your digital wardrobe</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* AI Upload Section */}
        <div className="space-y-6">
          {/* Drag and Drop Upload Area */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 cursor-pointer ${
              dragActive
                ? 'border-purple-500 bg-purple-500/10'
                : 'border-gray-600 hover:border-purple-500 hover:bg-purple-500/5'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={(e) => handleFileUpload(e.target.files)}
              className="hidden"
            />
            
            {imagePreview ? (
              <div className="space-y-4">
                <img
                  src={imagePreview}
                  alt="Uploaded item"
                  className="mx-auto max-h-48 rounded-lg object-contain"
                />
                <p className="text-white font-medium">Image uploaded successfully!</p>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setImagePreview(null);
                    setUploadedImage(null);
                    setAiSuggestions(null);
                  }}
                  className="btn-secondary"
                >
                  Upload Different Image
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-6xl mb-4">📸</div>
                <div>
                  <p className="text-xl font-semibold text-white mb-2">
                    Drop your clothing image here
                  </p>
                  <p className="text-gray-400 mb-4">
                    or click to browse files
                  </p>
                  <div className="btn-primary inline-block">
                    Choose Image
                  </div>
                </div>
                <p className="text-sm text-gray-500">
                  Supported formats: JPG, PNG, GIF (Max 10MB)
                </p>
              </div>
            )}
          </div>

          {/* AI Scanning Status */}
          {aiScanning && (
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-6">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
                <div>
                  <p className="text-purple-300 font-medium">🤖 Gemini AI Analyzing...</p>
                  <p className="text-gray-400 text-sm">Using Google Gemini AI to analyze your clothing item</p>
                </div>
              </div>
            </div>
          )}

          {/* AI Suggestions */}
          {aiSuggestions && !aiScanning && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-green-300 font-medium mb-2">✨ Gemini AI Analysis Complete!</p>
                  <p className="text-gray-400 text-sm">Here's what Google Gemini detected:</p>
                </div>
                <button
                  onClick={applyAISuggestions}
                  className="btn-success text-sm"
                >
                  Apply Suggestions
                </button>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Name:</span>
                  <span className="text-white">{aiSuggestions.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Category:</span>
                  <span className="text-white capitalize">{aiSuggestions.category}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Color:</span>
                  <span className="text-white capitalize">{aiSuggestions.color}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Vibe:</span>
                  <span className="text-white capitalize">{aiSuggestions.vibe}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Tags:</span>
                  <span className="text-white">
                    {Array.isArray(aiSuggestions.tags) 
                      ? aiSuggestions.tags.join(', ') 
                      : aiSuggestions.tags}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Manual Form Section */}
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">Item Details</h3>
            {aiSuggestions && (
              <span className="text-sm text-green-400">Gemini AI Enhanced 🤖✨</span>
            )}
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-white font-medium mb-2">Item Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="input-primary w-full"
                placeholder="e.g., Black Hoodie"
                required
              />
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Category</label>
              <select
                value={formData.category}
                onChange={(e) => handleChange('category', e.target.value)}
                className="input-primary w-full"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Color</label>
              <select
                value={formData.color}
                onChange={(e) => handleChange('color', e.target.value)}
                className="input-primary w-full"
                required
              >
                <option value="">Select a color</option>
                {Object.keys(colorEmojis).map(color => (
                  <option key={color} value={color}>
                    {colorEmojis[color]} {color.charAt(0).toUpperCase() + color.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Vibe</label>
              <select
                value={formData.vibe}
                onChange={(e) => handleChange('vibe', e.target.value)}
                className="input-primary w-full"
              >
                {vibes.map(vibe => (
                  <option key={vibe} value={vibe}>
                    {vibe.charAt(0).toUpperCase() + vibe.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">Tags</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => handleChange('tags', e.target.value)}
                className="input-primary w-full"
                placeholder="comfortable, winter, versatile (comma separated)"
              />
              <p className="text-gray-400 text-sm mt-1">Separate tags with commas</p>
            </div>

            <button type="submit" className="btn-primary w-full">
              Add to Wardrobe
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Upload;