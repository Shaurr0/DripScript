// Optional Firebase initialization for Storage/Firestore
// Usage: controlled by VITE_USE_FIREBASE=true in frontend/.env

import { initializeApp } from 'firebase/app';
import { getStorage } from 'firebase/storage';
import { getFirestore } from 'firebase/firestore';

const enabled = import.meta.env.VITE_USE_FIREBASE === 'true';

let app = null;
let storage = null;
let db = null;

if (enabled) {
  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
  };

  app = initializeApp(firebaseConfig);
  storage = getStorage(app);
  db = getFirestore(app);
}

export { app, storage, db, enabled as firebaseEnabled };
