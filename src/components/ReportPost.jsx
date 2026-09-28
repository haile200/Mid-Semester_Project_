import { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import { reportPost } from '../api';
import { MAX_REPORT_NOTE_LENGTH, REPORT_REASONS } from '../moderation';
import './ReportPost.css';

export default function ReportPost({ postId, onClose }) {
    const [reason, setReason] = useState('');
    const [note, setNote] = useState('');
    const [isSending, setIsSending] = useState(false);
    const [outcome, setOutcome] = useState(null);

    const handleSend = async () => {
        setIsSending(true);
        try {
            await reportPost(postId, reason, note);
            setOutcome({ kind: 'sent', text: 'Thanks. A moderator will review this post.' });
        } catch (error) {
            // A second report is not a failure from the user's point of view; it is already on record.
            const kind = error.message === 'You already reported this post' ? 'sent' : 'error';
            setOutcome({ kind, text: error.message });
        } finally {
            setIsSending(false);
        }
    };

    if (outcome?.kind === 'sent') {
        return (
            <Box className="report-post" data-cy="report-form">
                <Typography className="report-post-done">{outcome.text}</Typography>
            </Box>
        );
    }

    return (
        <Box className="report-post" data-cy="report-form">
            <Typography className="report-post-heading">Why are you reporting this post?</Typography>
            <Box className="report-post-reasons">
                {REPORT_REASONS.map((option) => (
                    <Chip
                        key={option.value}
                        label={option.label}
                        onClick={() => setReason(option.value)}
                        className={`report-post-reason${reason === option.value ? ' report-post-reason--selected' : ''}`}
                        data-cy={`report-reason-${option.value}`}
                    />
                ))}
            </Box>
            <TextField
                fullWidth
                size="small"
                placeholder="Anything a moderator should know? (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                className="report-post-note"
                slotProps={{ htmlInput: { maxLength: MAX_REPORT_NOTE_LENGTH } }}
            />
            {outcome?.kind === 'error' && <Typography className="report-post-error">{outcome.text}</Typography>}
            <Box className="report-post-actions">
                <Button size="small" className="report-post-cancel" onClick={onClose}>Cancel</Button>
                <Button
                    size="small"
                    className="report-post-send"
                    disabled={!reason || isSending}
                    onClick={handleSend}
                    data-cy="report-send"
                >
                    {isSending ? 'Sending...' : 'Send report'}
                </Button>
            </Box>
        </Box>
    );
}
