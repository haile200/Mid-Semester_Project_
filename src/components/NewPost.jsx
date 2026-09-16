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
import './NewPost.css';

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
        <Box className="new-post-page">
            <Card className="new-post-card">
                <Typography variant="h5" className="new-post-title">
                    New Post
                </Typography>

                {activeUser ? (
                    <Typography variant="body2" className="new-post-author-note">
                        Posting as <strong>{activeUser.name}</strong>
                    </Typography>
                ) : (
                    <Typography variant="body2" className="new-post-login-required">
                        You must be logged in to publish a post.
                    </Typography>
                )}

                {message && (
                    <Typography variant="body2" className="new-post-error">
                        {message}
                    </Typography>
                )}

                <Typography variant="body2" className="new-post-label">Title</Typography>
                <TextField
                    fullWidth
                    placeholder="What did you climb?"
                    size="small"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="new-post-input"
                    disabled={!activeUser || isLoading}
                />

                {/* Style and grade chips - gym-tag style pickers, visual metadata for now */}
                <Typography variant="body2" className="new-post-label">Style</Typography>
                <Box className="new-post-chip-row">
                    {CLIMB_STYLES.map((style) => (
                        <Chip
                            key={style}
                            label={style}
                            onClick={() => setClimbStyle(style)}
                            className={`new-post-chip new-post-style-chip${climbStyle === style ? ' new-post-style-chip--selected' : ''}`}
                        />
                    ))}
                </Box>

                <Typography variant="body2" className="new-post-label">Grade</Typography>
                <Box className="new-post-chip-row">
                    {CLIMB_GRADES.map((grade) => (
                        <Chip
                            key={grade}
                            label={grade}
                            onClick={() => setClimbGrade(grade)}
                            className={`new-post-chip new-post-grade-chip${climbGrade === grade ? ' new-post-grade-chip--selected' : ''}`}
                        />
                    ))}
                </Box>

                <Typography variant="body2" className="new-post-label">Image URL (Optional)</Typography>
                <TextField
                    fullWidth
                    placeholder="https://example.com/image.jpg"
                    size="small"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    className="new-post-input"
                    disabled={!activeUser || isLoading}
                />

                <Typography variant="body2" className="new-post-label">Body</Typography>
                <Box className="new-post-editor">
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
                    className="new-post-submit-button"
                >
                    {isLoading ? 'Posting...' : 'Post climb'}
                </Button>

                {!activeUser && (
                    <Button
                        fullWidth
                        variant="text"
                        onClick={() => navigate('/login')}
                        className="new-post-login-button"
                    >
                        Go to login
                    </Button>
                )}
            </Card>
        </Box>
    );
}
