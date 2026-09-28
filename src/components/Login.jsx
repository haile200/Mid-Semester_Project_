import { useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import TerrainIcon from '@mui/icons-material/Terrain';
import { useNavigate } from 'react-router-dom';
import { login } from '../api';
import './Login.css';

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
        try {
            const response = await login(email, password);
            localStorage.setItem('currentUser', JSON.stringify(response.user));
            localStorage.setItem('userId', response.user.id);

            if (typeof onLogin === 'function') {
                onLogin(response.user);
            }
            navigate('/');
        } catch (error) {
            console.error('Login failed', error);
            setMessage(error.message || 'Login failed.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box className="login-page">
            <Card className="login-card">
                {/* Chalk circle with the mountain mark - the brand moment of the page */}
                <Box className="login-logo-row">
                    <Box className="login-logo-circle">
                        <TerrainIcon className="login-logo-icon" />
                    </Box>
                </Box>
                <Typography variant="h5" className="login-title">
                    Welcome back, climber
                </Typography>
                <Typography variant="body2" className="login-subtitle">
                    Log in to find your next project
                </Typography>

                {message ? (
                    <Typography variant="body2" className="login-error">
                        {message}
                    </Typography>
                ) : null}

                <Typography variant="body2" className="login-field-label">Email</Typography>
                <Box className="login-field" data-cy="login-email">
                    <TextField
                        fullWidth
                        placeholder="you@example.com"
                        size="small"
                        value={email}
                        name="loginEmail"
                        onChange={(e) => setEmail(e.target.value)}
                    />
                </Box>

                <Typography variant="body2" className="login-field-label">Password</Typography>
                <Box className="login-field login-field--last" data-cy="login-password">
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
                    className="login-submit-button"
                >
                    {isLoading ? 'Logging in...' : 'Login'}
                </Button>

                <Button
                    variant="text"
                    onClick={() => navigate('/forgot-password')}
                    className="login-text-button"
                    data-cy="forgot-password"
                >
                    Forgot password?
                </Button>

                <Divider className="login-divider">OR</Divider>

                <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => navigate('/signup')}
                    className="login-signup-button"
                >
                    Join the crew
                </Button>
            </Card>
        </Box>
    );
}
