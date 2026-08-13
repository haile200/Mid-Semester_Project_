import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import CircularProgress from '@mui/material/CircularProgress';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import { Avatar as MuiAvatar } from '@mui/material';
import SinglePost from './SinglePost';
import { fetchPosts, fetchUserDetails, toggleFollow, fetchFollowingFeed, fetchFeed, updateProfile } from '../api';
import { climb } from '../theme';

export default function Feed() {
    const { userId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    
    // Extract the ID safely from the currentUser object stored in localStorage
    const storedUserString = localStorage.getItem('currentUser');
    let currentUserId = null;
    if (storedUserString) {
        try {
            const storedUser = JSON.parse(storedUserString);
            if (storedUser && storedUser.id) {
                currentUserId = String(storedUser.id); 
            }
        } catch (e) {
            console.error("Failed to parse currentUser from localStorage", e);
        }
    }
    
    const [posts, setPosts] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [offset, setOffset] = useState(0);
    const [hasMore, setHasMore] = useState(true);
    const [userDetails, setUserDetails] = useState(location.state?.userDetails || null);
    
    const [feedType, setFeedType] = useState(0); 

    // Edit Profile State
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editBio, setEditBio] = useState('');
    const [editProfilePicture, setEditProfilePicture] = useState('');
    const [isSavingProfile, setIsSavingProfile] = useState(false);
    
    const limit = 10;

    const loadPosts = async (currentOffset, isReset = false) => {
        if (isLoading) return; 
        
        // Block loading ONLY if trying to access Following feed while logged out
        if (!userId && feedType === 1 && !currentUserId) {
            if (isReset) {
                setPosts([]);
                setHasMore(false);
            }
            return;
        }
        
        setIsLoading(true);
        setError('');

        try {
            let data = [];
            if (userId) {
                data = await fetchPosts(currentOffset, limit, userId);
            } else {
                if (feedType === 0) {
                    data = await fetchFeed(currentOffset, limit); 
                } else {
                    data = await fetchFollowingFeed(currentOffset, limit);
                }
            }

            if (isReset) {
                setPosts(data);
                setOffset(limit);
            } else {
                setPosts((prev) => [...prev, ...data]);
                setOffset(currentOffset + limit);
            }
            
            setHasMore(data.length === limit);
        } catch (fetchError) {
            setError(fetchError.message || 'Unable to load posts.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleFollowToggle = async () => {
        if (!userDetails) return;
        try {
            await toggleFollow(userId, userDetails.is_following);
            setUserDetails(prev => ({
                ...prev,
                is_following: !prev.is_following,
                followersCount: prev.is_following ? prev.followersCount - 1 : prev.followersCount + 1
            }));
        } catch (err) {
            console.error("Failed to toggle follow status", err);
        }
    };

    const handleOpenEditDialog = () => {
        setEditBio(userDetails?.bio || '');
        setEditProfilePicture(userDetails?.profile_picture || '');
        setIsEditDialogOpen(true);
    };

    const handleSaveProfile = async () => {
        setIsSavingProfile(true);
        try {
            await updateProfile(editBio, editProfilePicture);
            
            setUserDetails(prev => ({
                ...prev,
                bio: editBio,
                profile_picture: editProfilePicture
            }));
            
            // Update localStorage so the Navbar reflects the change immediately
            const storedUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
            storedUser.profile_picture = editProfilePicture;
            localStorage.setItem('currentUser', JSON.stringify(storedUser));
            
            setIsEditDialogOpen(false);
        } catch (err) {
            console.error("Failed to update profile", err);
            alert("Failed to update profile. Make sure you are logged in.");
        } finally {
            setIsSavingProfile(false);
        }
    };

    const handleTabChange = (event, newValue) => {
        setFeedType(newValue);
    };

    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop + 1 >= document.documentElement.scrollHeight) {
                // Do not trigger scroll fetch if viewing Following tab while logged out
                if (!userId && feedType === 1 && !currentUserId) return;

                if (hasMore && !isLoading) {
                    loadPosts(offset);
                }
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [isLoading, hasMore, offset, feedType, userId, currentUserId]);

    useEffect(() => {
        // Only fetch user details if viewing a specific profile
        if (userId) {
            fetchUserDetails(userId)
                .then(user => setUserDetails(user))
                .catch(err => console.error(err));
        } else {
            setUserDetails(null);
        }
    }, [userId]);

    useEffect(() => {
        setHasMore(true);
        loadPosts(0, true);
    }, [userId, feedType, currentUserId]);

    return (
        <Box sx={{ backgroundColor: climb.page, minHeight: '100vh', py: { xs: 2, sm: 4 } }}>
            {userId && (
                <Box sx={{ maxWidth: '1000px', margin: '0 auto', px: 2, mb: 4 }}>
                    {userDetails ? (
                        <Card sx={{
                            backgroundColor: 'white', borderRadius: '14px',
                            border: '1px solid #EDEBE4',
                            boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)', p: 3,
                            display: 'flex', alignItems: 'center', gap: 3,
                            flexWrap: 'wrap'
                        }}>
                            <MuiAvatar 
                                src={userDetails.profile_picture || ''} 
                                alt={userDetails.name}
                                sx={{ width: 80, height: 80, fontSize: '32px', border: `3px solid ${climb.coral}`, backgroundColor: climb.coralTint, color: climb.onCoralTint }}
                            >
                                {userDetails.name ? userDetails.name[0].toUpperCase() : 'U'}
                            </MuiAvatar>
                            <Box sx={{ flex: 1 }}>
                                <Typography variant="h5" sx={{ fontWeight: '600', mb: 0.5 }}>
                                    {userDetails.name}
                                </Typography>
                                {userDetails.bio && (
                                    <Typography sx={{ color: '#555', mb: 1, fontStyle: 'italic' }}>
                                        {userDetails.bio}
                                    </Typography>
                                )}
                                <Typography sx={{ color: climb.coralDark, fontWeight: '500', fontSize: '14px' }}>
                                    {userDetails.postCount} {userDetails.postCount === 1 ? 'Post' : 'Posts'} 
                                    {' • '} 
                                    {userDetails.followersCount || 0} Followers 
                                    {' • '}
                                    {userDetails.followingCount || 0} Following
                                </Typography>
                            </Box>
                            
                            <Box sx={{ display: 'flex', gap: 1, flexDirection: 'column' }}>
                                {currentUserId && String(currentUserId) !== String(userId) && (
                                    <Button 
                                        variant={userDetails.is_following ? "outlined" : "contained"} 
                                        onClick={handleFollowToggle}
                                        sx={{
                                            borderRadius: '999px',
                                            textTransform: 'none',
                                            fontWeight: 'bold',
                                            backgroundColor: userDetails.is_following ? 'transparent' : climb.coral,
                                            color: userDetails.is_following ? climb.stone : climb.onCoral,
                                            borderColor: userDetails.is_following ? '#D3D1C7' : climb.coral,
                                            boxShadow: 'none',
                                            '&:hover': {
                                                backgroundColor: userDetails.is_following ? climb.chalk : climb.coralHover,
                                                borderColor: userDetails.is_following ? '#D3D1C7' : climb.coral,
                                                boxShadow: 'none'
                                            }
                                        }}
                                    >
                                        {userDetails.is_following ? 'Unfollow' : 'Follow'}
                                    </Button>
                                )}
                                
                                {currentUserId && String(currentUserId) === String(userId) && (
                                    <Button 
                                        variant="text" 
                                        size="small"
                                        onClick={handleOpenEditDialog}
                                        sx={{ color: '#666', textTransform: 'none' }}
                                    >
                                        Edit Profile
                                    </Button>
                                )}
                            </Box>
                        </Card>
                    ) : (
                        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                            <CircularProgress />
                        </Box>
                    )}
                </Box>
            )}

            <Dialog open={isEditDialogOpen} onClose={() => setIsEditDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Edit Profile</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                        <TextField
                            label="Profile Picture URL"
                            fullWidth
                            variant="outlined"
                            value={editProfilePicture}
                            onChange={(e) => setEditProfilePicture(e.target.value)}
                            placeholder="https://example.com/my-picture.jpg"
                        />
                        <TextField
                            label="Bio"
                            fullWidth
                            multiline
                            rows={3}
                            variant="outlined"
                            value={editBio}
                            onChange={(e) => setEditBio(e.target.value)}
                            placeholder="Tell us about yourself..."
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setIsEditDialogOpen(false)} color="inherit">Cancel</Button>
                    <Button onClick={handleSaveProfile} disabled={isSavingProfile} sx={{ color: climb.coralDark, fontWeight: 'bold' }}>
                        {isSavingProfile ? 'Saving...' : 'Save Changes'}
                    </Button>
                </DialogActions>
            </Dialog>

            <Box sx={{ maxWidth: '1000px', margin: '0 auto', px: 2 }}>
                {!userId ? (
                    <Box sx={{ maxWidth: '640px', margin: '0 auto', mb: 2 }}>
                        <Tabs
                            value={feedType}
                            onChange={handleTabChange}
                            sx={{
                                minHeight: 40,
                                '& .MuiTabs-indicator': { backgroundColor: climb.coralDark, height: 3, borderRadius: '3px' },
                                '& .MuiTab-root': {
                                    textTransform: 'none', fontWeight: 'bold', fontSize: '14px',
                                    minHeight: 40, color: climb.stone,
                                    '&.Mui-selected': { color: climb.rock }
                                }
                            }}
                        >
                            <Tab label="Feed" />
                            <Tab label="Following" />
                        </Tabs>
                    </Box>
                ) : (
                    <Typography variant="h5" sx={{ mb: 3, fontWeight: '600' }}>
                        Posts
                    </Typography>
                )}

                {/* Show login prompt ONLY on the Following tab if not logged in */}
                {!userId && feedType === 1 && !currentUserId ? (
                    <Box sx={{
                        textAlign: 'center', py: 8, mt: 4, maxWidth: '640px', mx: 'auto',
                        backgroundColor: 'white', borderRadius: '14px',
                        border: '1px solid #EDEBE4',
                        boxShadow: '0 2px 8px rgba(44, 44, 42, 0.06)'
                    }}>
                        <Typography variant="h5" sx={{ color: climb.rock, mb: 2, fontWeight: 'bold' }}>
                            Rope up first
                        </Typography>
                        <Typography sx={{ color: climb.stone, mb: 4, px: 2 }}>
                            Log in to follow climbers and see their sends and projects here.
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/login')}
                            sx={{ backgroundColor: climb.rock, textTransform: 'none', px: 4, py: 1, borderRadius: '999px', fontWeight: 'bold', boxShadow: 'none', '&:hover': { backgroundColor: climb.rockHover, boxShadow: 'none' } }}
                        >
                            Go to login
                        </Button>
                    </Box>
                ) : (
                    <>
                        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                        {posts.length === 0 && !isLoading ? (
                            <Typography sx={{ mb: 2, color: '#999', textAlign: 'center', py: 4 }}>
                                No posts available yet.
                            </Typography>
                        ) : null}

                        {userId ? (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                {posts.map((post, index) => (
                                    <SinglePost
                                        key={`${post.id}-${index}`}
                                        title={post.title}
                                        author={post.author_name || userDetails?.name || `User ${post.userId}`}
                                        body={post.body}
                                        imageUrl={post.image_url} 
                                        createdAt={post.created_at}
                                        authorProfilePicture={post.author_profile_picture || userDetails?.profile_picture}
                                    />
                                ))}
                            </Box>
                        ) : (
                            /* Single centered column like a phone feed - climbers scroll one-handed */
                            <Box sx={{ maxWidth: '640px', margin: '0 auto', display: 'flex', flexDirection: 'column' }}>
                                {posts.map((post, index) => (
                                    <SinglePost
                                        key={`${post.id}-${index}`}
                                        title={post.title}
                                        author={post.author_name || `User ${post.userId}`}
                                        body={post.body}
                                        imageUrl={post.image_url}
                                        createdAt={post.created_at}
                                        authorProfilePicture={post.author_profile_picture}
                                    />
                                ))}
                            </Box>
                        )}

                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, height: '40px' }}>
                            {isLoading && <CircularProgress size={30} />}
                            {!hasMore && posts.length > 0 && (
                                <Typography sx={{ color: '#999', fontStyle: 'italic' }}>
                                    No more posts to load
                                </Typography>
                            )}
                        </Box>
                    </>
                )}
            </Box>
        </Box>
    );
}