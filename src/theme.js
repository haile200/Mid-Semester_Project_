// "My Beta" climbing palette: rock grays for structure, chalk whites for
// surfaces, hold-orange coral as the single energetic accent.
export const climb = {
    rock: '#2C2C2A',
    rockHover: '#444441',
    stone: '#5F5E5A',
    chalk: '#F1EFE8',
    page: '#FAF9F5',
    coral: '#F0997B',
    coralDark: '#D85A30',
    coralHover: '#E8875F',
    onCoral: '#4A1B0C',
    coralTint: '#FAECE7',
    onCoralTint: '#712B13',
    leadTint: '#EEEDFE',
    onLeadTint: '#3C3489',
    sentTint: '#E1F5EE',
    onSentTint: '#085041',
    projectTint: '#FAEEDA',
    onProjectTint: '#633806',
    // Bold coral-to-rock diagonal for the feed hero banner
    heroGradient: 'linear-gradient(135deg, #D85A30 0%, #B5451F 55%, #2C2C2A 100%)',
};

// Placeholder climbing metadata until posts carry real grade/discipline columns.
// Derived deterministically from post text so each card keeps a stable badge.
// V-grades for boulder problems, French grades for rope routes
const DISCIPLINES = [
    { label: 'Bouldering', bg: climb.coralTint, fg: climb.onCoralTint, grades: ['V2', 'V3', 'V4', 'V5', 'V6'] },
    { label: 'Lead', bg: climb.leadTint, fg: climb.onLeadTint, grades: ['6a+', '6b+', '6c+', '7a'] },
    { label: 'Top rope', bg: climb.sentTint, fg: climb.onSentTint, grades: ['5c', '6a', '6b', '6c'] },
];

function hashText(seedText) {
    let hash = 0;
    for (const ch of String(seedText || '')) {
        hash = (hash * 31 + ch.charCodeAt(0)) % 100000;
    }
    return hash;
}

export function climbingBadges(seedText) {
    const hash = hashText(seedText);
    const discipline = DISCIPLINES[hash % DISCIPLINES.length];
    return {
        discipline,
        grade: discipline.grades[hash % discipline.grades.length],
        sent: hash % 3 !== 0,
        // Placeholder engagement counts, stable per post (no likes table yet)
        likes: 6 + (hash % 40),
        comments: hash % 9,
    };
}

// Placeholder profile stats for the hero banner until send data exists on the backend.
export function climbingStats(seedText) {
    const hash = hashText(seedText);
    const topGrades = ['V3', 'V4', 'V5', 'V6', '6c+', '7a'];
    return {
        sends: 5 + (hash % 25),
        topGrade: topGrades[hash % topGrades.length],
        crew: 8 + (hash % 40),
    };
}
