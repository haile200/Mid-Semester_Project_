import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import { Avatar as MuiAvatar } from '@mui/material';
import { fetchCurrentUser } from '../api';

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
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box
            data-cy="profile-page"
            sx={{
                maxWidth: 480,
                margin: '48px auto',
                padding: '32px',
                backgroundColor: 'white',
                borderRadius: '8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
                border: '1px solid #f0f0f0',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 1
            }}
        >
            <MuiAvatar
                src={user.profile_picture || ''}
                alt={user.name}
                sx={{ width: 72, height: 72, mb: 1 }}
            >
                {user.name ? user.name[0].toUpperCase() : 'U'}
            </MuiAvatar>
            <Typography variant="h5" fontWeight="bold" data-cy="profile-name">
                {user.name}
            </Typography>
            <Typography color="text.secondary" data-cy="profile-email">
                {user.email}
            </Typography>
        </Box>
    );
}
