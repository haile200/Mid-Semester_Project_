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

