import React from "react";

export const Post = ({ posts }) => {
  if (!posts || !posts.length) {
    return <div>Loading your posts....</div>;
  }

  return (
    <div>
      {posts.map((post, index) => (
        <div key={index}>
          {" "}
          {post.name}, {post.content}{" "}
        </div>
      ))}
    </div>
  );
};
