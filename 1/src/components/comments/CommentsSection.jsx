import React, { useState } from 'react';
import { MessageSquare, Plus, X } from 'lucide-react';
import { Comments } from './Comments';
import { CommentForm } from './CommentForm';
import { useComments } from '../../hooks/useComments';

export function CommentsSection({ entityType, entityId, entityName }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const { addComment, getEntityComments, getCommentCount, deleteComment } = useComments();
  
  const comments = getEntityComments(entityType, entityId);
  const commentCount = getCommentCount(entityType, entityId);

  const handleAddComment = (content, author, entityType, entityId, parentId = null) => {
    return addComment(content, author, entityType, entityId, parentId);
  };

  return (
    <div className="border rounded-lg bg-white">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 rounded-lg"
      >
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-gray-500" />
          <span className="font-medium">Comments & Notes</span>
          {commentCount > 0 && (
            <span className="px-2 py-1 bg-blue-100 text-blue-600 rounded-full text-xs font-medium">
              {commentCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isExpanded && commentCount > 0 && (
            <span className="text-sm text-gray-500">{commentCount} comment{commentCount !== 1 ? 's' : ''}</span>
          )}
          {isExpanded ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t p-4 space-y-4">
          <div className="text-sm text-gray-600">
            Comments for: <span className="font-medium">{entityName}</span>
          </div>
          
          <CommentForm
            onSubmit={(content, author) => handleAddComment(content, author, entityType, entityId)}
            placeholder={`Share your thoughts about ${entityName}...`}
          />
          
          <div className="border-t pt-4">
            <Comments
              entityType={entityType}
              entityId={entityId}
              comments={comments}
              onAddComment={handleAddComment}
              onDeleteComment={deleteComment}
            />
          </div>
        </div>
      )}
    </div>
  );
}