// The editor stores HTML; corrections work on plain text with one line per paragraph.

export function htmlToParagraphs(html) {
    const doc = new DOMParser().parseFromString(html || '', 'text/html');
    const paragraphs = [...doc.body.querySelectorAll('p')];
    const lines = paragraphs.length ? paragraphs.map((p) => p.textContent) : [doc.body.textContent];
    return lines.join('\n');
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export function paragraphsToHtml(text) {
    return text
        .split('\n')
        .map((line) => `<p>${line ? escapeHtml(line) : '<br>'}</p>`)
        .join('');
}

// The editor (Quill 2) saves every space as a non-breaking space, which turns a whole paragraph
// into one unbreakable word that cannot wrap. Used before saving, and when showing posts that were
// saved that way already.
export function withNormalSpaces(html) {
    return (html || '').replace(/&nbsp;|\u00A0/g, ' ');
}

export function hasFormatting(html) {
    return /<(strong|em|u|a)\b/i.test(html || '');
}
