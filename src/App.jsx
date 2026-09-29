import { useState } from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import { Routes, Route, Navigate } from 'react-router-dom';
import TopBar from './components/TopBar';
import Feed from './components/Feed';
import Users from './components/Users';
import Login from './components/Login';
import Signup from './components/Signup';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import Profile from './components/Profile';
import NewPost from './components/NewPost';
// Import the About component
import About from './components/About';
import AdminDashboard from './components/AdminDashboard';
import { logout } from './api';

function App() {
    // Read once before the first render, so the page never starts out as logged out.
    const [currentUser, setCurrentUser] = useState(() => JSON.parse(localStorage.getItem('currentUser') || 'null'));

    const handleLogin = (user) => {
        localStorage.setItem('currentUser', JSON.stringify(user));
        setCurrentUser(user);
    };

    const forgetUser = () => {
        localStorage.removeItem('currentUser');
        setCurrentUser(null);
    };

    const handleLogout = async () => {
        try {
            await logout();
        } catch (error) {
            console.error('Logout failed:', error);
        } finally {
            forgetUser();
        }
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
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword onPasswordReset={forgetUser} />} />
                <Route path="/profile" element={<Profile />} />
                
                {/* Removed RequireAuth wrapper to allow direct access for testing */}
                <Route path="/new-post" element={<NewPost currentUser={currentUser} />} />
                <Route path="/admin" element={<AdminDashboard />} />
                
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </>
    );
}

export default App;