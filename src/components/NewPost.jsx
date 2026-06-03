import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
// FIXED IMPORTS: using react-quill-new instead of react-quill
import ReactQuill from 'react-quill-new'; 
import 'react-quill-new/dist/quill.snow.css'; 
import { createPost } from '../api';

export default function NewPost({ currentUser }) {
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [imageUrl, setImageUrl] = useState(''); 
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const storedUser = currentUser || JSON.parse(localStorage.getItem('currentUser') || 'null');
    const activeUser = storedUser;

    // Define the modules for the Quill editor toolbar
    const modules = {
        toolbar: [
            ['bold', 'italic', 'underline'], 
            ['link'], 
            ['clean'] 
        ],
    };

    const handleSubmit = async (event) => {
        event.preventDefault();
        setMessage('');

        if (!activeUser) {
            setMessage('Please login before creating a post.');
            return;
        }

        // Check if body is empty
        if (!title.trim() || !body.trim() || body === '<p><br></p>') {
            setMessage('Title and body are required.');
            return;
        }

        setIsLoading(true);
        try {
            await createPost(title, body, activeUser.id, imageUrl);
            navigate('/');
        } catch (error) {
            setMessage(error.message || 'Failed to create post.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', py: 4 }}>
            <Card sx={{ padding: 4, width: '700px', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
                <Typography variant="h5" align="center" fontWeight="bold" gutterBottom sx={{ mb: 4 }}>
                    Create New Post
                </Typography>

                {activeUser ? (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Posting as <strong>{activeUser.name}</strong>
                    </Typography>
                ) : (
                    <Typography variant="body2" color="error" sx={{ mb: 3 }}>
                        You must be logged in to publish a post.
                    </Typography>
                )}

                {message && (
                    <Typography variant="body2" color="error" sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                )}

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Title</Typography>
                <TextField
                    fullWidth
                    placeholder="Enter post title..."
                    size="small"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    sx={{ mb: 3 }}
                    disabled={!activeUser || isLoading}
                />
                
                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Image URL (Optional)</Typography>
                <TextField
                    fullWidth
                    placeholder="https://example.com/image.jpg"
                    size="small"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    sx={{ mb: 3 }}
                    disabled={!activeUser || isLoading}
                />

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Body</Typography>
                <Box sx={{ 
                    mb: 4, 
                    '.ql-container': { minHeight: '200px', fontSize: '16px' } 
                }}>
                    <ReactQuill 
                        theme="snow" 
                        value={body} 
                        onChange={setBody} 
                        modules={modules}
                        placeholder="Write your post content here..."
                        readOnly={!activeUser || isLoading}
                    />
                </Box>

                <Button
                    fullWidth
                    variant="contained"
                    disabled={!activeUser || isLoading}
                    onClick={handleSubmit}
                    sx={{ backgroundColor: '#5c6bc0', textTransform: 'none', py: 1.5, borderRadius: '8px', fontWeight: 'bold' }}
                >
                    {isLoading ? 'Publishing...' : 'Publish'}
                </Button>

                {!activeUser && (
                    <Button
                        fullWidth
                        variant="text"
                        onClick={() => navigate('/login')}
                        sx={{ mt: 2, textTransform: 'none' }}
                    >
                        Go to login
                    </Button>
                )}
            </Card>
        </Box>
    );
}