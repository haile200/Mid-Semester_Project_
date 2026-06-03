import React from 'react';
import Box from '@mui/material/Box';

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
    const initials = getInitials(name);

    return (
        <Box
            sx={{
                width: size,
                height: size,
                borderRadius: '50%',
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: '#7b61ff',
                color: 'white',
                fontWeight: 'bold',
                fontSize: `${size / 2.5}px`,
                flexShrink: 0,
                border: '2px solid #f0f0f0',
                boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            }}
        >
            <img
                src={avatarUrl}
                alt={name}
                style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                }}
                onError={(e) => {
                    // Fallback if image fails to load
                    e.target.style.display = 'none';
                }}
            />
        </Box>
    );
}
