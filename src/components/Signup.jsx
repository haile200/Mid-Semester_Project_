import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { useNavigate } from 'react-router-dom';
import { signup } from '../api';

export default function Signup() {
    const navigate = useNavigate();
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setMessage('');

        if (!name.trim() || !email.trim() || !password) {
            setMessage('Please fill in all fields.');
            return;
        }

        if (password !== confirmPassword) {
            setMessage('Passwords do not match.');
            return;
        }

        setIsLoading(true);
        try {
            await signup(name, email, password);
            navigate('/login');
        } catch (error) {
            setMessage(error.message || 'Signup failed.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
            <Card sx={{ padding: 4, width: '420px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <Typography variant="h5" align="center" fontWeight="bold" gutterBottom>
                    Create Account
                </Typography>
                <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
                    Sign up for a new account
                </Typography>

                {message ? (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                ) : null}

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Name</Typography>
                <TextField
                    fullWidth
                    placeholder="Your name"
                    size="small"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    sx={{ mb: 2 }}
                />

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Email</Typography>
                <TextField
                    fullWidth
                    placeholder="you@example.com"
                    size="small"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    sx={{ mb: 2 }}
                />

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Password</Typography>
                <TextField
                    fullWidth
                    type="password"
                    placeholder="........"
                    size="small"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    sx={{ mb: 2 }}
                />

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Repeat Password</Typography>
                <TextField
                    fullWidth
                    type="password"
                    placeholder="........"
                    size="small"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    sx={{ mb: 3 }}
                />

                <Button
                    fullWidth
                    variant="contained"
                    disabled={isLoading}
                    onClick={handleSubmit}
                    sx={{ backgroundColor: '#7b61ff', textTransform: 'none', py: 1.5, mb: 3, borderRadius: '8px' }}
                >
                    {isLoading ? 'Creating account...' : 'Sign Up'}
                </Button>

                <Typography variant="body2" align="center">
                    Already have an account?{' '}
                    <span
                        style={{ color: '#4a29f0', cursor: 'pointer', fontWeight: 'bold' }}
                        onClick={() => navigate('/login')}
                    >
                        Login
                    </span>
                </Typography>
            </Card>
        </Box>
    );
}