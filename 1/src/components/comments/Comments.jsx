import React, { useState } from 'react';
import { MessageSquare, Reply, Trash2, Calendar } from 'lucide-react';
import { CommentForm } from './CommentForm';

function Comment({ comment, onReply, onDelete, depth = 0 }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [isExpanded, setIsExpanded] = useState(depth < 2);

  const handleReply = (content, author) => {
    const success = onReply(content, author, comment.id);
    if (success) {
      setShowReplyForm(false);
      setIsExpanded(true);
    }
    return success;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'just now';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 24 * 7) {
      return `${Math.floor(diffInHours / 24)}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const maxDepth = 4;
  const shouldIndent = depth < maxDepth;

  return (
    <div className={`${shouldIndent ? `ml-${Math.min(depth * 6, 24)}` : ''}`}>
      <div className="border rounded-lg p-3 bg-white">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-xs font-medium text-blue-600">
                {comment.author.charAt(0).toUpperCase()}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-900">{comment.author}</span>
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                {formatDate(comment.createdAt)}
              </div>
            </div>
          </div>
          <button
            onClick={() => onDelete(comment.id)}
            className="p-1 text-gray-400 hover:text-red-500 rounded"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
        
        <p className="text-gray-700 mb-3 whitespace-pre-wrap">{comment.content}</p>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
          >
            <Reply className="w-3 h-3" />
            Reply
          </button>
          
          {comment.replies.length > 0 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? '−' : '+'} {comment.replies.length} {comment.replies.length === 1 ? 'reply' : 'replies'}
            </button>
          )}
        </div>
        
        {showReplyForm && (
          <div className="mt-3 pt-3 border-t">
            <CommentForm
              onSubmit={handleReply}
              placeholder="Write a reply..."
              buttonText="Reply"
              autoFocus
              compact
            />
          </div>
        )}
      </div>

      {isExpanded && comment.replies.length > 0 && (
        <div className="mt-3 space-y-3">
          {comment.replies.map((reply) => (
            <Comment
              key={reply.id}
              comment={reply}
              onReply={onReply}
              onDelete={onDelete}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function Comments({ entityType, entityId, comments, onAddComment, onDeleteComment }) {
  if (!comments.length) {
    return (
      <div className="text-center py-8 text-gray-500">
        <MessageSquare className="w-8 h-8 mx-auto mb-2 text-gray-300" />
        <p>No comments yet. Be the first to add one!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {comments.map((comment) => (
        <Comment
          key={comment.id}
          comment={comment}
          onReply={(content, author, parentId) => onAddComment(content, author, entityType, entityId, parentId)}
          onDelete={onDeleteComment}
        />
      ))}
    </div>
  );
}