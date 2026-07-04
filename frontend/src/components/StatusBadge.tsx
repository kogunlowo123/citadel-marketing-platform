const statusClasses: Record<string, string> = {
  active: 'badge-active', draft: 'badge-draft', scheduled: 'badge-scheduled',
  sending: 'badge-sending', sent: 'badge-sent', bounced: 'badge-bounced',
  unsubscribed: 'badge-unsubscribed', paused: 'badge-paused', cancelled: 'badge-draft',
  completed: 'badge-completed', failed: 'badge-failed', pending: 'badge-pending',
  processing: 'badge-processing', complained: 'badge-bounced', cleaned: 'badge-draft',
};

export default function StatusBadge({ status }: { status: string }) {
  return <span className={`badge ${statusClasses[status] || 'badge-draft'}`}>{status}</span>;
}
