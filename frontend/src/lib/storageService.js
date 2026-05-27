import { apiPostForm, API_BASE } from './apiClient';

export async function uploadWardrobeImage(userId, file, token) {
  if (!userId) {
    throw new Error('You must be signed in to upload images.');
  }
  if (!file) {
    throw new Error('No image file provided.');
  }

  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    throw new Error('Image must be under 10MB.');
  }

  console.info('[Storage] Uploading wardrobe image', {
    userId,
    name: file.name,
    type: file.type,
    size: file.size,
  });

  const formData = new FormData();
  formData.append('file', file);
  formData.append('userId', userId);

  const result = await apiPostForm('/api/upload-image', formData, { token, timeout: 60000 });
  const imageUrl = `${API_BASE}${result.url}`;

  console.info('[Storage] Upload complete', { userId, url: imageUrl });
  return imageUrl;
}
