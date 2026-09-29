import { useState, useEffect, useEffectEvent } from 'react';
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

const PAGE_SIZE = 10;

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

    // The loaded posts, labelled with the list they belong to (see listKey below).
    const [list, setList] = useState({ key: null, posts: [], offset: 0, hasMore: true, error: '' });
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [loadedUser, setLoadedUser] = useState(location.state?.userDetails || null);
    // Details loaded for another profile are never shown under this one, so nothing needs resetting.
    const userDetails = loadedUser && String(loadedUser.id) === String(userId) ? loadedUser : null;

    const [feedType, setFeedType] = useState(0);
    const [openFollowList, setOpenFollowList] = useState(null);

    // Edit Profile State
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [editBio, setEditBio] = useState('');
    const [editProfilePicture, setEditProfilePicture] = useState('');
    const [isSavingProfile, setIsSavingProfile] = useState(false);

    // Which list belongs on screen: a profile, the global feed or the following feed.
    const listKey = `${userId ?? ''}|${feedType}|${currentUserId ?? ''}`;
    // The Following feed needs an account, so a logged-out visitor sees a login prompt instead.
    const needsLogin = !userId && feedType === 1 && !currentUserId;
    // Posts loaded for another list are hidden, never shown under the wrong tab or profile.
    const isCurrentList = list.key === listKey;
    const posts = isCurrentList ? list.posts : [];
    const hasMore = isCurrentList && list.hasMore;
    const error = isCurrentList ? list.error : '';
    const isLoading = !needsLogin && (!isCurrentList || isLoadingMore);

    const fetchPage = (pageOffset) => {
        if (userId) return fetchPosts(pageOffset, PAGE_SIZE, userId);
        return feedType === 0 ? fetchFeed(pageOffset, PAGE_SIZE) : fetchFollowingFeed(pageOffset, PAGE_SIZE);
    };

    const loadMorePosts = async () => {
        const key = list.key;
        setIsLoadingMore(true);
        try {
            const data = await fetchPage(list.offset);
            // Added only if the same list is still on screen when the answer arrives.
            setList((current) => current.key !== key ? current : {
                ...current,
                posts: [...current.posts, ...data],
                offset: current.offset + PAGE_SIZE,
                hasMore: data.length === PAGE_SIZE,
                error: '',
            });
        } catch (fetchError) {
            setList((current) => current.key !== key ? current : {
                ...current,
                error: fetchError.message || 'Unable to load posts.',
            });
        } finally {
            setIsLoadingMore(false);
        }
    };

    const handleFollowToggle = async () => {
        if (!userDetails) return;
        try {
            await toggleFollow(userId, userDetails.is_following);
            setLoadedUser(prev => ({
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

            setLoadedUser(prev => ({
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

    // Effect Events always see the latest state, so the effects below need not re-run when it changes.
    const handleReachedBottom = useEffectEvent(() => {
        if (!needsLogin && isCurrentList && list.hasMore && !isLoadingMore) {
            loadMorePosts();
        }
    });

    const fetchFirstPage = useEffectEvent(() => fetchPage(0));

    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop + 1 >= document.documentElement.scrollHeight) {
                handleReachedBottom();
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    useEffect(() => {
        // Only fetch user details if viewing a specific profile
        if (userId) {
            fetchUserDetails(userId)
                .then(user => setLoadedUser(user))
                .catch(err => console.error(err));
        }
    }, [userId]);

    // The first page of the list on screen. State changes only when the answer arrives, and an answer
    // for a list that is no longer on screen (after a quick tab or profile switch) is ignored.
    useEffect(() => {
        if (needsLogin) return;
        let ignore = false;
        fetchFirstPage()
            .then((data) => {
                if (!ignore) {
                    setList({ key: listKey, posts: data, offset: PAGE_SIZE, hasMore: data.length === PAGE_SIZE, error: '' });
                }
            })
            .catch((fetchError) => {
                if (!ignore) {
                    setList({ key: listKey, posts: [], offset: 0, hasMore: false, error: fetchError.message || 'Unable to load posts.' });
                }
            });
        return () => {
            ignore = true;
        };
    }, [listKey, needsLogin]);

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
