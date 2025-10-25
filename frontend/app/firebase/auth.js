import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
} from "firebase/auth";
import app from "./initialize";

const auth = getAuth(app);

// Signup
export function signup(email, password) {
  return createUserWithEmailAndPassword(auth, email, password);
}

// Login
export function login(email, password) {
  return signInWithEmailAndPassword(auth, email, password);
}

// Logout
export function logout() {
  return signOut(auth);
}
