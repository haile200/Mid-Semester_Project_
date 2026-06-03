import React from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import { Avatar as MuiAvatar } from '@mui/material';

export default function User({ id, name, email, postCount, profile_picture }) {
    const navigate = useNavigate();

    return (
        <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            padding: '16px 24px',
            backgroundColor: 'white', 
            borderRadius: '8px', 
            marginBottom: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
            border: '1px solid #f0f0f0'
        }}>
            <Box sx={{ width: '10%', display: 'flex', justifyContent: 'center' }}>
                <MuiAvatar 
                    src={profile_picture || ''} 
                    alt={name}
                    sx={{ width: 40, height: 40 }}
                >
                    {name ? name[0].toUpperCase() : 'U'}
                </MuiAvatar>
            </Box>
            
            <Box sx={{ width: '25%' }}>
                <Typography fontWeight="bold">{name}</Typography>
                <Typography variant="body2" color="text.secondary">{email}</Typography>
            </Box>
            
            <Typography sx={{ width: '20%', textAlign: 'center' }}>
                {postCount || 0}
            </Typography>
            
            <Box sx={{ width: '45%', display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                    variant="contained" 
                    size="small"
                    onClick={() => navigate(`/user-posts/${id}`)}
                    sx={{ 
                        backgroundColor: '#7b61ff', 
                        textTransform: 'none',
                        borderRadius: '20px',
                        px: 3
                    }}
                >
                    See Posts
                </Button>
            </Box>
        </Box>
    );
}