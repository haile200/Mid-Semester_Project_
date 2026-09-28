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
import FollowListDialog from './FollowListDialog';
import ImageUpload from './ImageUpload';
import SuggestedUsers from './SuggestedUsers';
import { fetchPosts, fetchUserDetails, toggleFollow, fetchFollowingFeed, fetchFeed, updateProfile } from '../api';
import './Feed.css';

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
    const [openFollowList, setOpenFollowList] = useState(null);

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
        <Box className="feed-page">
            {userId && (
                <Box className="feed-profile-section">
                    {userDetails ? (
                        <Card className="feed-profile-card">
                            <MuiAvatar
                                src={userDetails.profile_picture || ''}
                                alt={userDetails.name}
                                className="feed-profile-avatar"
                            >
                                {userDetails.name ? userDetails.name[0].toUpperCase() : 'U'}
                            </MuiAvatar>
                            <Box className="feed-profile-info">
                                <Typography variant="h5" className="feed-profile-name">
                                    {userDetails.name}
                                </Typography>
                                {userDetails.bio && (
                                    <Typography className="feed-profile-bio">
                                        {userDetails.bio}
                                    </Typography>
                                )}
                                <Typography className="feed-profile-stats">
                                    {userDetails.postCount} {userDetails.postCount === 1 ? 'Post' : 'Posts'}
                                    {' • '}
                                    <button type="button" className="feed-profile-stat-link" onClick={() => setOpenFollowList('followers')} data-cy="followers-link">
                                        {userDetails.followersCount || 0} Followers
                                    </button>
                                    {' • '}
                                    <button type="button" className="feed-profile-stat-link" onClick={() => setOpenFollowList('following')} data-cy="following-link">
                                        {userDetails.followingCount || 0} Following
                                    </button>
                                </Typography>
                            </Box>

                            <Box className="feed-profile-actions">
                                {currentUserId && String(currentUserId) !== String(userId) && (
                                    <Button
                                        variant={userDetails.is_following ? "outlined" : "contained"}
                                        onClick={handleFollowToggle}
                                        className={`feed-follow-button${userDetails.is_following ? ' feed-follow-button--following' : ''}`}
                                    >
                                        {userDetails.is_following ? 'Unfollow' : 'Follow'}
                                    </Button>
                                )}

                                {currentUserId && String(currentUserId) === String(userId) && (
                                    <Button
                                        variant="text"
                                        size="small"
                                        onClick={handleOpenEditDialog}
                                        className="feed-edit-profile-button"
                                    >
                                        Edit Profile
                                    </Button>
                                )}
                            </Box>
                        </Card>
                    ) : (
                        <Box className="feed-profile-loading">
                            <CircularProgress />
                        </Box>
                    )}
                </Box>
            )}

            <Dialog open={isEditDialogOpen} onClose={() => setIsEditDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Edit Profile</DialogTitle>
                <DialogContent>
                    <Box className="feed-edit-dialog-fields">
                        <ImageUpload onUploaded={setEditProfilePicture} label="Upload a picture" />
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
                    <Button onClick={handleSaveProfile} disabled={isSavingProfile} className="feed-edit-dialog-save">
                        {isSavingProfile ? 'Saving...' : 'Save Changes'}
                    </Button>
                </DialogActions>
            </Dialog>

            {openFollowList && (
                <FollowListDialog userId={userId} kind={openFollowList} onClose={() => setOpenFollowList(null)} />
            )}

            <Box className="feed-content">
              {/* The sidebar only makes sense on the home feed for someone logged in. */}
              <Box className={!userId && currentUserId ? 'feed-home' : undefined}>
                {!userId && currentUserId && (
                    <Box className="feed-home-aside"><SuggestedUsers /></Box>
                )}
                <Box className="feed-home-main">
                {!userId ? (
                    <Box className="feed-tabs-container">
                        <Tabs
                            value={feedType}
                            onChange={handleTabChange}
                            className="feed-tabs"
                        >
                            <Tab label="Feed" />
                            <Tab label="Following" />
                        </Tabs>
                    </Box>
                ) : (
                    <Typography variant="h5" className="feed-posts-heading">
                        Posts
                    </Typography>
                )}

                {/* Show login prompt ONLY on the Following tab if not logged in */}
                {!userId && feedType === 1 && !currentUserId ? (
                    <Box className="feed-login-prompt">
                        <Typography variant="h5" className="feed-login-prompt-title">
                            Rope up first
                        </Typography>
                        <Typography className="feed-login-prompt-text">
                            Log in to follow climbers and see their sends and projects here.
                        </Typography>
                        <Button
                            variant="contained"
                            onClick={() => navigate('/login')}
                            className="feed-login-prompt-button"
                        >
                            Go to login
                        </Button>
                    </Box>
                ) : (
                    <>
                        {error && <Alert severity="error" className="feed-error">{error}</Alert>}

                        {posts.length === 0 && !isLoading ? (
                            <Typography className="feed-empty-message">
                                No posts available yet.
                            </Typography>
                        ) : null}

                        {userId ? (
                            <Box className="feed-profile-posts">
                                {posts.map((post, index) => (
                                    <SinglePost
                                        key={`${post.id}-${index}`}
                                        postId={post.id}
                                        authorId={post.userId}
                                        currentUserId={currentUserId}
                                        canComment={Boolean(currentUserId)}
                                        title={post.title}
                                        author={post.author_name || userDetails?.name || `User ${post.userId}`}
                                        body={post.body}
                                        imageUrl={post.image_url}
                                        createdAt={post.created_at}
                                        likeCount={post.likeCount}
                                        likedByMe={post.likedByMe}
                                        authorProfilePicture={post.author_profile_picture || userDetails?.profile_picture}
                                    />
                                ))}
                            </Box>
                        ) : (
                            /* Single centered column like a phone feed - climbers scroll one-handed */
                            <Box className="feed-posts-column">
                                {posts.map((post, index) => (
                                    <SinglePost
                                        key={`${post.id}-${index}`}
                                        postId={post.id}
                                        authorId={post.userId}
                                        currentUserId={currentUserId}
                                        canComment={Boolean(currentUserId)}
                                        title={post.title}
                                        author={post.author_name || `User ${post.userId}`}
                                        body={post.body}
                                        imageUrl={post.image_url}
                                        createdAt={post.created_at}
                                        likeCount={post.likeCount}
                                        likedByMe={post.likedByMe}
                                        authorProfilePicture={post.author_profile_picture}
                                    />
                                ))}
                            </Box>
                        )}

                        <Box className="feed-footer">
                            {isLoading && <CircularProgress size={30} />}
                            {!hasMore && posts.length > 0 && (
                                <Typography className="feed-end-message">
                                    No more posts to load
                                </Typography>
                            )}
                        </Box>
                    </>
                )}
                </Box>
              </Box>
            </Box>
        </Box>
    );
}
