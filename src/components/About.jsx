import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import './About.css';

export default function About() {
    return (
        <Box className="about-page">
            <Box className="about-card">
                <Typography variant="h4" className="about-title">
                    About Us
                </Typography>
                <Typography variant="body1" className="about-text">
                    Welcome to our platform. This application allows users to share posts,
                    view other users' profiles, and engage with community content.
                </Typography>
            </Box>
        </Box>
    );
}
