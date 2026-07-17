import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import { useNavigate } from 'react-router-dom';

export default function TopBar({ currentUser, onLogout }) {
    const navigate = useNavigate();

    return (
        <AppBar position="static" sx={{ backgroundColor: '#3517c9', boxShadow: 'none' }}>
            <Toolbar>
                <Typography 
                    variant="h6" 
                    component="div" 
                    onClick={() => navigate('/')}
                    sx={{ fontWeight: 'bold', cursor: 'pointer', mr: 3 }}
                >
                    MyApp
                </Typography>

                {/* Yellow New Post button */}
                <Button 
                    onClick={() => navigate('/new-post')}
                    sx={{ 
                        backgroundColor: '#ffb300', 
                        color: 'black', 
                        textTransform: 'none', 
                        fontWeight: 'bold',
                        borderRadius: '20px',
                        px: 2,
                        '&:hover': { backgroundColor: '#ffa000' }
                    }}
                >
                    + New Post
                </Button>

                {/* Spacer to push the rest of the buttons to the right */}
                <Box sx={{ flexGrow: 1 }} />

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Button color="inherit" onClick={() => navigate('/')} sx={{ textTransform: 'none' }}>Home</Button>
                    <Button color="inherit" onClick={() => navigate('/users')} sx={{ textTransform: 'none' }}>Users</Button>
                    
                    {/* Added About link exactly where you wanted it */}
                    <Button color="inherit" onClick={() => navigate('/about')} sx={{ textTransform: 'none' }}>About</Button>
                    
                    {currentUser ? (
                        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', ml: 1 }}>
                            {/* Display email instead of name to match your picture */}
                            <Typography
                                data-cy="profile-link"
                                onClick={() => navigate('/profile')}
                                sx={{ color: '#fff', fontSize: '14px', lineHeight: 1.2, cursor: 'pointer' }}
                            >
                                {currentUser.email}
                            </Typography>
                            <Button 
                                color="inherit" 
                                data-cy="logout-button"
                                onClick={onLogout} 
                                sx={{ 
                                    color: '#ffd700', 
                                    textTransform: 'none', 
                                    fontWeight: 'bold', 
                                    padding: 0, 
                                    minWidth: 'auto',
                                    fontSize: '14px' 
                                }}
                            >
                                Logout
                            </Button>
                        </Box>
                    ) : (
                        /* Removed Signup to match the layout in the image */
                        <Button color="inherit" data-cy="topbar-login" onClick={() => navigate('/login')} sx={{ textTransform: 'none' }}>Login</Button>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
}