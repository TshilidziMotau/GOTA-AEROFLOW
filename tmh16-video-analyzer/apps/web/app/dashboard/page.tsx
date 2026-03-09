'use client';

import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

export default function DashboardPage() {
  const [projectId, setProjectId] = useState('1');
  const [cards, setCards] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [readiness, setReadiness] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);
  const [governanceEvents, setGovernanceEvents] = useState<any[]>([]);
  const [finalReview, setFinalReview] = useState<any>(null);
  const [manifestHash, setManifestHash] = useState('');
  const [manifestDrift, setManifestDrift] = useState<any>(null);
  const [releaseReadiness, setReleaseReadiness] = useState<any>(null);
  const [releaseAudit, setReleaseAudit] = useState<any>(null);
  const [releaseCandidate, setReleaseCandidate] = useState<any>(null);
  const [candidateLock, setCandidateLock] = useState<any>(null);
  const [releasePackage, setReleasePackage] = useState<any>(null);
  const [releasePackageExport, setReleasePackageExport] = useState<any>(null);
  const [message, setMessage] = useState('');

  const load = () => {
    api.get(`/projects/${projectId}/tmh16-alignment`).then((r) => setCards(r.data.cards || [])).catch(() => setCards([]));
    api.get(`/projects/${projectId}/summary`).then((r) => setSummary(r.data)).catch(() => setSummary(null));
    api.get(`/projects/${projectId}/readiness`).then((r) => setReadiness(r.data)).catch(() => setReadiness(null));
    api.get(`/projects/${projectId}/analysis/status`).then((r) => setRuns(r.data || [])).catch(() => setRuns([]));
    api.get(`/projects/${projectId}/analysis/audit`).then((r) => setGovernanceEvents(r.data.governance_events || [])).catch(() => setGovernanceEvents([]));
    api.get(`/projects/${projectId}/evidence-manifest`).then((r) => setManifestHash(r.data.sha256 || '')).catch(() => setManifestHash(''));
    api.get(`/projects/${projectId}/manifest-drift`).then((r) => setManifestDrift(r.data)).catch(() => setManifestDrift(null));
    api.get(`/projects/${projectId}/release-readiness`).then((r) => setReleaseReadiness(r.data)).catch(() => setReleaseReadiness(null));
    api.get(`/projects/${projectId}/release-audit`).then((r) => setReleaseAudit(r.data)).catch(() => setReleaseAudit(null));
    api.get(`/projects/${projectId}/release-candidate`).then((r) => setReleaseCandidate(r.data)).catch(() => setReleaseCandidate(null));
    api.get(`/projects/${projectId}/release-candidate-lock`).then((r) => setCandidateLock(r.data)).catch(() => setCandidateLock(null));
    api.get(`/projects/${projectId}/release-package`).then((r) => setReleasePackage(r.data)).catch(() => setReleasePackage(null));
    api.get(`/projects/${projectId}/release-package/export`).then((r) => setReleasePackageExport(r.data)).catch(() => setReleasePackageExport(null));
    api.get(`/projects/${projectId}/final-review`).then((r) => setFinalReview(r.data)).catch(() => setFinalReview(null));
  };

  useEffect(() => {
    load();
  }, [projectId]);

  const setRunStatus = async (runId: number, status: 'review_needed' | 'completed' | 'failed') => {
    try {
      await api.post(`/projects/${projectId}/analysis/${runId}/review`, { status, note: `Status updated via dashboard to ${status}` });
      setMessage(`Run ${runId} updated to ${status}.`);
      load();
    } catch {
      setMessage(`Failed to update run ${runId}.`);
    }
  };

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="text-sm text-slate-600">TMH16 alignment checklist support (not legal compliance).</p>
      <input className="border p-2" value={projectId} onChange={(e) => setProjectId(e.target.value)} placeholder="Project ID" />

      <div className="flex gap-2 flex-wrap">
        <button className="border px-3 py-2" onClick={async () => {
          try {
            const res = await api.post(`/projects/${projectId}/analysis/run`, { frame_skip: 3, confidence_threshold: 0.4 });
            setMessage(`Analysis queued: run ${res.data.run_id}`);
            load();
          } catch {
            setMessage('Failed to start analysis run.');
          }
        }}>Run Analysis</button>

        <button className="border px-3 py-2" onClick={async () => {
          if (!summary?.latest_run?.id) {
            setMessage('No run available to retry.');
            return;
          }
          try {
            const res = await api.post(`/projects/${projectId}/analysis/${summary.latest_run.id}/retry`);
            setMessage(`Retry queued: run ${res.data.run_id}`);
            load();
          } catch {
            setMessage('Failed to retry analysis run.');
          }
        }}>Retry Latest Run</button>
      </div>

      {message && <p className="text-xs text-slate-700">{message}</p>}


      {manifestHash && (
        <div className="border rounded bg-white p-3 text-sm">
          <p className="font-medium">Evidence manifest hash (SHA-256)</p>
          <p className="text-xs break-all mt-1">{manifestHash}</p>
        </div>
      )}



      {manifestDrift && (
        <div className="border rounded bg-white p-3 text-sm">
          <p className="font-medium">Manifest snapshot status</p>
          <p className="text-xs mt-1">Approved snapshot: {manifestDrift.has_approved_snapshot ? 'yes' : 'no'}</p>
          <p className="text-xs">Drift detected: <strong>{manifestDrift.drift_detected ? 'YES' : 'NO'}</strong></p>
          {manifestDrift.last_approved_at && <p className="text-xs">Last approved: {manifestDrift.last_approved_at}</p>}
          <button className="border px-2 py-1 text-xs mt-2" onClick={async () => {
            try {
              await api.post(`/projects/${projectId}/manifest-snapshot/approve`);
              setMessage('Manifest snapshot approved.');
              load();
            } catch {
              setMessage('Failed to approve manifest snapshot.');
            }
          }}>Approve Snapshot</button>
          <p className="text-xs text-slate-600 mt-1">{manifestDrift.disclaimer}</p>
        </div>
      )}

      {readiness && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Readiness: <strong>{readiness.ready_for_professional_review ? 'READY' : 'INCOMPLETE'}</strong></p>
          {!readiness.ready_for_professional_review && (
            <p className="text-xs">Missing: {(readiness.missing_items || []).join(', ')}</p>
          )}
          <p className="text-xs text-slate-600">{readiness.disclaimer}</p>
        </div>
      )}


      {finalReview && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Final review: <strong>{finalReview.checks?.final_review_approved ? 'APPROVED' : 'PENDING'}</strong></p>
          <p className="text-xs">Can issue draft pack: {finalReview.can_issue_draft_pack ? 'yes' : 'no'}</p>
          {!finalReview.can_issue_draft_pack && <p className="text-xs">Blockers: {(finalReview.blockers || []).join(', ')}</p>}
          <button className="border px-2 py-1 text-xs" onClick={async () => {
            try {
              await api.post(`/projects/${projectId}/final-review/approve`);
              setMessage('Final review approved.');
              load();
            } catch {
              setMessage('Final review approval failed (resolve blockers first).');
            }
          }}>Approve Final Review</button>
          <p className="text-xs text-slate-600">{finalReview.disclaimer}</p>
        </div>
      )}



      {releaseReadiness && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Release readiness: <strong>{releaseReadiness.can_issue_draft_pack ? 'READY' : 'BLOCKED'}</strong></p>
          {!releaseReadiness.can_issue_draft_pack && <p className="text-xs">Blockers: {(releaseReadiness.blockers || []).join(', ')}</p>}
          <button className="border px-2 py-1 text-xs" onClick={async () => {
            try {
              await api.post(`/projects/${projectId}/release/issue-draft-pack`);
              setMessage('Draft pack issued and audit recorded.');
              load();
            } catch {
              setMessage('Draft pack issue failed (resolve readiness blockers first).');
            }
          }}>Issue Draft Pack</button>
          <p className="text-xs text-slate-600">{releaseReadiness.disclaimer}</p>
        </div>
      )}

      {summary && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p>Latest run: <strong>{summary.latest_run ? `#${summary.latest_run.id} (${summary.latest_run.status})` : 'none'}</strong></p>
          <p>Latest export: <strong>{summary.latest_export ? `${summary.latest_export.type}` : 'none'}</strong></p>
          <p>Queue max: <strong>{summary.queue_max}</strong> · Pedestrians: <strong>{summary.total_pedestrians}</strong></p>
          <p>Alignment complete: <strong>{summary.alignment_complete_count}/{summary.alignment_total_count}</strong></p>
        </div>
      )}

      <div className="border rounded bg-white p-3 text-sm space-y-2">
        <p className="font-medium">Analysis runs</p>
        <div className="space-y-2 max-h-64 overflow-auto">
          {runs.map((r) => (
            <div key={r.id} className="border rounded p-2 text-xs">
              <p>Run #{r.id} · {r.status}</p>
              <div className="flex gap-2 mt-1 flex-wrap">
                <button className="border px-2 py-1" onClick={() => setRunStatus(r.id, 'review_needed')}>Mark Review Needed</button>
                <button className="border px-2 py-1" onClick={() => setRunStatus(r.id, 'completed')}>Mark Completed</button>
                <button className="border px-2 py-1" onClick={() => setRunStatus(r.id, 'failed')}>Mark Failed</button>
              </div>
            </div>
          ))}
        </div>
      </div>





      {releaseCandidate && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p className="font-medium">Release candidate snapshot</p>
          <p className="text-xs">Candidate hash: <span className="break-all">{releaseCandidate.candidate_sha256}</span></p>
          <p className="text-xs">Manifest hash: <span className="break-all">{releaseCandidate.manifest_sha256}</span></p>
          <p className="text-xs">Ready to issue: {releaseCandidate.can_issue_draft_pack ? 'yes' : 'no'}</p>
          <p className="text-xs text-slate-600">{releaseCandidate.disclaimer}</p>
        </div>
      )}



      {candidateLock && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p className="font-medium">Release candidate lock</p>
          <p className="text-xs">Locked candidate present: {candidateLock.has_locked_candidate ? 'yes' : 'no'}</p>
          <p className="text-xs">Lock drift detected: <strong>{candidateLock.drift_detected ? 'YES' : 'NO'}</strong></p>
          <button className="border px-2 py-1 text-xs" onClick={async () => {
            try {
              await api.post(`/projects/${projectId}/release-candidate-lock`);
              setMessage('Release candidate locked.');
              load();
            } catch {
              setMessage('Failed to lock release candidate.');
            }
          }}>Lock Release Candidate</button>
          <p className="text-xs text-slate-600">{candidateLock.disclaimer}</p>
        </div>
      )}



      {releasePackage && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p className="font-medium">Release package fingerprint</p>
          <p className="text-xs">Package hash: <span className="break-all">{releasePackage.package_sha256}</span></p>
          <p className="text-xs">Candidate lock drift: {releasePackage.candidate_lock_drift_detected ? 'YES' : 'NO'}</p>
          <p className="text-xs">Manifest drift: {releasePackage.manifest_drift_detected ? 'YES' : 'NO'}</p>
          <p className="text-xs text-slate-600">{releasePackage.disclaimer}</p>
        </div>
      )}



      {releasePackageExport && (
        <div className="border rounded bg-white p-3 text-sm space-y-1">
          <p className="font-medium">Release package export</p>
          <p className="text-xs">Package hash: <span className="break-all">{releasePackageExport.package_sha256}</span></p>
          <button className="border px-2 py-1 text-xs" onClick={() => {
            try {
              navigator.clipboard.writeText(releasePackageExport.content || '');
              setMessage('Release package JSON copied to clipboard.');
            } catch {
              setMessage('Unable to copy release package JSON.');
            }
          }}>Copy Package JSON</button>
          <p className="text-xs text-slate-600">{releasePackageExport.disclaimer}</p>
        </div>
      )}

      {releaseAudit && (
        <div className="border rounded bg-white p-3 text-sm space-y-2">
          <p className="font-medium">Release governance audit</p>
          <p className="text-xs">Events tracked: {releaseAudit.event_count}</p>
          <div className="text-xs space-y-1">
            <p>Latest counts approval: {releaseAudit.latest?.approve_counts?.created_at || 'none'}</p>
            <p>Latest final review approval: {releaseAudit.latest?.final_review_approved?.created_at || 'none'}</p>
            <p>Latest manifest snapshot approval: {releaseAudit.latest?.manifest_snapshot_approved?.created_at || 'none'}</p>
            <p>Latest draft-pack issue: {releaseAudit.latest?.draft_pack_issued?.created_at || 'none'}</p>
          </div>
          <p className="text-xs text-slate-600">{releaseAudit.disclaimer}</p>
        </div>
      )}

      <div className="border rounded bg-white p-3 text-sm space-y-2">
        <p className="font-medium">Analysis governance events</p>
        <div className="space-y-1 max-h-48 overflow-auto text-xs">
          {governanceEvents.map((e) => (
            <div key={e.id} className="border rounded p-2">#{e.id} · {e.edit_type} · user {e.user_id}</div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-3">
        {cards.map((c, idx) => (
          <div key={idx} className="border rounded bg-white p-3 text-sm">
            <p className="font-medium">{c.topic}</p>
            <p className="text-xs mt-1">Status: {c.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
