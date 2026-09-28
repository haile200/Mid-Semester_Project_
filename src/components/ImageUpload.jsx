import { useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import { uploadImage } from '../api';
import './ImageUpload.css';

const MAX_BYTES = 5 * 1024 * 1024;
const ACCEPTED_TYPES = 'image/jpeg,image/png,image/webp';

// Uploads one image and passes its URL to onUploaded. The server checks everything again;
// the check here only gives a faster message before a large file is sent.
export default function ImageUpload({ onUploaded, disabled = false, label = 'Upload photo' }) {
    const inputRef = useRef(null);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = async (event) => {
        const file = event.target.files[0];
        // Cleared so that choosing the same file again still counts as a change.
        event.target.value = '';
        if (!file) return;

        setError('');
        if (file.size > MAX_BYTES) {
            setError('Images can be up to 5 MB.');
            return;
        }

        setIsUploading(true);
        try {
            const { url } = await uploadImage(file);
            onUploaded(url);
        } catch (uploadError) {
            setError(uploadError.message || 'Upload failed.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <Box className="image-upload">
            <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED_TYPES}
                hidden
                onChange={handleChange}
                data-cy="image-upload-input"
            />
            <Button
                variant="outlined"
                size="small"
                startIcon={<AddPhotoAlternateIcon />}
                disabled={disabled || isUploading}
                onClick={() => inputRef.current.click()}
                className="image-upload-button"
            >
                {isUploading ? 'Uploading...' : label}
            </Button>
            {error && <Typography variant="body2" className="image-upload-error" data-cy="image-upload-error">{error}</Typography>}
        </Box>
    );
}
