"use client";
import React, { useState, createContext, useContext, useEffect } from "react";
import { signup, login, logout } from "./auth";
import { getAuth, onAuthStateChanged } from "firebase/auth";
import LoginForm from "../../components/authentication-01";
const AuthContext = createContext({
  isLoadingAuthStatus: true,
  isAuthenticated: false,
});

const auth = getAuth();

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuthStatus, setIsLoadingAuthStatus] = useState(true);

  const handleAuth = (user) => {
    setIsAuthenticated(!!user);
    setIsLoadingAuthStatus(false);
  };

  onAuthStateChanged(auth, handleAuth);

  const signupUser = async ({ email, password }) => {
    signup(email, password)
      .then(() => setIsAuthenticated(true))
      .catch(() => alert("Unable to sign up, please try a different email"));
  };

  const loginUser = async ({ email, password }) => {
    login(email, password)
      .then(() => setIsAuthenticated(true))
      .catch((err) => {
        if (err.message === "Firebase: Error (auth/invalid-credential).") {
          signupUser({ email, password });
        }
      });
  };

  const logoutUser = async () => {
    logout()
      .then(() => setIsAuthenticated(false))
      .catch(() => alert("Unable to log you out, please try again"));
  };

  return (
    <AuthContext.Provider
      value={{
        loginUser,
        logoutUser,
        signupUser,
        isLoadingAuthStatus,
        isAuthenticated,
      }}
    >
      {!isLoadingAuthStatus && !isAuthenticated && (
        <LoginForm login={loginUser} />
      )}
      {!isLoadingAuthStatus && isAuthenticated && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
