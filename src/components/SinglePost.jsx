import React, { useState } from 'react';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import CheckIcon from '@mui/icons-material/Check';
import DOMPurify from 'dompurify';
import Avatar from './Avatar';
import { climbingBadges } from '../theme';
import './SinglePost.css';

export default function SinglePost({ title, author, body, imageUrl, createdAt }) {
    // "Share beta" is climber-speak for route advice - local UI only for now
    const [isBetaOpen, setIsBetaOpen] = useState(false);
    const [betaText, setBetaText] = useState('');
    const [betaSent, setBetaSent] = useState(false);

    const badges = climbingBadges(`${title}|${author}`);
    const disciplineClass = `post-badge--${badges.discipline.label.toLowerCase().replace(/\s+/g, '-')}`;

    const getTimeAgo = (dateString) => {
        if (!dateString) return '';
        const postDate = new Date(dateString.endsWith('GMT') ? dateString : dateString + 'Z');
        const now = new Date();
        const seconds = Math.floor((now - postDate) / 1000);

        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days} day${days !== 1 ? 's' : ''} ago`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months} month${months !== 1 ? 's' : ''} ago`;
        const years = Math.floor(months / 12);
        return `${years} year${years !== 1 ? 's' : ''} ago`;
    };

    const handleSendBeta = () => {
        if (!betaText.trim()) return;
        setBetaText('');
        setIsBetaOpen(false);
        setBetaSent(true);
    };

    return (
        // Chalk-white card with a soft stone shadow - modern and calm like a gym wall
        <Card className="post-card">
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

            <Typography variant="h6" className="post-title">
                {title}
            </Typography>

            {imageUrl && (
                <Box className="post-image-container">
                    <img
                        src={imageUrl}
                        alt="Post attachment"
                        className="post-image"
                        onError={(e) => { e.target.style.display = 'none'; }}
                    />
                </Box>
            )}

            <Box
                className="post-body"
                dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(body) }}
            />

            <Box className="post-footer">
                <Box className="post-footer-spacer" />
                {betaSent ? (
                    <Typography className="beta-shared-message">
                        Beta shared with {author ? author.split(' ')[0] : 'the author'}
                    </Typography>
                ) : (
                    <Button
                        startIcon={<LightbulbOutlinedIcon />}
                        onClick={() => setIsBetaOpen((open) => !open)}
                        className="beta-button"
                    >
                        Share beta
                    </Button>
                )}
            </Box>

            {isBetaOpen && !betaSent && (
                <Box className="beta-form">
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="Share your beta - heel hooks, rests, sequences..."
                        value={betaText}
                        onChange={(e) => setBetaText(e.target.value)}
                        className="beta-input"
                    />
                    <Button onClick={handleSendBeta} className="beta-send-button">
                        Send
                    </Button>
                </Box>
            )}
        </Card>
    );
}
