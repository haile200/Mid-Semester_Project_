import { useState } from 'react';
import Button from '@mui/material/Button';
import FavoriteIcon from '@mui/icons-material/Favorite';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import { likePost, unlikePost } from '../api';

export default function LikeButton({ postId, initialCount, initialLiked, canLike }) {
    const [count, setCount] = useState(initialCount || 0);
    const [liked, setLiked] = useState(Boolean(initialLiked));
    const [isSending, setIsSending] = useState(false);

    const handleClick = async () => {
        setIsSending(true);
        try {
            // The server's answer is the truth, so a double click or another tab cannot leave a wrong count.
            const result = await (liked ? unlikePost(postId) : likePost(postId));
            setLiked(result.liked);
            setCount(result.likeCount);
        } catch (error) {
            console.error('Like failed:', error);
        } finally {
            setIsSending(false);
        }
    };

    return (
        <Button
            size="small"
            onClick={handleClick}
            disabled={!canLike || isSending}
            title={canLike ? (liked ? 'Unlike' : 'Like') : 'Log in to like posts'}
            startIcon={liked ? <FavoriteIcon /> : <FavoriteBorderIcon />}
            className={`post-like-button${liked ? ' post-like-button--liked' : ''}`}
            data-cy="like-button"
        >
            {count}
        </Button>
    );
}
