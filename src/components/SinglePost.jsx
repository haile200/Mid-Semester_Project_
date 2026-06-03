import React from 'react';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Avatar from './Avatar'; // Assuming you kept the original Avatar here, or you can switch to MuiAvatar if you prefer


export default function SinglePost({ title, author, body, imageUrl, createdAt }) {
    // A helper function to make relative time look nice (e.g., "2 hours ago")
    const getTimeAgo = (dateString) => {
        if (!dateString) return '';
        
        // Ensure the date is parsed correctly.
        // Some backends might send a date that needs to be appended with 'Z' to indicate UTC.
        // If your database stores times in UTC but doesn't send the 'Z', add it.
        const postDate = new Date(dateString.endsWith('GMT') ? dateString : dateString + 'Z');
        const now = new Date();
        const seconds = Math.floor((now - postDate) / 1000);

        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days} day${days !== 1 ? 's' : ''} ago`;
        const months = Math.floor(days / 30);
        if (months < 12) return `${months} month${months !== 1 ? 's' : ''} ago`;
        const years = Math.floor(months / 12);
        return `${years} year${years !== 1 ? 's' : ''} ago`;
    };

    return (
        <Card sx={{ 
            p: 3, 
            borderRadius: '12px', 
            boxShadow: '0 4px 12px rgba(123, 97, 255, 0.1)',
            mb: 2,
            transition: 'box-shadow 0.2s ease',
            '&:hover': {
                boxShadow: '0 6px 16px rgba(123, 97, 255, 0.2)'
            }
        }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {/* Fallback to first letter if profile picture isn't passed here */}
                <Avatar name={author || 'User'} size={40} />
                <Box sx={{ ml: 2, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                        {author || 'Unknown Author'}
                    </Typography>
                    {createdAt && (
                        <Typography variant="caption" color="text.secondary">
                            {getTimeAgo(createdAt)}
                        </Typography>
                    )}
                </Box>
            </Box>

            {/* Post Title */}
            <Typography variant="h6" fontWeight="bold" gutterBottom>
                {title}
            </Typography>

            {/* Post Image (if any) */}
            {imageUrl && (
                <Box sx={{ width: '100%', maxHeight: '400px', overflow: 'hidden', borderRadius: '8px', mb: 2 }}>
                    <img 
                        src={imageUrl} 
                        alt="Post attachment" 
                        style={{ width: '100%', height: 'auto', display: 'block' }} 
                        onError={(e) => { e.target.style.display = 'none'; }}
                    />
                </Box>
            )}

            {/* Post Body - Rendered as HTML to support WYSIWYG formatting */}
            <Box 
                sx={{ 
                    color: '#444', 
                    fontSize: '15px', 
                    lineHeight: 1.6,
                    '& p': { margin: '0 0 10px 0' }, // basic styling for paragraphs from the editor
                    '& a': { color: '#7b61ff', textDecoration: 'none' } // basic styling for links
                }}
                dangerouslySetInnerHTML={{ __html: body }} 
            />
        </Card>
    );
}