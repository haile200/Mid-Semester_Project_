import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TerrainIcon from '@mui/icons-material/Terrain';
import { useNavigate } from 'react-router-dom';
import './TopBar.css';

export default function TopBar({ currentUser, onLogout }) {
    const navigate = useNavigate();

    return (
        // Sticky dark-rock bar: stays reachable while scrolling a long feed one-handed at the gym
        <AppBar position="sticky" className="topbar">
            <Toolbar className="topbar-toolbar">
                <Box
                    onClick={() => navigate('/')}
                    className="topbar-brand"
                >
                    <TerrainIcon className="topbar-brand-icon" />
                    <Typography variant="h6" className="topbar-brand-title">
                        My Beta
                    </Typography>
                </Box>

                {/* Coral pill = the one energetic accent, reserved for the main action */}
                <Button
                    onClick={() => navigate('/new-post')}
                    className="topbar-new-post-button"
                >
                    + New Post
                </Button>

                <Box className="topbar-spacer" />

                <Box className="topbar-nav">
                    <Button className="topbar-nav-button" onClick={() => navigate('/')}>Home</Button>
                    <Button className="topbar-nav-button" onClick={() => navigate('/users')}>Community</Button>
                    <Button className="topbar-nav-button topbar-nav-button--wide-only" onClick={() => navigate('/about')}>About</Button>
                    {/* A convenience only: the server refuses admin requests from anyone else with 403. */}
                    {currentUser?.is_admin && (
                        <Button className="topbar-nav-button topbar-admin-button" onClick={() => navigate('/admin')} data-cy="admin-link">
                            Admin
                        </Button>
                    )}

                    {currentUser ? (
                        <Box className="topbar-account">
                            <Typography
                                data-cy="profile-link"
                                onClick={() => navigate('/profile')}
                                className="topbar-profile-link"
                            >
                                {currentUser.email}
                            </Typography>
                            <Button
                                color="inherit"
                                data-cy="logout-button"
                                onClick={onLogout}
                                className="topbar-logout-button"
                            >
                                Logout
                            </Button>
                        </Box>
                    ) : (
                        <Button color="inherit" data-cy="topbar-login" onClick={() => navigate('/login')} className="topbar-nav-button">
                            Login
                        </Button>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
}
