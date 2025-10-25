"use client";
import React, { Suspense, useState, useEffect, useCallback } from "react";
import { useAuth } from "./firebase/AuthContext";
import { Post } from "./utils/showPosts";

export default function Home() {
  const { isAuthenticated, isLoadingAuthStatus } = useAuth();
  const [posts, setPosts] = useState();
  const [postName, setPostName] = useState();
  const [postContent, setPostContent] = useState();

  useEffect(() => {
    const getPosts = async () => {
      try {
        const currPosts = await fetch("http://127.0.0.1:5000/posts", {
          method: "GET",
          credentials: "include",
        });
        const response = await currPosts.json();
        setPosts(response);
      } catch (err) {
        alert(err.message);
      }
    };

    isAuthenticated && getPosts();
  }, [isAuthenticated, isLoadingAuthStatus]);

  const createPost = useCallback(() => {
    const putPost = async () => {
      try {
        const currPosts = await fetch("http://127.0.0.1:5000/posts", {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: postName,
            content: postContent,
          }),
        });
      } catch (err) {
        alert(err.message);
      }
    };

    isAuthenticated && putPost();
  });

  console.log("auth", isLoadingAuthStatus, isAuthenticated);
  return (
    <>
      <Post posts={posts} />
      <div>
        <label htmlFor="postName">Post Title</label>
        <input
          id="postName"
          type="text"
          onChange={(e) => setPostName(e.target.value)}
        />
        <label htmlFor="postContent">Description</label>
        <input
          id="postContent"
          type="text"
          onChange={(e) => setPostContent(e.target.value)}
        />
        <button type="submit" onClick={createPost}>
          Create
        </button>
      </div>
    </>
  );
}
