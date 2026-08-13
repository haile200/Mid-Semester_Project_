import React from 'react';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';
import { climb } from '../theme';

export default function Search({ onSearch }) {
    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
            <TextField
                fullWidth
                size="small"
                placeholder="Search climbers..."
                variant="outlined"
                onChange={(e) => onSearch(e.target.value)}
                sx={{
                    backgroundColor: 'white',
                    borderRadius: '999px',
                    '& .MuiOutlinedInput-root': {
                        borderRadius: '999px',
                        '& fieldset': { borderColor: '#EDEBE4' },
                        '&:hover fieldset': { borderColor: climb.coral },
                    },
                }}
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon sx={{ color: climb.stone, fontSize: 20 }} />
                            </InputAdornment>
                        ),
                    },
                }}
            />
        </Box>
    );
}
