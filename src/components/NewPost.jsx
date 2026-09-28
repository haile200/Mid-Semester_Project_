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
import SpellcheckIcon from '@mui/icons-material/Spellcheck';
import { createPost, suggestCorrection } from '../api';
import { hasFormatting, htmlToParagraphs, paragraphsToHtml } from '../writingHelp';
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
    // Suggested fixes are only shown; nothing changes until the author presses Apply.
    const [suggestion, setSuggestion] = useState(null);
    const [isChecking, setIsChecking] = useState(false);
    const [checkMessage, setCheckMessage] = useState('');

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

    const bodyText = htmlToParagraphs(body);
    const hasTextToCheck = Boolean(title.trim() || bodyText.trim());

    const handleCheckWriting = async () => {
        setSuggestion(null);
        setCheckMessage('');
        setIsChecking(true);
        try {
            const [fixedTitle, fixedBody] = await Promise.all([
                title.trim() ? suggestCorrection(title).then((data) => data.text) : title,
                bodyText.trim() ? suggestCorrection(bodyText).then((data) => data.text) : bodyText,
            ]);
            const changes = {};
            if (fixedTitle !== title) changes.title = fixedTitle;
            if (fixedBody !== bodyText) changes.body = fixedBody;
            if (Object.keys(changes).length) {
                setSuggestion(changes);
            } else {
                setCheckMessage('Looks good - no changes suggested.');
            }
        } catch (error) {
            setCheckMessage(error.message || 'Could not check the writing.');
        } finally {
            setIsChecking(false);
        }
    };

    const applySuggestion = (field) => {
        if (field === 'title') setTitle(suggestion.title);
        if (field === 'body') setBody(paragraphsToHtml(suggestion.body));
        const remaining = { ...suggestion };
        delete remaining[field];
        setSuggestion(Object.keys(remaining).length ? remaining : null);
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

                <Box className="new-post-check-row">
                    <Button
                        variant="outlined"
                        startIcon={<SpellcheckIcon />}
                        disabled={!activeUser || isLoading || isChecking || !hasTextToCheck}
                        onClick={handleCheckWriting}
                        className="new-post-check-button"
                        data-cy="check-writing"
                    >
                        {isChecking ? 'Checking...' : 'Check writing'}
                    </Button>
                    {checkMessage && (
                        <Typography variant="body2" className="new-post-check-message">{checkMessage}</Typography>
                    )}
                </Box>

                {suggestion && (
                    <Box className="new-post-suggestion" data-cy="writing-suggestion">
                        <Typography className="new-post-suggestion-heading">Suggested fixes</Typography>

                        {suggestion.title !== undefined && (
                            <Box className="new-post-suggestion-item">
                                <Typography className="new-post-suggestion-label">Title</Typography>
                                <Typography className="new-post-suggestion-text">{suggestion.title}</Typography>
                                <Button size="small" className="new-post-apply-button" onClick={() => applySuggestion('title')}>
                                    Apply
                                </Button>
                            </Box>
                        )}

                        {suggestion.body !== undefined && (
                            <Box className="new-post-suggestion-item">
                                <Typography className="new-post-suggestion-label">Text</Typography>
                                <Typography className="new-post-suggestion-text">{suggestion.body}</Typography>
                                {hasFormatting(body) && (
                                    <Typography className="new-post-suggestion-note">
                                        Applying removes bold, italic, underline and links.
                                    </Typography>
                                )}
                                <Button size="small" className="new-post-apply-button" onClick={() => applySuggestion('body')}>
                                    Apply
                                </Button>
                            </Box>
                        )}

                        <Button size="small" className="new-post-dismiss-button" onClick={() => setSuggestion(null)}>
                            Dismiss
                        </Button>
                    </Box>
                )}

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
