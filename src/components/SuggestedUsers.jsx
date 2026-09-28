import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { fetchSuggestions, toggleFollow } from '../api';
import PeopleList from './PeopleList';
import './SuggestedUsers.css';

function reason(person) {
    if (person.mutualCount > 0) {
        return `Followed by ${person.mutualCount} ${person.mutualCount === 1 ? 'person' : 'people'} you follow`;
    }
    return person.followersCount > 0 ? 'Popular climber' : 'New to My Beta';
}

export default function SuggestedUsers() {
    const [people, setPeople] = useState([]);
    const [followingId, setFollowingId] = useState(null);

    useEffect(() => {
        let cancelled = false;
        fetchSuggestions()
            .then((data) => { if (!cancelled) setPeople(data); })
            .catch(() => { if (!cancelled) setPeople([]); });
        return () => { cancelled = true; };
    }, []);

    const handleFollow = async (person) => {
        setFollowingId(person.id);
        try {
            await toggleFollow(person.id, false);
            setPeople((current) => current.filter((p) => p.id !== person.id));
        } finally {
            setFollowingId(null);
        }
    };

    if (people.length === 0) return null;

    return (
        <Box className="suggested-users" data-cy="suggested-users">
            <Typography className="suggested-users-title">Climbers you may know</Typography>
            <PeopleList
                people={people}
                subtitle={reason}
                renderAction={(person) => (
                    <Button
                        size="small"
                        disabled={followingId === person.id}
                        onClick={() => handleFollow(person)}
                        className="suggested-users-follow"
                        data-cy="suggested-follow"
                    >
                        Follow
                    </Button>
                )}
            />
        </Box>
    );
}
