import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export default function About() {
    return (
        <Box sx={{ backgroundColor: '#fdfdfd', minHeight: '100vh', py: 6 }}>
            <Box sx={{ maxWidth: '800px', margin: '0 auto', p: 4, textAlign: 'center', backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)' }}>
                <Typography variant="h4" sx={{ mb: 3, fontWeight: '600', color: '#333' }}>
                    About Us
                </Typography>
                <Typography variant="body1" sx={{ color: '#555', lineHeight: 1.8 }}>
                    Welcome to our platform. This application allows users to share posts, 
                    view other users' profiles, and engage with community content.
                </Typography>
            </Box>
        </Box>
    );
}