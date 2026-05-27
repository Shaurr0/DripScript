import {
  collection,
  addDoc,
  deleteDoc,
  doc,
  getDocs,
  query,
  orderBy,
  updateDoc,
  serverTimestamp,
} from 'firebase/firestore';
import { db } from './firebase';

function assertUserId(userId, action) {
  if (!userId) {
    const error = new Error(`Missing user id for Firestore ${action}.`);
    console.error(`[Firestore] ${action} failed: missing uid`);
    throw error;
  }
}

function logFirestoreError(action, error, context = {}) {
  const code = error?.code || 'unknown';
  const message = error?.message || String(error);
  console.error(`[Firestore] ${action} failed (${code}): ${message}`, context);
}

function wardrobeCollection(userId) {
  return collection(db, 'users', userId, 'wardrobe');
}

function savedOutfitsCollection(userId) {
  return collection(db, 'users', userId, 'savedOutfits');
}

export async function fetchWardrobeItems(userId) {
  assertUserId(userId, 'wardrobe read');
  console.info('[Firestore] Fetching wardrobe items', { userId });
  try {
    const q = query(wardrobeCollection(userId), orderBy('timestamp', 'desc'));
    const snapshot = await getDocs(q);
    const items = snapshot.docs.map((d) => ({ id: d.id, ...d.data() }));
    console.info('[Firestore] Wardrobe items loaded', { userId, count: items.length });
    return items;
  } catch (error) {
    logFirestoreError('wardrobe read', error, { userId });
    throw error;
  }
}

export async function addWardrobeItemToFirestore(userId, item) {
  assertUserId(userId, 'wardrobe write');
  const payload = {
    name: item.name || '',
    category: item.category || 'tops',
    color: item.color || '',
    pattern: item.pattern || 'solid',
    vibe: item.vibe || 'casual',
    tags: item.tags || [],
    caption: item.caption || '',
    image: item.image || '',
    hasRealImage: item.hasRealImage || false,
    imageHash: item.imageHash || '',
    timestamp: serverTimestamp(),
  };
  console.info('[Firestore] Creating wardrobe item', { userId });
  try {
    const docRef = await addDoc(wardrobeCollection(userId), payload);
    console.info('[Firestore] Wardrobe item created', { userId, id: docRef.id });
    return { id: docRef.id, ...payload, timestamp: new Date().toISOString() };
  } catch (error) {
    logFirestoreError('wardrobe write', error, { userId, payload });
    throw error;
  }
}

export async function deleteWardrobeItemFromFirestore(userId, itemId) {
  assertUserId(userId, 'wardrobe delete');
  if (!itemId) {
    throw new Error('Missing wardrobe item id for delete.');
  }
  console.info('[Firestore] Deleting wardrobe item', { userId, itemId });
  try {
    const docRef = doc(db, 'users', userId, 'wardrobe', itemId);
    await deleteDoc(docRef);
  } catch (error) {
    logFirestoreError('wardrobe delete', error, { userId, itemId });
    throw error;
  }
}

export async function fetchSavedOutfits(userId) {
  assertUserId(userId, 'saved outfits read');
  console.info('[Firestore] Fetching saved outfits', { userId });
  try {
    const q = query(savedOutfitsCollection(userId), orderBy('timestamp', 'desc'));
    const snapshot = await getDocs(q);
    const outfits = snapshot.docs.map((d) => ({ id: d.id, ...d.data() }));
    console.info('[Firestore] Saved outfits loaded', { userId, count: outfits.length });
    return outfits;
  } catch (error) {
    logFirestoreError('saved outfits read', error, { userId });
    throw error;
  }
}

export async function addSavedOutfitToFirestore(userId, outfit) {
  assertUserId(userId, 'saved outfits write');
  const payload = {
    name: outfit.name || '',
    items: outfit.items || [],
    occasion: outfit.occasion || '',
    styling_tip: outfit.styling_tip || '',
    color_story: outfit.color_story || '',
    why_it_works: outfit.why_it_works || '',
    timestamp: serverTimestamp(),
  };
  console.info('[Firestore] Creating saved outfit', { userId });
  try {
    const docRef = await addDoc(savedOutfitsCollection(userId), payload);
    console.info('[Firestore] Saved outfit created', { userId, id: docRef.id });
    return { id: docRef.id, ...payload, timestamp: new Date().toISOString() };
  } catch (error) {
    logFirestoreError('saved outfits write', error, { userId, payload });
    throw error;
  }
}

export async function deleteSavedOutfitFromFirestore(userId, outfitId) {
  assertUserId(userId, 'saved outfits delete');
  if (!outfitId) {
    throw new Error('Missing saved outfit id for delete.');
  }
  console.info('[Firestore] Deleting saved outfit', { userId, outfitId });
  try {
    const docRef = doc(db, 'users', userId, 'savedOutfits', outfitId);
    await deleteDoc(docRef);
  } catch (error) {
    logFirestoreError('saved outfits delete', error, { userId, outfitId });
    throw error;
  }
}

export async function updateWardrobeItemInFirestore(userId, itemId, updates) {
  assertUserId(userId, 'wardrobe update');
  if (!itemId) {
    throw new Error('Missing wardrobe item id for update.');
  }
  const payload = {
    name: updates.name || '',
    category: updates.category || 'tops',
    color: updates.color || '',
    pattern: updates.pattern || 'solid',
    vibe: updates.vibe || 'casual',
    tags: updates.tags || [],
    caption: updates.caption || '',
    image: updates.image || '',
    hasRealImage: updates.hasRealImage || false,
    imageHash: updates.imageHash || '',
  };
  console.info('[Firestore] Updating wardrobe item', { userId, itemId });
  try {
    const docRef = doc(db, 'users', userId, 'wardrobe', itemId);
    await updateDoc(docRef, payload);
    return { id: itemId, ...payload };
  } catch (error) {
    logFirestoreError('wardrobe update', error, { userId, itemId, payload });
    throw error;
  }
}

export async function updateSavedOutfitInFirestore(userId, outfitId, updates) {
  assertUserId(userId, 'saved outfits update');
  if (!outfitId) {
    throw new Error('Missing saved outfit id for update.');
  }
  const payload = {
    name: updates.name || '',
    items: updates.items || [],
    occasion: updates.occasion || '',
    styling_tip: updates.styling_tip || '',
    color_story: updates.color_story || '',
    why_it_works: updates.why_it_works || '',
  };
  console.info('[Firestore] Updating saved outfit', { userId, outfitId });
  try {
    const docRef = doc(db, 'users', userId, 'savedOutfits', outfitId);
    await updateDoc(docRef, payload);
    return { id: outfitId, ...payload };
  } catch (error) {
    logFirestoreError('saved outfits update', error, { userId, outfitId, payload });
    throw error;
  }
}
