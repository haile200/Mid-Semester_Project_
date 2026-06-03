import React, { useState, useEffect } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Search from './Search';
import User from './User';
import { fetchUsers } from '../api';

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
        <Box sx={{ minHeight: '100vh', backgroundColor: '#fdfdfd', py: 4 }}>
            <Box sx={{ maxWidth: '900px', margin: '0 auto', px: 2 }}>
                <Typography variant="h4" sx={{ mb: 2 }}>
                    Users
                </Typography>
                <Search onSearch={setSearchTerm} />

                {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

                <Box sx={{ 
                    display: 'flex', justifyContent: 'space-between', padding: '16px 24px',
                    backgroundColor: '#f4f5f7', borderRadius: '8px', marginBottom: '16px'
                }}>
                    <Box sx={{ width: '10%' }} />
                    <Typography sx={{ width: '25%', fontWeight: 'bold', fontSize: '14px' }}>User</Typography>
                    <Typography sx={{ width: '20%', textAlign: 'center', fontWeight: 'bold', fontSize: '14px' }}>Posts</Typography>
                    <Box sx={{ width: '45%' }} />
                </Box>

                {users.length === 0 && !isLoading && !error && (
                    <Typography sx={{ textAlign: 'center', py: 4, color: '#999' }}>
                        No users found. Try adjusting your search.
                    </Typography>
                )}

                <Box>
                    {users.map((u) => (
                        <User 
                            key={u.id} 
                            id={u.id} 
                            name={u.name} 
                            email={u.email} 
                            postCount={u.postCount} 
                            profile_picture={u.profile_picture} 
                        />
                    ))}
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, height: '40px' }}>
                    {isLoading && <CircularProgress sx={{ color: '#7b61ff' }} size={30} />}
                    {!hasMore && users.length > 0 && (
                        <Typography sx={{ color: '#999', fontStyle: 'italic' }}>
                            No more users to load
                        </Typography>
                    )}
                </Box>
            </Box>
        </Box>
    );
}