import { useState, useEffect } from 'react';
import { createComment, getCommentsForEntity, buildCommentTree } from '../utils/commentsUtils';

const STORAGE_KEY = 'ymca_comments';

export const useComments = () => {
  const [allComments, setAllComments] = useState([]);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setAllComments(JSON.parse(stored));
      } catch (error) {
        console.error('Error loading comments from storage:', error);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(allComments));
  }, [allComments]);

  const addComment = (content, author, entityType, entityId, parentId = null) => {
    if (!content.trim() || !author.trim()) return false;

    const newComment = createComment(content, author, entityType, entityId, parentId);
    setAllComments(prev => [...prev, newComment]);
    return true;
  };

  const getEntityComments = (entityType, entityId) => {
    const entityComments = getCommentsForEntity(allComments, entityType, entityId);
    return buildCommentTree(entityComments);
  };

  const getCommentCount = (entityType, entityId) => {
    return getCommentsForEntity(allComments, entityType, entityId).length;
  };

  const deleteComment = (commentId) => {
    setAllComments(prev => prev.filter(comment => comment.id !== commentId && comment.parentId !== commentId));
  };

  return {
    addComment,
    getEntityComments,
    getCommentCount,
    deleteComment,
    allComments
  };
};