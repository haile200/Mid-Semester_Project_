import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import { resetPassword } from '../api';
import './Login.css';

export default function ResetPassword({ onPasswordReset }) {
    const navigate = useNavigate();
    const location = useLocation();
    // The token arrives after "#", which browsers never send to a server; read it once on arrival.
    const [token] = useState(() => new URLSearchParams(location.hash.slice(1)).get('token') || '');
    const [password, setPassword] = useState('');
    const [confirmation, setConfirmation] = useState('');
    const [error, setError] = useState('');
    const [done, setDone] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    // Take the token out of the address bar and history, so it is not left behind on a shared computer.
    useEffect(() => {
        if (location.hash) {
            navigate(location.pathname, { replace: true });
        }
    }, [location.hash, location.pathname, navigate]);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError('');

        if (password.length < 8 || password.length > 72) {
            setError('Password must be between 8 and 72 characters.');
            return;
        }
        if (password !== confirmation) {
            setError('The two passwords do not match.');
            return;
        }

        setIsLoading(true);
        try {
            await resetPassword(token, password);
            // Every session of the account was ended on the server, including this browser's.
            onPasswordReset();
            setDone(true);
        } catch (resetError) {
            setError(resetError.message || 'Could not reset the password.');
        } finally {
            setIsLoading(false);
        }
    };

    let content;
    if (done) {
        content = (
            <>
                <Typography variant="body2" className="login-success" data-cy="reset-done">
                    Your password has been changed, and you have been logged out everywhere.
                </Typography>
                <Button fullWidth variant="contained" onClick={() => navigate('/login')} className="login-submit-button">
                    Go to login
                </Button>
            </>
        );
    } else if (!token) {
        content = (
            <Typography variant="body2" className="login-error">
                This reset link is incomplete. Please ask for a new one.
            </Typography>
        );
    } else {
        content = (
            <Box component="form" onSubmit={handleSubmit} noValidate>
                <Typography variant="body2" className="login-field-label">New password</Typography>
                <Box className="login-field">
                    <TextField
                        fullWidth
                        type="password"
                        size="small"
                        autoComplete="new-password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        inputProps={{ 'data-cy': 'reset-password' }}
                    />
                </Box>
                <Typography variant="body2" className="login-field-label">Repeat the new password</Typography>
                <Box className="login-field login-field--last">
                    <TextField
                        fullWidth
                        type="password"
                        size="small"
                        autoComplete="new-password"
                        value={confirmation}
                        onChange={(e) => setConfirmation(e.target.value)}
                        inputProps={{ 'data-cy': 'reset-confirmation' }}
                    />
                </Box>
                <Button
                    fullWidth
                    type="submit"
                    variant="contained"
                    disabled={isLoading}
                    className="login-submit-button"
                    data-cy="reset-submit"
                >
                    {isLoading ? 'Saving...' : 'Set new password'}
                </Button>
            </Box>
        );
    }

    return (
        <Box className="login-page">
            <Card className="login-card">
                <Typography variant="h5" className="login-title">Choose a new password</Typography>
                <Typography variant="body2" className="login-subtitle">At least 8 characters.</Typography>

                {error && <Typography variant="body2" className="login-error" data-cy="reset-error">{error}</Typography>}
                {content}

                {!done && (
                    <Button variant="text" onClick={() => navigate('/forgot-password')} className="login-text-button">
                        Ask for a new link
                    </Button>
                )}
            </Card>
        </Box>
    );
}
