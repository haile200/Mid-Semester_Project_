import React, { useEffect, useState } from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import TopBar from './components/TopBar';
import Feed from './components/Feed';
import Users from './components/Users';
import Login from './components/Login';
import Signup from './components/Signup';
import NewPost from './components/NewPost';
// Import the About component
import About from './components/About';

function RequireAuth({ user, children }) {
    const navigate = useNavigate();

    useEffect(() => {
        if (!user) {
            navigate('/login', { replace: true });
        }
    }, [user, navigate]);

    return user ? children : null;
}

function App() {
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
        const storedUser = localStorage.getItem('currentUser');
        if (storedUser) {
            setCurrentUser(JSON.parse(storedUser));
        }
    }, []);

    const handleLogin = (user) => {
        localStorage.setItem('currentUser', JSON.stringify(user));
        setCurrentUser(user);
    };

    const handleLogout = () => {
        localStorage.removeItem('currentUser');
        setCurrentUser(null);
    };

    return (
        <>
            <CssBaseline />
            <TopBar currentUser={currentUser} onLogout={handleLogout} />
            <Routes>
                <Route path="/" element={<Feed />} />
                <Route path="/users" element={<Users />} />
                <Route path="/about" element={<About />} />
                <Route path="/user-posts/:userId" element={<Feed />} />
                <Route path="/login" element={<Login onLogin={handleLogin} />} />
                <Route path="/signup" element={<Signup />} />
                
                {/* Removed RequireAuth wrapper to allow direct access for testing */}
                <Route path="/new-post" element={<NewPost currentUser={currentUser} />} />
                
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </>
    );
}

export default App;