import Box from '@mui/material/Box';
import './Avatar.css';

export default function Avatar({ name = 'User', profileImage = null, size = 40 }) {
    // Generate initials from name
    const getInitials = (fullName) => {
        return fullName
            .split(' ')
            .map(word => word.charAt(0).toUpperCase())
            .join('')
            .slice(0, 2);
    };

    // Generate UI Avatars URL with initials
    const getAvatarUrl = (userName) => {
        const initials = getInitials(userName);
        return `https://ui-avatars.com/api/?name=${encodeURIComponent(initials)}&background=7b61ff&color=fff&bold=true&size=${size}`;
    };

    const avatarUrl = profileImage || getAvatarUrl(name);

    return (
        <Box className="avatar-circle">
            <img
                src={avatarUrl}
                alt={name}
                className="avatar-image"
                onError={(e) => {
                    // Fallback if image fails to load
                    e.target.style.display = 'none';
                }}
            />
        </Box>
    );
}
