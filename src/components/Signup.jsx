import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { useNavigate } from 'react-router-dom';
import { signup } from '../api';
import styles from './Signup.module.css';

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

        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
            setMessage('Please enter a valid email address.');
            return;
        }

        if (password.length < 8) {
            setMessage('Password must be at least 8 characters.');
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
                <Box sx={{ mb: 2 }} data-cy="signup-name">
                    <TextField
                        fullWidth
                        placeholder="Your name"
                        size="small"
                        value={name}
                        name="signupName"
                        onChange={(e) => setName(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Email</Typography>
                <Box sx={{ mb: 2 }} data-cy="signup-email">
                    <TextField
                        fullWidth
                        placeholder="you@example.com"
                        size="small"
                        value={email}
                        name="signupEmail"
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Password</Typography>
                <Box sx={{ mb: 2 }} data-cy="signup-password">
                    <TextField
                        fullWidth
                        type="password"
                        placeholder="........"
                        size="small"
                        value={password}
                        name="signupPassword"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Repeat Password</Typography>
                <Box sx={{ mb: 3 }} data-cy="signup-confirm-password">
                    <TextField
                        fullWidth
                        type="password"
                        placeholder="........"
                        size="small"
                        value={confirmPassword}
                        name="signupConfirmPassword"
                        onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                </Box>

                <Button
                    fullWidth
                    variant="contained"
                    disabled={isLoading}
                    data-cy="signup-submit"
                    onClick={handleSubmit}
                    sx={{ backgroundColor: '#7b61ff', textTransform: 'none', py: 1.5, mb: 3, borderRadius: '8px' }}
                >
                    {isLoading ? 'Creating account...' : 'Sign Up'}
                </Button>

                <Typography variant="body2" align="center">
                    Already have an account?{' '}
                    <span
                        className={styles.loginLink}
                        onClick={() => navigate('/login')}
                    >
                        Login
                    </span>
                </Typography>
            </Card>
        </Box>
    );
}