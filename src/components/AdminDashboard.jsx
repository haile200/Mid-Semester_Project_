import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import { banUser, deletePostAsAdmin, dismissReports, fetchReports, unbanUser } from '../api';
import { reasonLabel } from '../moderation';
import { getTimeAgo } from '../timeAgo';
import { htmlToParagraphs } from '../writingHelp';
import './AdminDashboard.css';

const EXCERPT_LENGTH = 280;

function excerpt(html) {
    const text = htmlToParagraphs(html).replace(/\n+/g, ' ');
    return text.length > EXCERPT_LENGTH ? `${text.slice(0, EXCERPT_LENGTH)}...` : text;
}

function ReportGroup({ post, reports, isBusy, onAction }) {
    const { author } = post;
    const count = `${reports.length} report${reports.length === 1 ? '' : 's'}`;

    return (
        <Box className="admin-card" data-cy="admin-report-group">
            <Box className="admin-card-header">
                <Typography className="admin-post-title">{post.title}</Typography>
                <Chip label={count} className="admin-count-chip" />
            </Box>

            <Box className="admin-author-row">
                <Typography className="admin-author">by {author.name}</Typography>
                {author.is_bot && <Chip label="bot" size="small" className="admin-tag" />}
                {author.is_admin && <Chip label="admin" size="small" className="admin-tag" />}
                {author.is_banned && <Chip label="banned" size="small" className="admin-tag admin-tag--banned" />}
                <Typography className="admin-time">{getTimeAgo(post.created_at)}</Typography>
            </Box>

            <Typography className="admin-excerpt">{excerpt(post.body)}</Typography>

            <Box className="admin-reports">
                {reports.map((report) => (
                    <Box key={report.id} className="admin-report">
                        <Chip label={reasonLabel(report.reason)} size="small" className={`admin-reason admin-reason--${report.reason}`} />
                        <Typography className="admin-report-meta">
                            by {report.reporter_name}, {getTimeAgo(report.created_at)}
                        </Typography>
                        {report.note && <Typography className="admin-report-note">"{report.note}"</Typography>}
                    </Box>
                ))}
            </Box>

            <Box className="admin-actions">
                <Button
                    size="small"
                    disabled={isBusy}
                    className="admin-action admin-action--dismiss"
                    onClick={() => onAction(post.id, () => dismissReports(post.id), null, `Dismissed the reports on "${post.title}".`)}
                    data-cy="admin-dismiss"
                >
                    Dismiss reports
                </Button>
                <Button
                    size="small"
                    disabled={isBusy}
                    className="admin-action admin-action--danger"
                    onClick={() => onAction(
                        post.id,
                        () => deletePostAsAdmin(post.id),
                        `Delete "${post.title}" by ${author.name}? Its comments are deleted too. This cannot be undone.`,
                        `Deleted "${post.title}".`,
                    )}
                    data-cy="admin-delete"
                >
                    Delete post
                </Button>
                {!author.is_admin && (author.is_banned ? (
                    <Button
                        size="small"
                        disabled={isBusy}
                        className="admin-action"
                        onClick={() => onAction(post.id, () => unbanUser(author.id), null, `${author.name} is no longer banned.`)}
                        data-cy="admin-unban"
                    >
                        Unban {author.name}
                    </Button>
                ) : (
                    <Button
                        size="small"
                        disabled={isBusy}
                        className="admin-action admin-action--danger"
                        onClick={() => onAction(
                            post.id,
                            () => banUser(author.id),
                            `Ban ${author.name}? They are logged out now and cannot log in until unbanned. Their posts stay up.`,
                            `${author.name} is banned.`,
                        )}
                        data-cy="admin-ban"
                    >
                        Ban {author.name}
                    </Button>
                ))}
            </Box>
        </Box>
    );
}

export default function AdminDashboard() {
    const [groups, setGroups] = useState([]);
    const [status, setStatus] = useState('loading');
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const [busyPostId, setBusyPostId] = useState(null);
    // Bumping this re-runs the effect below, which reloads the list after an action.
    const [version, setVersion] = useState(0);

    useEffect(() => {
        let cancelled = false;

        fetchReports()
            .then((data) => {
                if (cancelled) return;
                setGroups(data);
                setStatus('ready');
            })
            .catch((loadError) => {
                if (cancelled) return;
                setError(loadError.message);
                setStatus('error');
            });

        return () => { cancelled = true; };
    }, [version]);

    const handleAction = async (postId, action, confirmText, doneText) => {
        if (confirmText && !window.confirm(confirmText)) return;
        setBusyPostId(postId);
        setNotice('');
        try {
            await action();
            setNotice(doneText);
            setVersion((current) => current + 1);
        } catch (actionError) {
            setNotice(actionError.message);
        } finally {
            setBusyPostId(null);
        }
    };

    const needsLogin = error.toLowerCase().includes('log in');

    return (
        <Box className="admin-page">
            <Box className="admin-content">
                <Typography variant="h5" className="admin-title">Moderation</Typography>
                <Typography className="admin-subtitle">Reported posts, most reported first.</Typography>

                {notice && <Typography className="admin-notice" data-cy="admin-notice">{notice}</Typography>}

                {status === 'loading' && (
                    <Box className="admin-status"><CircularProgress size={28} className="admin-spinner" /></Box>
                )}

                {status === 'error' && (
                    <Box className="admin-denied" data-cy="admin-denied">
                        <Typography className="admin-denied-text">
                            {needsLogin ? 'Log in with an admin account to see this page.' : error}
                        </Typography>
                        {needsLogin && <Link to="/login" className="admin-denied-link">Go to login</Link>}
                    </Box>
                )}

                {status === 'ready' && groups.length === 0 && (
                    <Typography className="admin-empty" data-cy="admin-empty">No open reports. All clear.</Typography>
                )}

                {groups.map(({ post, reports }) => (
                    <ReportGroup
                        key={post.id}
                        post={post}
                        reports={reports}
                        isBusy={busyPostId === post.id}
                        onAction={handleAction}
                    />
                ))}
            </Box>
        </Box>
    );
}
