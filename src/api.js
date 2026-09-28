const BASE_URL = '/api';

const handleResponse = async (response) => {
    const text = await response.text();
    let data = null;

    try {
        data = JSON.parse(text);
    } catch {
        data = null;
    }

    if (!response.ok) {
        const message = data?.message || response.statusText || 'Request failed';
        throw new Error(message);
    }

    return data;
};

export const fetchFeed = async (offset = 0, limit = 10) => { 
    try {
        // Adding URLSearchParams to properly attach pagination parameters
        const params = new URLSearchParams({ start: offset, limit });
        const response = await fetch(`${BASE_URL}/feed?${params.toString()}`, {
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (fetchFeed):', error);
        throw error;
    }
};

export const fetchFollowingFeed = async (offset = 0, limit = 10) => {
    try {
        const params = new URLSearchParams({ start: offset, limit });
        const response = await fetch(`${BASE_URL}/feed/following?${params.toString()}`, {
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (fetchFollowingFeed):', error);
        throw error;
    }
};

export const fetchPosts = async (offset = 0, limit = 10, userId = null) => {
    try {
        const params = new URLSearchParams({ start: offset, limit });
        if (userId) params.set('userId', userId);
        const response = await fetch(`${BASE_URL}/posts?${params.toString()}`, {
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (fetchPosts):', error);
        throw error;
    }
};

export const fetchUsers = async (offset = 0, limit = 10, search = '') => {
    try {
        const params = new URLSearchParams({ start: offset, limit });
        if (search) params.set('search', search);
        const response = await fetch(`${BASE_URL}/users?${params.toString()}`, {
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (fetchUsers):', error);
        return [];
    }
};

export const fetchUserDetails = async (userId) => {
    try {
        const response = await fetch(`${BASE_URL}/users/${userId}`, {
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (fetchUserDetails):', error);
        throw error;
    }
};

export const toggleFollow = async (userId, isFollowing) => {
    try {
        const method = isFollowing ? 'DELETE' : 'POST';
        const response = await fetch(`${BASE_URL}/follow/${userId}`, {
            method: method,
            credentials: 'include'
        });
        return await handleResponse(response);
    } catch (error) {
        console.error('API Error (toggleFollow):', error);
        throw error;
    }
};

export const signup = async (name, email, password) => {
    const response = await fetch(`${BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name, email, password })
    });
    return handleResponse(response);
};

export const login = async (email, password) => {
    const response = await fetch(`${BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password })
    });
    return handleResponse(response);
};

export const fetchCurrentUser = async () => {
    const response = await fetch(`${BASE_URL}/auth/me`, {
        credentials: 'include'
    });
    return handleResponse(response);
};

export const logout = async () => {
    const response = await fetch(`${BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include'
    });
    return handleResponse(response);
};

// In api.js - ensure imageUrl is passed
export const createPost = async (title, body, author_id, imageUrl = '') => {
    const response = await fetch(`${BASE_URL}/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        // Make sure imageUrl is sent to the Flask server
        body: JSON.stringify({ title, body, author_id, imageUrl })
    });
    return handleResponse(response);
};

export const fetchComments = async (postId, offset = 0, limit = 50) => {
    const params = new URLSearchParams({ start: offset, limit });
    const response = await fetch(`${BASE_URL}/posts/${postId}/comments?${params.toString()}`, {
        credentials: 'include'
    });
    return handleResponse(response);
};

export const createComment = async (postId, body, parentId = null) => {
    const payload = { body };
    if (parentId !== null) payload.parent_id = parentId;
    const response = await fetch(`${BASE_URL}/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
    });
    return handleResponse(response);
};

export const suggestCorrection = async (text) => {
    const response = await fetch(`${BASE_URL}/corrections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ text })
    });
    return handleResponse(response);
};

export const fetchCommentIdeas = async (postId) => {
    const response = await fetch(`${BASE_URL}/posts/${postId}/comment-ideas`, {
        credentials: 'include'
    });
    return handleResponse(response);
};

const sendJson = async (method, path, payload) => {
    const response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: payload === undefined ? undefined : JSON.stringify(payload)
    });
    return handleResponse(response);
};

// notes: { style, grade, title, body } with body as plain text, one paragraph per line
export const suggestPost = (notes) => sendJson('POST', '/post-suggestions', notes);

export const likePost = (postId) => sendJson('PUT', `/posts/${postId}/like`);

export const unlikePost = (postId) => sendJson('DELETE', `/posts/${postId}/like`);

const getJson = async (path) => {
    const response = await fetch(`${BASE_URL}${path}`, { credentials: 'include' });
    return handleResponse(response);
};

export const fetchFollowers = (userId) => getJson(`/users/${userId}/followers?limit=50`);

export const fetchFollowing = (userId) => getJson(`/users/${userId}/following?limit=50`);

export const fetchSuggestions = (limit = 5) => getJson(`/users/suggestions?limit=${limit}`);

export const reportPost = (postId, reason, note) =>
    sendJson('POST', `/posts/${postId}/reports`, { reason, note });

export const fetchReports = async () => {
    const response = await fetch(`${BASE_URL}/admin/reports`, { credentials: 'include' });
    return handleResponse(response);
};

export const dismissReports = (postId) =>
    sendJson('PATCH', `/admin/posts/${postId}/reports`, { status: 'dismissed' });

export const deletePostAsAdmin = (postId) => sendJson('DELETE', `/admin/posts/${postId}`);

export const banUser = (userId) => sendJson('PUT', `/admin/users/${userId}/ban`);

export const unbanUser = (userId) => sendJson('DELETE', `/admin/users/${userId}/ban`);

export const updateProfile = async (bio, profilePicture) => {
    // We assume BASE_URL is defined at the top of your api.js file
    const response = await fetch(`${BASE_URL}/users/profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ bio, profilePicture })
    });
    return handleResponse(response);
};

