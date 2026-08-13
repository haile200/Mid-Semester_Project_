import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import TerrainIcon from '@mui/icons-material/Terrain';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';
import { climb } from '../theme';

export default function Login({ onLogin }) {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setMessage('');

        if (!email.trim() || !password) {
            setMessage('Please enter your email and password.');
            return;
        }

        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
            setMessage('Please enter a valid email address.');
            return;
        }

        setIsLoading(true);
        window.__loginAttempt = { email, password };
        console.debug('Login handleSubmit', { email, password });
        try {
            const response = await login(email, password);
            window.__loginResponse = response;
            console.debug('Login response', response);
            localStorage.setItem('currentUser', JSON.stringify(response.user));
            localStorage.setItem('userId', response.user.id);
            
            if (typeof onLogin === 'function') {
                onLogin(response.user);
            }
            navigate('/');
        } catch (error) {
            window.__loginError = error.message || 'Login failed.';
            console.error('Login failed', error);
            setMessage(error.message || 'Login failed.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', backgroundColor: climb.page, px: 2 }}>
            <Card sx={{ padding: 4, width: '400px', maxWidth: '100%', borderRadius: '16px', border: '1px solid #EDEBE4', boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)' }}>
                {/* Chalk circle with the mountain mark - the brand moment of the page */}
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 1.5 }}>
                    <Box sx={{ width: 56, height: 56, borderRadius: '50%', backgroundColor: climb.coralTint, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <TerrainIcon sx={{ color: climb.coralDark, fontSize: 30 }} />
                    </Box>
                </Box>
                <Typography variant="h5" align="center" fontWeight="bold" gutterBottom>
                    Welcome back, climber
                </Typography>
                <Typography variant="body2" align="center" sx={{ mb: 3, color: climb.stone }}>
                    Log in to find your next project
                </Typography>

                {message ? (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                ) : null}

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Email</Typography>
                <Box sx={{ mb: 2 }} data-cy="login-email">
                    <TextField
                        fullWidth
                        placeholder="you@example.com"
                        size="small"
                        value={email}
                        name="loginEmail"
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Password</Typography>
                <Box sx={{ mb: 3 }} data-cy="login-password">
                    <TextField
                        fullWidth
                        type="password"
                        placeholder="........"
                        size="small"
                        value={password}
                        name="loginPassword"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </Box>

                <Button
                    fullWidth
                    variant="contained"
                    disabled={isLoading}
                    data-cy="login-submit"
                    onClick={handleSubmit}
                    sx={{ backgroundColor: climb.rock, textTransform: 'none', py: 1.5, mb: 2, borderRadius: '999px', fontWeight: 'bold', boxShadow: 'none', '&:hover': { backgroundColor: climb.rockHover, boxShadow: 'none' } }}
                >
                    {isLoading ? 'Logging in...' : 'Login'}
                </Button>

                <Divider sx={{ mb: 2, fontSize: '12px', color: 'text.secondary' }}>OR</Divider>

                <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => navigate('/signup')}
                    sx={{ textTransform: 'none', py: 1.5, borderRadius: '999px', color: climb.coralDark, borderColor: climb.coral, fontWeight: 'bold', '&:hover': { borderColor: climb.coralDark, backgroundColor: climb.coralTint } }}
                >
                    Join the crew
                </Button>
            </Card>
        </Box>
    );
}