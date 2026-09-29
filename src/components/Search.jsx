import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import InputAdornment from '@mui/material/InputAdornment';
import SearchIcon from '@mui/icons-material/Search';
import './Search.css';

export default function Search({ onSearch }) {
    return (
        <Box className="search-bar">
            <TextField
                fullWidth
                size="small"
                placeholder="Search climbers..."
                variant="outlined"
                onChange={(e) => onSearch(e.target.value)}
                className="search-input"
                slotProps={{
                    input: {
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon className="search-icon" />
                            </InputAdornment>
                        ),
                    },
                }}
            />
        </Box>
    );
}
