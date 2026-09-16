import React from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Avatar as MuiAvatar } from '@mui/material';
import './User.css';

export default function User({ id, name, postCount, profile_picture }) {
    const navigate = useNavigate();

    return (
        // Compact card row: avatar, identity, climb count - thumb-sized tap targets for mobile
        <Box className="user-card">
            <MuiAvatar
                src={profile_picture || ''}
                alt={name}
                className="user-card-avatar"
            >
                {name ? name[0].toUpperCase() : 'U'}
            </MuiAvatar>

            <Box className="user-card-info">
                <Typography className="user-card-name">
                    {name}
                </Typography>
                <Typography className="user-card-meta">
                    {postCount || 0} {postCount === 1 ? 'climb logged' : 'climbs logged'}
                </Typography>
            </Box>

            <Button
                size="small"
                onClick={() => navigate(`/user-posts/${id}`)}
                className="user-card-button"
            >
                See sends
            </Button>
        </Box>
    );
}
