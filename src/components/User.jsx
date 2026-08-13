import React from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Avatar as MuiAvatar } from '@mui/material';
import { climb } from '../theme';

export default function User({ id, name, email, postCount, profile_picture }) {
    const navigate = useNavigate();

    return (
        // Compact card row: avatar, identity, climb count - thumb-sized tap targets for mobile
        <Box sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            padding: '12px 16px',
            backgroundColor: 'white',
            borderRadius: '14px',
            marginBottom: '10px',
            border: '1px solid #EDEBE4',
            boxShadow: '0 2px 8px rgba(44, 44, 42, 0.04)',
        }}>
            <MuiAvatar
                src={profile_picture || ''}
                alt={name}
                sx={{ width: 42, height: 42, backgroundColor: climb.coralTint, color: climb.onCoralTint, fontWeight: 'bold' }}
            >
                {name ? name[0].toUpperCase() : 'U'}
            </MuiAvatar>

            <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography fontWeight="bold" sx={{ fontSize: '14px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {name}
                </Typography>
                <Typography sx={{ fontSize: '12px', color: climb.stone, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {postCount || 0} {postCount === 1 ? 'climb logged' : 'climbs logged'} · {email}
                </Typography>
            </Box>

            <Button
                size="small"
                onClick={() => navigate(`/user-posts/${id}`)}
                sx={{
                    backgroundColor: climb.coral,
                    color: climb.onCoral,
                    textTransform: 'none',
                    fontWeight: 'bold',
                    borderRadius: '999px',
                    px: 2,
                    fontSize: '12px',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                    '&:hover': { backgroundColor: climb.coralHover },
                }}
            >
                See sends
            </Button>
        </Box>
    );
}
