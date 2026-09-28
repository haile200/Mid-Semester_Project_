import { useEffect, useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { fetchFollowers, fetchFollowing } from '../api';
import PeopleList from './PeopleList';

// Rendered only while open, so each opening loads a fresh list.
export default function FollowListDialog({ userId, kind, onClose }) {
    const [people, setPeople] = useState(null);
    const [error, setError] = useState('');

    useEffect(() => {
        let cancelled = false;
        const load = kind === 'followers' ? fetchFollowers : fetchFollowing;

        load(userId)
            .then((data) => { if (!cancelled) setPeople(data); })
            .catch((loadError) => { if (!cancelled) setError(loadError.message); });

        return () => { cancelled = true; };
    }, [userId, kind]);

    const title = kind === 'followers' ? 'Followers' : 'Following';
    const emptyText = kind === 'followers' ? 'No followers yet.' : 'Not following anyone yet.';

    return (
        <Dialog open onClose={onClose} maxWidth="xs" fullWidth data-cy="follow-list-dialog">
            <DialogTitle>{title}</DialogTitle>
            <DialogContent>
                {error && <Typography className="people-message people-message--error">{error}</Typography>}
                {!error && people === null && (
                    <Box className="people-loading"><CircularProgress size={24} /></Box>
                )}
                {people?.length === 0 && <Typography className="people-message">{emptyText}</Typography>}
                {people?.length > 0 && <PeopleList people={people} onOpen={onClose} />}
            </DialogContent>
        </Dialog>
    );
}
