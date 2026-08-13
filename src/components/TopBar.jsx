import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import TerrainIcon from '@mui/icons-material/Terrain';
import { useNavigate } from 'react-router-dom';
import { climb } from '../theme';

export default function TopBar({ currentUser, onLogout }) {
    const navigate = useNavigate();

    const navButtonSx = {
        textTransform: 'none',
        color: climb.chalk,
        minWidth: 'auto',
        px: { xs: 1, sm: 1.5 },
        '&:hover': { backgroundColor: climb.rockHover },
    };

    return (
        // Sticky dark-rock bar: stays reachable while scrolling a long feed one-handed at the gym
        <AppBar position="sticky" sx={{ backgroundColor: climb.rock, boxShadow: '0 1px 0 rgba(0,0,0,0.25)' }}>
            <Toolbar sx={{ gap: 1, minHeight: { xs: 56 }, px: { xs: 1.5, sm: 3 } }}>
                <Box
                    onClick={() => navigate('/')}
                    sx={{ display: 'flex', alignItems: 'center', gap: 0.75, cursor: 'pointer', mr: { xs: 0.5, sm: 2 } }}
                >
                    <TerrainIcon sx={{ color: climb.coral, fontSize: 26 }} />
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '18px', letterSpacing: '-0.02em' }}>
                        My Beta
                    </Typography>
                </Box>

                {/* Coral pill = the one energetic accent, reserved for the main action */}
                <Button
                    onClick={() => navigate('/new-post')}
                    sx={{
                        backgroundColor: climb.coral,
                        color: climb.onCoral,
                        textTransform: 'none',
                        fontWeight: 'bold',
                        borderRadius: '999px',
                        px: 2,
                        fontSize: '13px',
                        whiteSpace: 'nowrap',
                        '&:hover': { backgroundColor: climb.coralHover },
                    }}
                >
                    + New Post
                </Button>

                <Box sx={{ flexGrow: 1 }} />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 0, sm: 0.5 } }}>
                    <Button sx={navButtonSx} onClick={() => navigate('/')}>Home</Button>
                    <Button sx={navButtonSx} onClick={() => navigate('/users')}>Community</Button>
                    <Button sx={{ ...navButtonSx, display: { xs: 'none', sm: 'inline-flex' } }} onClick={() => navigate('/about')}>About</Button>

                    {currentUser ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', ml: 1 }}>
                            <Typography
                                data-cy="profile-link"
                                onClick={() => navigate('/profile')}
                                sx={{
                                    color: climb.chalk,
                                    fontSize: '13px',
                                    lineHeight: 1.2,
                                    cursor: 'pointer',
                                    maxWidth: { xs: '110px', sm: '220px' },
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    '&:hover': { color: climb.coral },
                                }}
                            >
                                {currentUser.email}
                            </Typography>
                            <Button
                                color="inherit"
                                data-cy="logout-button"
                                onClick={onLogout}
                                sx={{
                                    color: climb.coral,
                                    textTransform: 'none',
                                    fontWeight: 'bold',
                                    padding: 0,
                                    minWidth: 'auto',
                                    fontSize: '13px',
                                }}
                            >
                                Logout
                            </Button>
                        </Box>
                    ) : (
                        <Button color="inherit" data-cy="topbar-login" onClick={() => navigate('/login')} sx={navButtonSx}>
                            Login
                        </Button>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
}
