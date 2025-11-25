// Import the functions you need from the SDKs you need
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';

// Your web app's Firebase configuration
// TODO: Replace with your actual Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyD_EKMuJBHRwaWUHjWqY-jbHu3Ge8Y_erQ",
  authDomain: "lct-auth-db7ff.firebaseapp.com",
  projectId: "lct-auth-db7ff",
  storageBucket: "lct-auth-db7ff.firebasestorage.app",
  messagingSenderId: "499845763196",
  appId: "1:499845763196:web:a4bf8430e1c1147e70f9f9"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Google Auth Provider
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

// Auth functions
export const signInWithGoogle = () => signInWithPopup(auth, googleProvider);
export const signOutUser = () => signOut(auth);

export default app;

