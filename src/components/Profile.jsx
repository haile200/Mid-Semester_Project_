import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import { Avatar as MuiAvatar } from '@mui/material';
import { fetchCurrentUser } from '../api';
import { climb } from '../theme';

export default function Profile() {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;

        fetchCurrentUser()
            .then((data) => {
                if (!cancelled) {
                    setUser(data.user);
                    setIsLoading(false);
                }
            })
            .catch(() => {
                if (!cancelled) {
                    navigate('/login', { replace: true });
                }
            });

        return () => { cancelled = true; };
    }, [navigate]);

    if (isLoading) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
                <CircularProgress sx={{ color: climb.coralDark }} />
            </Box>
        );
    }

    return (
        <Box sx={{ minHeight: '100vh', backgroundColor: climb.page, py: { xs: 2, sm: 5 }, px: 2 }}>
            <Box
                data-cy="profile-page"
                sx={{
                    maxWidth: 480,
                    margin: '0 auto',
                    backgroundColor: 'white',
                    borderRadius: '16px',
                    border: '1px solid #EDEBE4',
                    boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)',
                    overflow: 'hidden',
                }}
            >
                {/* Chalk band behind the avatar - the "summit photo" header */}
                <Box sx={{ backgroundColor: climb.chalk, textAlign: 'center', pt: 4, pb: 3, px: 2 }}>
                    <MuiAvatar
                        src={user.profile_picture || ''}
                        alt={user.name}
                        sx={{
                            width: 76, height: 76, margin: '0 auto', fontSize: '28px', fontWeight: 'bold',
                            backgroundColor: climb.coralTint, color: climb.onCoralTint,
                            border: `3px solid ${climb.coral}`,
                        }}
                    >
                        {user.name ? user.name[0].toUpperCase() : 'U'}
                    </MuiAvatar>
                    <Typography variant="h5" fontWeight="bold" data-cy="profile-name" sx={{ mt: 1.5, color: climb.rock }}>
                        {user.name}
                    </Typography>
                    <Typography data-cy="profile-email" sx={{ color: climb.stone, fontSize: '14px' }}>
                        {user.email}
                    </Typography>
                </Box>

                <Box sx={{ p: { xs: 2, sm: 3 } }}>
                    <Typography sx={{ fontWeight: 'bold', fontSize: '14px', mb: 1.5, color: climb.rock }}>
                        Climbing card
                    </Typography>
                    {/* Placeholder badges until real send data exists on the backend */}
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip label="Boulderer" sx={{ backgroundColor: climb.coralTint, color: climb.onCoralTint, fontWeight: 'bold', fontSize: '12px', borderRadius: '999px' }} />
                        <Chip label="Working on V5" sx={{ backgroundColor: climb.chalk, color: climb.rock, fontWeight: 'bold', fontSize: '12px', borderRadius: '999px' }} />
                        <Chip label="Open to beta" sx={{ backgroundColor: climb.sentTint, color: climb.onSentTint, fontWeight: 'bold', fontSize: '12px', borderRadius: '999px' }} />
                    </Box>
                </Box>
            </Box>
        </Box>
    );
}
