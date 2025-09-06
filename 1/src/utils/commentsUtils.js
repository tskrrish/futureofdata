export const generateCommentId = () => {
  return `comment_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const buildCommentTree = (comments) => {
  const commentMap = new Map();
  const roots = [];

  comments.forEach(comment => {
    commentMap.set(comment.id, { ...comment, replies: [] });
  });

  comments.forEach(comment => {
    if (comment.parentId) {
      const parent = commentMap.get(comment.parentId);
      if (parent) {
        parent.replies.push(commentMap.get(comment.id));
      }
    } else {
      roots.push(commentMap.get(comment.id));
    }
  });

  const sortByDate = (a, b) => new Date(b.createdAt) - new Date(a.createdAt);
  roots.sort(sortByDate);
  
  const sortReplies = (comment) => {
    comment.replies.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    comment.replies.forEach(sortReplies);
  };
  
  roots.forEach(sortReplies);
  
  return roots;
};

export const createComment = (content, author, entityType, entityId, parentId = null) => {
  return {
    id: generateCommentId(),
    content: content.trim(),
    author,
    entityType,
    entityId,
    parentId,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
};

export const getCommentsForEntity = (allComments, entityType, entityId) => {
  return allComments.filter(comment => 
    comment.entityType === entityType && comment.entityId === entityId
  );
};