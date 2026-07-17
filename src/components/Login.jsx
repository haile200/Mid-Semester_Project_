import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';

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
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
            <Card sx={{ padding: 4, width: '400px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <Typography variant="h5" align="center" fontWeight="bold" gutterBottom>
                    Welcome Back
                </Typography>
                <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
                    Sign in to your account
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
                    sx={{ backgroundColor: '#4423ea', textTransform: 'none', py: 1.5, mb: 2, borderRadius: '8px' }}
                >
                    {isLoading ? 'Logging in...' : 'Login'}
                </Button>

                <Divider sx={{ mb: 2, fontSize: '12px', color: 'text.secondary' }}>OR</Divider>

                <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => navigate('/signup')}
                    sx={{ textTransform: 'none', py: 1.5, borderRadius: '8px', color: '#7b61ff', borderColor: '#7b61ff' }}
                >
                    Sign Up
                </Button>
            </Card>
        </Box>
    );
}