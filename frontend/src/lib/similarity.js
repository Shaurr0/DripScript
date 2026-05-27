export const hashCache = {};

export const getFilenameFromUrl = (url) => {
  if (!url) return '';
  try {
    const segment = url.split('/').pop() || '';
    // Remove timestamp prefix (digits followed by underscore)
    return segment.replace(/^\d+_/, '');
  } catch (e) {
    return '';
  }
};

export const loadImage = (src) => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(e);
    img.src = src;
  });
};

export const computeDHashFromImage = (img) => {
  const width = 9;
  const height = 8;
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) return '';
  ctx.drawImage(img, 0, 0, width, height);
  const imgData = ctx.getImageData(0, 0, width, height);
  const data = imgData.data;

  // Convert to grayscale
  const gray = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) {
    const r = data[i * 4];
    const g = data[i * 4 + 1];
    const b = data[i * 4 + 2];
    gray[i] = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
  }

  // Compute difference hash (dHash)
  let hash = '';
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width - 1; x++) {
      const left = gray[y * width + x];
      const right = gray[y * width + (x + 1)];
      hash += (left > right) ? '1' : '0';
    }
  }
  return hash;
};

export const computeImageHash = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const dataUrl = e.target?.result;
      if (typeof dataUrl === 'string') {
        try {
          const img = await loadImage(dataUrl);
          const hash = computeDHashFromImage(img);
          resolve(hash);
        } catch (err) {
          console.warn('Failed to compute image hash from file:', err);
          resolve('');
        }
      } else {
        resolve('');
      }
    };
    reader.onerror = () => resolve('');
    reader.readAsDataURL(file);
  });
};

export const getHammingDistance = (hash1, hash2) => {
  if (!hash1 || !hash2 || hash1.length !== hash2.length) return 999;
  let distance = 0;
  for (let i = 0; i < hash1.length; i++) {
    if (hash1[i] !== hash2[i]) distance++;
  }
  return distance;
};

export const precomputeWardrobeHashes = async (wardrobe) => {
  for (const item of wardrobe) {
    if (item.image && !item.imageHash && !hashCache[item.image]) {
      loadImage(item.image)
        .then((img) => {
          const hash = computeDHashFromImage(img);
          hashCache[item.image] = hash;
          console.debug('Background hash computed for:', item.image, hash);
        })
        .catch((err) => {
          // ignore loading error
        });
    }
  }
};

export const checkForDuplicate = async (file, wardrobe) => {
  if (!file) return { isDuplicate: false, hash: '' };

  const newFilename = file.name.toLowerCase();

  // 1. Check filename & path/URL duplicates
  for (const item of wardrobe) {
    if (item.image) {
      const existingFilename = getFilenameFromUrl(item.image).toLowerCase();
      if (existingFilename && existingFilename === newFilename) {
        return { isDuplicate: true, hash: '' };
      }
    }
  }

  // 2. Compute hash for the new file
  const newHash = await computeImageHash(file);
  if (!newHash) return { isDuplicate: false, hash: '' };

  // 3. Compare with hashes of existing items
  for (const item of wardrobe) {
    let existingHash = item.imageHash;
    if (!existingHash && item.image) {
      if (hashCache[item.image]) {
        existingHash = hashCache[item.image];
      } else {
        try {
          const img = await loadImage(item.image);
          existingHash = computeDHashFromImage(img);
          hashCache[item.image] = existingHash;
        } catch (e) {
          // ignore loading error
        }
      }
    }

    if (existingHash) {
      const distance = getHammingDistance(newHash, existingHash);
      // Hamming distance <= 8 indicates high visual similarity (nearly identical)
      if (distance <= 8) {
        return { isDuplicate: true, hash: newHash };
      }
    }
  }

  return { isDuplicate: false, hash: newHash };
};
