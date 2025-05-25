export function formatDate(ts: number | string | null | undefined): string {
    if (!ts) return '';
    const date = new Date(Number(ts));
    // Pad with zeros
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
