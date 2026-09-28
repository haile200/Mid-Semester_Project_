import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import { Avatar as MuiAvatar } from '@mui/material';
import './PeopleList.css';

// A compact list of people; each row opens that person's profile. `renderAction` adds a button per row.
export default function PeopleList({ people, subtitle, renderAction, onOpen }) {
    const navigate = useNavigate();

    const open = (person) => {
        onOpen?.();
        navigate(`/user-posts/${person.id}`);
    };

    return (
        <Box className="people-list">
            {people.map((person) => (
                <Box key={person.id} className="people-row" data-cy="people-row">
                    <Box className="people-identity" onClick={() => open(person)}>
                        <MuiAvatar src={person.profile_picture || ''} alt={person.name} className="people-avatar">
                            {person.name ? person.name[0].toUpperCase() : 'U'}
                        </MuiAvatar>
                        <Box className="people-text">
                            <Box className="people-name-row">
                                <Typography className="people-name">{person.name}</Typography>
                                {person.is_bot && <Chip label="bot" size="small" className="people-bot-chip" />}
                            </Box>
                            {subtitle && <Typography className="people-subtitle">{subtitle(person)}</Typography>}
                        </Box>
                    </Box>
                    {renderAction?.(person)}
                </Box>
            ))}
        </Box>
    );
}
