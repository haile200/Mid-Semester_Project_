import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import TerrainIcon from '@mui/icons-material/Terrain';
import { useNavigate } from 'react-router-dom';
import { signup } from '../api';
import './Signup.css';

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
        <Box className="signup-page">
            <Card className="signup-card">
                <Box className="signup-logo-row">
                    <Box className="signup-logo-circle">
                        <TerrainIcon className="signup-logo-icon" />
                    </Box>
                </Box>
                <Typography variant="h5" className="signup-title">
                    Join the crew
                </Typography>
                <Typography variant="body2" className="signup-subtitle">
                    Share your sends, projects, and beta
                </Typography>

                {message ? (
                    <Typography variant="body2" className="signup-error">
                        {message}
                    </Typography>
                ) : null}

                <Typography variant="body2" className="signup-field-label">Name</Typography>
                <Box className="signup-field" data-cy="signup-name">
                    <TextField
                        fullWidth
                        placeholder="Your name"
                        size="small"
                        value={name}
                        name="signupName"
                        onChange={(e) => setName(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" className="signup-field-label">Email</Typography>
                <Box className="signup-field" data-cy="signup-email">
                    <TextField
                        fullWidth
                        placeholder="you@example.com"
                        size="small"
                        value={email}
                        name="signupEmail"
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" className="signup-field-label">Password</Typography>
                <Box className="signup-field" data-cy="signup-password">
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

                <Typography variant="body2" className="signup-field-label">Repeat Password</Typography>
                <Box className="signup-field signup-field--last" data-cy="signup-confirm-password">
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
                    className="signup-submit-button"
                >
                    {isLoading ? 'Creating account...' : 'Sign Up'}
                </Button>

                <Typography variant="body2" className="signup-footer-text">
                    Already have an account?{' '}
                    <span
                        className="signup-login-link"
                        onClick={() => navigate('/login')}
                    >
                        Login
                    </span>
                </Typography>
            </Card>
        </Box>
    );
}
