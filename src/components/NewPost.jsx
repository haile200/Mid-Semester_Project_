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
import Chip from '@mui/material/Chip';
import { createPost } from '../api';
import { climb } from '../theme';

const CLIMB_STYLES = ['Bouldering', 'Lead', 'Top rope'];
const CLIMB_GRADES = ['V2', 'V3', 'V4', 'V5', 'V6', '6b+', '6c+', '7a'];

export default function NewPost({ currentUser }) {
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [imageUrl, setImageUrl] = useState(''); 
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    // Visual-only climbing metadata until the backend stores grades and styles
    const [climbStyle, setClimbStyle] = useState('Bouldering');
    const [climbGrade, setClimbGrade] = useState('V4');

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
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', py: 4, backgroundColor: climb.page, px: 2 }}>
            <Card sx={{ padding: { xs: 2.5, sm: 4 }, width: '700px', maxWidth: '100%', borderRadius: '16px', border: '1px solid #EDEBE4', boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)' }}>
                <Typography variant="h5" align="center" fontWeight="bold" gutterBottom sx={{ mb: 4, color: climb.rock }}>
                    New Post
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
                    placeholder="What did you climb?"
                    size="small"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    sx={{ mb: 3 }}
                    disabled={!activeUser || isLoading}
                />

                {/* Style and grade chips - gym-tag style pickers, visual metadata for now */}
                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Style</Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
                    {CLIMB_STYLES.map((style) => (
                        <Chip
                            key={style}
                            label={style}
                            onClick={() => setClimbStyle(style)}
                            sx={{
                                fontWeight: 'bold',
                                fontSize: '12px',
                                borderRadius: '999px',
                                backgroundColor: climbStyle === style ? climb.coralTint : 'transparent',
                                color: climbStyle === style ? climb.onCoralTint : climb.stone,
                                border: climbStyle === style ? `1px solid ${climb.coral}` : '1px solid #D3D1C7',
                                '&:hover': { backgroundColor: climb.coralTint },
                            }}
                        />
                    ))}
                </Box>

                <Typography variant="body2" fontWeight="bold" sx={{ mb: 1 }}>Grade</Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
                    {CLIMB_GRADES.map((grade) => (
                        <Chip
                            key={grade}
                            label={grade}
                            onClick={() => setClimbGrade(grade)}
                            sx={{
                                fontWeight: 'bold',
                                fontSize: '12px',
                                borderRadius: '999px',
                                backgroundColor: climbGrade === grade ? climb.rock : 'transparent',
                                color: climbGrade === grade ? climb.chalk : climb.stone,
                                border: climbGrade === grade ? `1px solid ${climb.rock}` : '1px solid #D3D1C7',
                                '&:hover': { backgroundColor: climbGrade === grade ? climb.rockHover : climb.chalk },
                            }}
                        />
                    ))}
                </Box>
                
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
                        placeholder="Describe the problem, the moves, your beta..."
                        readOnly={!activeUser || isLoading}
                    />
                </Box>

                <Button
                    fullWidth
                    variant="contained"
                    disabled={!activeUser || isLoading}
                    onClick={handleSubmit}
                    sx={{ backgroundColor: climb.coral, color: climb.onCoral, textTransform: 'none', py: 1.5, borderRadius: '999px', fontWeight: 'bold', boxShadow: 'none', '&:hover': { backgroundColor: climb.coralHover, boxShadow: 'none' } }}
                >
                    {isLoading ? 'Posting...' : 'Post climb'}
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