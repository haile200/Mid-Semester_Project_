import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import { Avatar as MuiAvatar } from '@mui/material';
import { fetchCurrentUser } from '../api';
import './Profile.css';

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
            <Box className="profile-loading">
                <CircularProgress className="profile-loading-spinner" />
            </Box>
        );
    }

    return (
        <Box className="profile-container">
            <Box data-cy="profile-page" className="profile-card">
                {/* Chalk band behind the avatar - the "summit photo" header */}
                <Box className="profile-header">
                    <MuiAvatar
                        src={user.profile_picture || ''}
                        alt={user.name}
                        className="profile-avatar"
                    >
                        {user.name ? user.name[0].toUpperCase() : 'U'}
                    </MuiAvatar>
                    <Typography variant="h5" data-cy="profile-name" className="profile-name">
                        {user.name}
                    </Typography>
                    <Typography data-cy="profile-email" className="profile-email">
                        {user.email}
                    </Typography>
                </Box>

                <Box className="profile-body">
                    <Typography className="profile-section-title">
                        Climbing card
                    </Typography>
                    {/* Placeholder badges until real send data exists on the backend */}
                    <Box className="profile-badges">
                        <Chip label="Boulderer" className="profile-badge profile-badge--discipline" />
                        <Chip label="Working on V5" className="profile-badge profile-badge--project" />
                        <Chip label="Open to beta" className="profile-badge profile-badge--open" />
                    </Box>
                </Box>
            </Box>
        </Box>
    );
}
