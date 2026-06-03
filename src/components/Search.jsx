import React from 'react';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';

export default function Search({ onSearch }) {
    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4, mt: 2 }}>
            <TextField
                placeholder="Search by name or email..."
                variant="outlined"
                onChange={(e) => onSearch(e.target.value)}
                sx={{
                    width: '60%',
                    backgroundColor: 'white',
                    borderRadius: '30px',
                    // Targeting the inner input to round the borders completely
                    '& .MuiOutlinedInput-root': {
                        borderRadius: '30px',
                    }
                }}
                InputProps={{
                    startAdornment: (
                        <InputAdornment position="start">
                            <SearchIcon />
                        </InputAdornment>
                    ),
                }}
            />
        </Box>
    );
}