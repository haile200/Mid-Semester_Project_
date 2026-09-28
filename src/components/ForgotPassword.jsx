import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { requestPasswordReset } from '../api';
import './Login.css';

export default function ForgotPassword() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [sentMessage, setSentMessage] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');

        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())) {
            setError('Please enter a valid email address.');
            return;
        }

        setIsLoading(true);
        try {
            const data = await requestPasswordReset(email.trim());
            setSentMessage(data.message);
        } catch (requestError) {
            setError(requestError.message || 'Could not send the reset email.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box className="login-page">
            <Card className="login-card">
                <Typography variant="h5" className="login-title">Forgot your password?</Typography>
                <Typography variant="body2" className="login-subtitle">
                    Enter your email and we will send you a link to choose a new one.
                </Typography>

                {error && <Typography variant="body2" className="login-error">{error}</Typography>}

                {sentMessage ? (
                    <Typography variant="body2" className="login-success" data-cy="reset-requested">
                        {sentMessage} Check your inbox and spam folder.
                    </Typography>
                ) : (
                    <Box component="form" onSubmit={handleSubmit} noValidate>
                        <Typography variant="body2" className="login-field-label">Email</Typography>
                        <Box className="login-field login-field--last">
                            <TextField
                                fullWidth
                                type="email"
                                placeholder="you@example.com"
                                size="small"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                inputProps={{ 'data-cy': 'reset-email' }}
                            />
                        </Box>
                        <Button
                            fullWidth
                            type="submit"
                            variant="contained"
                            disabled={isLoading}
                            className="login-submit-button"
                            data-cy="reset-request-submit"
                        >
                            {isLoading ? 'Sending...' : 'Send reset link'}
                        </Button>
                    </Box>
                )}

                <Button variant="text" onClick={() => navigate('/login')} className="login-text-button">
                    Back to login
                </Button>
            </Card>
        </Box>
    );
}
