import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import { Avatar as MuiAvatar } from '@mui/material';
import { fetchComments, createComment } from '../api';
import { getTimeAgo } from '../timeAgo';
import './CommentThread.css';

const MAX_COMMENT_LENGTH = 1000;

// A reply whose parent is outside the loaded page is shown at the top level rather than dropped.
function buildTree(comments) {
    const byId = new Map(comments.map((comment) => [comment.id, { ...comment, replies: [] }]));
    const roots = [];
    byId.forEach((node) => {
        const parent = node.parent_id !== null ? byId.get(node.parent_id) : null;
        (parent ? parent.replies : roots).push(node);
    });
    return roots;
}

function Comment({ comment, canComment, onReply }) {
    return (
        <Box className="comment" data-cy="comment">
            <Box className="comment-row">
                <MuiAvatar
                    src={comment.author_profile_picture || ''}
                    alt={comment.author_name}
                    className="comment-avatar"
                >
                    {comment.author_name ? comment.author_name[0].toUpperCase() : 'U'}
                </MuiAvatar>
                <Box className="comment-content">
                    <Box className="comment-meta">
                        <Typography className="comment-author">{comment.author_name}</Typography>
                        {comment.author_is_bot && (
                            <Chip label="bot" size="small" className="comment-bot-chip" />
                        )}
                        <Typography className="comment-time">{getTimeAgo(comment.created_at)}</Typography>
                    </Box>
                    <Typography className="comment-body">{comment.body}</Typography>
                    {canComment && (
                        <Button size="small" className="comment-reply-button" onClick={() => onReply(comment)}>
                            Reply
                        </Button>
                    )}
                </Box>
            </Box>

            {comment.replies.length > 0 && (
                <Box className="comment-replies">
                    {comment.replies.map((reply) => (
                        <Comment key={reply.id} comment={reply} canComment={canComment} onReply={onReply} />
                    ))}
                </Box>
            )}
        </Box>
    );
}

export default function CommentThread({ postId, canComment }) {
    const [comments, setComments] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState('');
    const [draft, setDraft] = useState('');
    const [replyTo, setReplyTo] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState('');
    const inputRef = useRef(null);

    useEffect(() => {
        let cancelled = false;

        fetchComments(postId)
            .then((data) => { if (!cancelled) setComments(data); })
            .catch((error) => { if (!cancelled) setLoadError(error.message); })
            .finally(() => { if (!cancelled) setIsLoading(false); });

        return () => { cancelled = true; };
    }, [postId]);

    const tree = useMemo(() => buildTree(comments), [comments]);
    const trimmedLength = draft.trim().length;
    const canSubmit = trimmedLength > 0 && trimmedLength <= MAX_COMMENT_LENGTH && !isSubmitting;

    const handleReply = (comment) => {
        setReplyTo(comment);
        inputRef.current?.focus();
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!canSubmit) return;

        setIsSubmitting(true);
        setSubmitError('');
        try {
            const { comment } = await createComment(postId, draft, replyTo ? replyTo.id : null);
            setComments((current) => [...current, comment]);
            setDraft('');
            setReplyTo(null);
        } catch (error) {
            setSubmitError(error.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Box className="comment-thread" data-cy="comment-thread">
            {isLoading && (
                <Box className="comment-thread-status">
                    <CircularProgress size={20} className="comment-thread-spinner" />
                </Box>
            )}

            {loadError && <Typography className="comment-thread-error">{loadError}</Typography>}

            {!isLoading && !loadError && comments.length === 0 && (
                <Typography className="comment-thread-empty">No beta yet. Be the first to share some.</Typography>
            )}

            {tree.map((comment) => (
                <Comment key={comment.id} comment={comment} canComment={canComment} onReply={handleReply} />
            ))}

            {canComment ? (
                <Box component="form" onSubmit={handleSubmit} className="comment-form">
                    {replyTo && (
                        <Box className="comment-replying-to">
                            <Typography className="comment-replying-to-text">
                                Replying to {replyTo.author_name}
                            </Typography>
                            <Button size="small" className="comment-cancel-reply" onClick={() => setReplyTo(null)}>
                                Cancel
                            </Button>
                        </Box>
                    )}
                    <TextField
                        multiline
                        maxRows={6}
                        fullWidth
                        size="small"
                        placeholder={replyTo ? `Reply to ${replyTo.author_name}...` : 'Share your beta - heel hooks, rests, sequences...'}
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        inputRef={inputRef}
                        className="comment-input"
                        slotProps={{ htmlInput: { 'data-cy': 'comment-input' } }}
                    />
                    <Box className="comment-form-footer">
                        <Typography
                            className={`comment-counter${trimmedLength > MAX_COMMENT_LENGTH ? ' comment-counter--over' : ''}`}
                        >
                            {trimmedLength}/{MAX_COMMENT_LENGTH}
                        </Typography>
                        {submitError && <Typography className="comment-thread-error">{submitError}</Typography>}
                        <Button
                            type="submit"
                            disabled={!canSubmit}
                            className="comment-submit-button"
                            data-cy="comment-submit"
                        >
                            {isSubmitting ? 'Sending...' : 'Send'}
                        </Button>
                    </Box>
                </Box>
            ) : (
                <Typography className="comment-login-prompt">
                    <Link to="/login">Log in</Link> to share beta.
                </Typography>
            )}
        </Box>
    );
}
