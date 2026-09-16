import React, { useState, useEffect } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Search from './Search';
import User from './User';
import { fetchUsers } from '../api';
import './Users.css';

export default function Users() {
    const [users, setUsers] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [offset, setOffset] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [hasMore, setHasMore] = useState(true);
    const limit = 10;

    const loadUsers = async (currentOffset, currentSearch, isReset = false) => {
        if (isLoading) return;
        setIsLoading(true);
        setError('');

        try {
            const data = await fetchUsers(currentOffset, limit, currentSearch);

            // Smartly update array and filter duplicates
            setUsers((prev) => {
                let combined = [];
                if (isReset) {
                    combined = data || [];
                } else {
                    combined = [...prev, ...(data || [])];
                }

                // Convert array to Map (which prevents duplicate keys by ID) and revert to array
                const uniqueUsers = Array.from(new Map(combined.map(user => [user.id, user])).values());
                return uniqueUsers;
            });

            if (isReset) {
                setOffset(limit);
            } else {
                setOffset(currentOffset + limit);
            }

            setHasMore((data && data.length === limit) ? true : false);
        } catch (err) {
            setError(err.message || 'Failed to load users. Please try again.');
            if (isReset) {
                setUsers([]);
                setOffset(0);
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Infinite Scroll implementation
    useEffect(() => {
        const handleScroll = () => {
            if (window.innerHeight + document.documentElement.scrollTop + 1 >= document.documentElement.scrollHeight) {
                if (hasMore && !isLoading) {
                    loadUsers(offset, searchTerm, false);
                }
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [isLoading, hasMore, offset, searchTerm]);

    // Handle search debouncing
    useEffect(() => {
        const delayDebounce = setTimeout(() => {
            loadUsers(0, searchTerm, true);
        }, 300);
        return () => clearTimeout(delayDebounce);
    }, [searchTerm]);

    return (
        <Box className="users-page">
            <Box className="users-content">
                <Typography variant="h5" className="users-title">
                    Community
                </Typography>
                <Typography className="users-subtitle">
                    Find climbers to follow and swap beta with
                </Typography>
                <Search onSearch={setSearchTerm} />

                {error && <Alert severity="error" className="users-error">{error}</Alert>}

                {users.length === 0 && !isLoading && !error && (
                    <Typography className="users-empty-message">
                        No climbers found. Try another name.
                    </Typography>
                )}

                <Box>
                    {users.map((u) => (
                        <User
                            key={u.id}
                            id={u.id}
                            name={u.name}
                            postCount={u.postCount}
                            profile_picture={u.profile_picture}
                        />
                    ))}
                </Box>

                <Box className="users-footer">
                    {isLoading && <CircularProgress className="users-loading-spinner" size={30} />}
                    {!hasMore && users.length > 0 && (
                        <Typography className="users-end-message">
                            No more climbers to load
                        </Typography>
                    )}
                </Box>
            </Box>
        </Box>
    );
}
