import { useState } from 'react';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import CheckIcon from '@mui/icons-material/Check';
import DOMPurify from 'dompurify';
import Avatar from './Avatar';
import CommentThread from './CommentThread';
import ReportPost from './ReportPost';
import LikeButton from './LikeButton';
import { climbingBadges } from '../theme';
import { getTimeAgo } from '../timeAgo';
import './SinglePost.css';

export default function SinglePost({
    postId, authorId, currentUserId, title, author, body, imageUrl, createdAt, canComment, likeCount, likedByMe,
}) {
    // "Beta" is climber-speak for route advice; the thread loads only when opened.
    const [isThreadOpen, setIsThreadOpen] = useState(false);
    const [isReportOpen, setIsReportOpen] = useState(false);
    // The server refuses reports on your own post, so the button is not offered there.
    const canReport = Boolean(currentUserId) && String(currentUserId) !== String(authorId);

    const badges = climbingBadges(`${title}|${author}`);
    const disciplineClass = `post-badge--${badges.discipline.label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
        // Chalk-white card with a soft stone shadow - modern and calm like a gym wall
        <Card className="post-card" data-cy="post-card">
            <Box className="post-header">
                <Avatar name={author || 'User'} size={40} />
                <Box className="post-header-text">
                    <Typography variant="subtitle1" className="post-author-name">
                        {author || 'Unknown Author'}
                    </Typography>
                    {createdAt && (
                        <Typography variant="caption" className="post-timestamp">
                            {getTimeAgo(createdAt)}
                        </Typography>
                    )}
                </Box>
            </Box>

            {/* Discipline, grade, and status badges - the vocabulary climbers scan for first */}
            <Box className="post-badges">
                <Chip label={badges.discipline.label} className={`post-badge ${disciplineClass}`} />
                <Chip label={badges.grade} className="post-badge post-badge--grade" />
                {badges.sent ? (
                    <Chip
                        icon={<CheckIcon className="post-badge-sent-icon" />}
                        label="Sent"
                        className="post-badge post-badge--sent"
                    />
                ) : (
                    <Chip label="Project" className="post-badge post-badge--project" />
                )}
            </Box>

            <Typography variant="h6" className="post-title" data-cy="post-title">
                {title}
            </Typography>

            {imageUrl && (
                <Box className="post-image-container">
                    <img
                        src={imageUrl}
                        alt="Post attachment"
                        className="post-image"
                        data-cy="post-image"
                        onError={(e) => { e.target.style.display = 'none'; }}
                    />
                </Box>
            )}

            <Box
                className="post-body"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(body) }}
            />

            <Box className="post-footer">
                <LikeButton
                    postId={postId}
                    initialCount={likeCount}
                    initialLiked={likedByMe}
                    canLike={Boolean(currentUserId)}
                />
                {canReport && (
                    <Button
                        size="small"
                        className="post-report-button"
                        onClick={() => setIsReportOpen((open) => !open)}
                        data-cy="report-toggle"
                    >
                        Report
                    </Button>
                )}
                <Box className="post-footer-spacer" />
                <Button
                    startIcon={<LightbulbOutlinedIcon />}
                    onClick={() => setIsThreadOpen((open) => !open)}
                    className="beta-button"
                    data-cy="beta-toggle"
                >
                    {isThreadOpen ? 'Hide beta' : 'Show beta'}
                </Button>
            </Box>

            {isReportOpen && <ReportPost postId={postId} onClose={() => setIsReportOpen(false)} />}

            {isThreadOpen && <CommentThread postId={postId} canComment={canComment} />}
        </Card>
    );
}
