// Must match REPORT_REASONS in backend/utils.py.
export const REPORT_REASONS = [
    { value: 'spam', label: 'Spam' },
    { value: 'harassment', label: 'Harassment' },
    { value: 'hate', label: 'Hate speech' },
    { value: 'other', label: 'Other' },
];

export const MAX_REPORT_NOTE_LENGTH = 300;

export function reasonLabel(value) {
    return REPORT_REASONS.find((reason) => reason.value === value)?.label || value;
}
