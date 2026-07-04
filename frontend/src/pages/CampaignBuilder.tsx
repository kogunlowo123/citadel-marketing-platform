import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { useCreateCampaign, useGenerateCampaign, useSegments } from '../api/hooks';

interface Segment { id: string; name: string; contact_count: number }
interface SegmentList { items: Segment[] }

export default function CampaignBuilder() {
  const navigate = useNavigate();
  const createMutation = useCreateCampaign();
  const generateMutation = useGenerateCampaign();
  const { data: segData } = useSegments() as { data: SegmentList | undefined };
  const segments = segData?.items || [];

  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [subject, setSubject] = useState('');
  const [previewText, setPreviewText] = useState('');
  const [htmlContent, setHtmlContent] = useState('');
  const [segmentId, setSegmentId] = useState('');
  const [aiTopic, setAiTopic] = useState('');

  const handleGenerate = async () => {
    if (!aiTopic) return;
    const result = await generateMutation.mutateAsync({ topic: aiTopic, tone: 'professional', audience: 'cloud professionals', length: 'medium' }) as { data: { subject: string; preview_text: string; html_content: string } };
    if (result?.data) {
      setSubject(result.data.subject);
      setPreviewText(result.data.preview_text);
      setHtmlContent(result.data.html_content);
    }
  };

  const handleCreate = async () => {
    await createMutation.mutateAsync({
      name, subject, preview_text: previewText, html_content: htmlContent,
      segment_id: segmentId || undefined,
    });
    navigate('/campaigns');
  };

  return (
    <div className="fade-in" style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: '1.75rem', marginBottom: 24 }}>New Campaign</h1>

      <div style={{ display: 'flex', gap: 8, marginBottom: 32 }}>
        {[1, 2, 3].map(s => (
          <div key={s} style={{
            width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: step >= s ? 'var(--accent)' : 'var(--surface)', color: step >= s ? '#0a0a0a' : 'var(--text-muted)',
            fontWeight: 700, fontSize: '0.8rem',
          }}>{s}</div>
        ))}
      </div>

      {step === 1 && (
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: 20 }}>Campaign Details</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div><label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Campaign Name</label><input value={name} onChange={e => setName(e.target.value)} placeholder="Q3 Newsletter" /></div>
            <div><label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Subject Line</label><input value={subject} onChange={e => setSubject(e.target.value)} placeholder="Your cloud career update" /></div>
            <div><label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Preview Text</label><input value={previewText} onChange={e => setPreviewText(e.target.value)} placeholder="See what's new..." /></div>
            <div><label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>Audience</label>
              <select value={segmentId} onChange={e => setSegmentId(e.target.value)}>
                <option value="">All active contacts</option>
                {segments.map(s => <option key={s.id} value={s.id}>{s.name} ({s.contact_count})</option>)}
              </select>
            </div>
            <button className="btn-primary" onClick={() => setStep(2)} disabled={!name || !subject}>Next: Content</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: 20 }}>Content</h2>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <input placeholder="Describe your email topic for AI generation..." value={aiTopic} onChange={e => setAiTopic(e.target.value)} style={{ flex: 1 }} />
            <button className="btn-primary" onClick={handleGenerate} disabled={generateMutation.isPending || !aiTopic}>
              <Sparkles size={14} style={{ marginRight: 6 }} />{generateMutation.isPending ? 'Generating...' : 'AI Generate'}
            </button>
          </div>
          <textarea value={htmlContent} onChange={e => setHtmlContent(e.target.value)} placeholder="Paste your HTML email content here, or use AI Generate above..." rows={16} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }} />
          <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
            <button className="btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary" onClick={() => setStep(3)} disabled={!htmlContent}>Next: Review</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h2 style={{ fontSize: '1.125rem', marginBottom: 20 }}>Review & Create</h2>
          <div style={{ display: 'grid', gap: 12, fontSize: '0.875rem' }}>
            <div><strong>Name:</strong> {name}</div>
            <div><strong>Subject:</strong> {subject}</div>
            <div><strong>Preview:</strong> {previewText || '—'}</div>
            <div><strong>Audience:</strong> {segmentId ? segments.find(s => s.id === segmentId)?.name : 'All active contacts'}</div>
            <div><strong>Content:</strong> {htmlContent.length.toLocaleString()} chars</div>
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
            <button className="btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button className="btn-primary" onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Campaign'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
