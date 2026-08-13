import React, { useState } from 'react';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import CheckIcon from '@mui/icons-material/Check';
import Avatar from './Avatar';
import styles from './SinglePost.module.css';
import { climb, climbingBadges } from '../theme';

export default function SinglePost({ title, author, body, imageUrl, createdAt }) {
    // "Share beta" is climber-speak for route advice - local UI only for now
    const [isBetaOpen, setIsBetaOpen] = useState(false);
    const [betaText, setBetaText] = useState('');
    const [betaSent, setBetaSent] = useState(false);

    const badges = climbingBadges(`${title}|${author}`);

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

    const chipSx = { height: 22, fontSize: '11px', fontWeight: 'bold', borderRadius: '999px' };

    return (
        // Chalk-white card with a soft stone shadow - modern and calm like a gym wall
        <Card sx={{
            p: { xs: 2, sm: 3 },
            borderRadius: '14px',
            border: '1px solid #EDEBE4',
            boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)',
            mb: 2,
            transition: 'box-shadow 0.2s ease',
            '&:hover': { boxShadow: '0 6px 16px rgba(44, 44, 42, 0.12)' },
        }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                <Avatar name={author || 'User'} size={40} />
                <Box sx={{ ml: 1.5, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ lineHeight: 1.3 }}>
                        {author || 'Unknown Author'}
                    </Typography>
                    {createdAt && (
                        <Typography variant="caption" sx={{ color: climb.stone }}>
                            {getTimeAgo(createdAt)}
                        </Typography>
                    )}
                </Box>
            </Box>

            {/* Discipline, grade, and status badges - the vocabulary climbers scan for first */}
            <Box sx={{ display: 'flex', gap: 0.75, mb: 1.5, flexWrap: 'wrap' }}>
                <Chip label={badges.discipline.label} sx={{ ...chipSx, backgroundColor: badges.discipline.bg, color: badges.discipline.fg }} />
                <Chip label={badges.grade} sx={{ ...chipSx, backgroundColor: climb.chalk, color: climb.rock }} />
                {badges.sent ? (
                    <Chip icon={<CheckIcon sx={{ fontSize: 13, color: `${climb.onSentTint} !important` }} />} label="Sent"
                        sx={{ ...chipSx, backgroundColor: climb.sentTint, color: climb.onSentTint }} />
                ) : (
                    <Chip label="Project" sx={{ ...chipSx, backgroundColor: climb.projectTint, color: climb.onProjectTint }} />
                )}
            </Box>

            <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ fontSize: '17px' }}>
                {title}
            </Typography>

            {imageUrl && (
                <Box sx={{ width: '100%', maxHeight: '400px', overflow: 'hidden', borderRadius: '10px', mb: 2 }}>
                    <img
                        src={imageUrl}
                        alt="Post attachment"
                        className={styles.postImage}
                        onError={(e) => { e.target.style.display = 'none'; }}
                    />
                </Box>
            )}

            <Box
                sx={{
                    color: '#444441',
                    fontSize: '14px',
                    lineHeight: 1.6,
                    '& p': { margin: '0 0 10px 0' },
                    '& a': { color: climb.coralDark, textDecoration: 'none' },
                }}
                dangerouslySetInnerHTML={{ __html: body }}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1.5, pt: 1.5, borderTop: '1px solid #F1EFE8' }}>
                <Box sx={{ flexGrow: 1 }} />
                {betaSent ? (
                    <Typography sx={{ fontSize: '12px', fontWeight: 'bold', color: climb.onSentTint }}>
                        Beta shared with {author ? author.split(' ')[0] : 'the author'}
                    </Typography>
                ) : (
                    <Button
                        startIcon={<LightbulbOutlinedIcon sx={{ fontSize: 15 }} />}
                        onClick={() => setIsBetaOpen((open) => !open)}
                        sx={{
                            backgroundColor: climb.coral,
                            color: climb.onCoral,
                            textTransform: 'none',
                            fontWeight: 'bold',
                            borderRadius: '999px',
                            px: 1.75,
                            py: 0.5,
                            fontSize: '12px',
                            '&:hover': { backgroundColor: climb.coralHover },
                        }}
                    >
                        Share beta
                    </Button>
                )}
            </Box>

            {isBetaOpen && !betaSent && (
                <Box sx={{ display: 'flex', gap: 1, mt: 1.5 }}>
                    <TextField
                        fullWidth
                        size="small"
                        placeholder="Share your beta - heel hooks, rests, sequences..."
                        value={betaText}
                        onChange={(e) => setBetaText(e.target.value)}
                        sx={{ '& .MuiOutlinedInput-root': { borderRadius: '999px', fontSize: '13px' } }}
                    />
                    <Button
                        onClick={handleSendBeta}
                        sx={{
                            backgroundColor: climb.rock,
                            color: climb.chalk,
                            textTransform: 'none',
                            fontWeight: 'bold',
                            borderRadius: '999px',
                            px: 2,
                            fontSize: '12px',
                            '&:hover': { backgroundColor: climb.rockHover },
                        }}
                    >
                        Send
                    </Button>
                </Box>
            )}
        </Card>
    );
}
