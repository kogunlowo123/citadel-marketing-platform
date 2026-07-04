import { useWorkflows } from '../api/hooks';
import { api } from '../api/client';
import { useQueryClient } from '@tanstack/react-query';
import { Play, Pause } from 'lucide-react';

interface Workflow { id: string; name: string; description: string | null; trigger_type: string; is_active: boolean; run_count: number; last_run_at: string | null }

export default function Workflows() {
  const { data } = useWorkflows() as { data: Workflow[] | undefined };
  const qc = useQueryClient();
  const workflows = data || [];

  const toggle = async (id: string, active: boolean) => {
    await api.post(`/workflows/${id}/${active ? 'deactivate' : 'activate'}`);
    qc.invalidateQueries({ queryKey: ['workflows'] });
  };

  const run = async (id: string) => {
    await api.post(`/workflows/${id}/run`);
    qc.invalidateQueries({ queryKey: ['workflows'] });
  };

  return (
    <div className="fade-in">
      <h1 style={{ fontSize: '1.75rem', marginBottom: 24 }}>Workflows</h1>

      <div style={{ display: 'grid', gap: 16 }}>
        {workflows.map(w => (
          <div key={w.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', display: 'inline-block', marginRight: 8, background: w.is_active ? 'var(--success)' : '#444' }} />
                {w.name}
              </h3>
              {w.description && <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 8 }}>{w.description}</p>}
              <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                <span>Trigger: <strong>{w.trigger_type}</strong></span>
                <span>Runs: <strong>{w.run_count}</strong></span>
                {w.last_run_at && <span>Last: {new Date(w.last_run_at).toLocaleDateString()}</span>}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn-secondary btn-sm" onClick={() => toggle(w.id, w.is_active)}>
                {w.is_active ? <><Pause size={12} /> Pause</> : <><Play size={12} /> Activate</>}
              </button>
              <button className="btn-primary btn-sm" onClick={() => run(w.id)}>Run Now</button>
            </div>
          </div>
        ))}
        {workflows.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No workflows configured yet</p>}
      </div>
    </div>
  );
}
