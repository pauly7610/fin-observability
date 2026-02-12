import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const AgenticWorkflowScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const taglineOpacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: 'clamp' });

  const queueOpacity = interpolate(frame, [45, 70], [0, 1], { extrapolateRight: 'clamp' });
  const queueX = spring({ frame: frame - 45, fps, from: -80, to: 0, durationInFrames: 30 });

  const buttonPressed = frame >= 100 && frame <= 115;
  const buttonScale = buttonPressed ? 0.95 : 1;

  const approveOpacity = interpolate(frame, [120, 145], [0, 1], { extrapolateRight: 'clamp' });
  const auditOpacity = interpolate(frame, [150, 170], [0, 1], { extrapolateRight: 'clamp' });
  const rbacOpacity = interpolate(frame, [175, 190], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 50,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 12 }}>
        <h2 style={{ fontSize: 32, color: 'white', margin: 0, fontWeight: 700 }}>
          Human-in-the-Loop
        </h2>
      </div>
      <div style={{ opacity: taglineOpacity, marginBottom: 28 }}>
        <p style={{ fontSize: 18, color: '#94a3b8', margin: 0 }}>
          Every override logged. Role-gated approvals.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        {/* Left - Approval Queue */}
        <div
          style={{
            flex: 1,
            opacity: queueOpacity,
            transform: `translateX(${queueX}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 20 }}>
              Approval Queue
            </h3>

            {/* Flagged transaction */}
            <div
              style={{
                padding: 18,
                backgroundColor: 'rgba(234, 179, 8, 0.1)',
                borderRadius: 12,
                border: '1px solid rgba(234, 179, 8, 0.4)',
                marginBottom: 16,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600 }}>
                  txn_suspicious_001 — $50,000 Wire
                </span>
                <span
                  style={{
                    padding: '4px 10px',
                    backgroundColor: 'rgba(234, 179, 8, 0.2)',
                    color: '#eab308',
                    fontSize: 11,
                    fontWeight: 600,
                    borderRadius: 6,
                  }}
                >
                  MANUAL REVIEW
                </span>
              </div>
              <p style={{ color: '#94a3b8', fontSize: 12, margin: 0, lineHeight: 1.5 }}>
                SHAP: amount (+0.32), off_hours (+0.28). Agent: high anomaly, recommend review.
              </p>
            </div>

            {/* Approve button */}
            <div
              style={{
                display: 'flex',
                gap: 12,
              }}
            >
              <div
                style={{
                  flex: 1,
                  padding: '14px 20px',
                  backgroundColor: buttonPressed ? '#15803d' : '#22c55e',
                  borderRadius: 10,
                  color: 'white',
                  fontSize: 16,
                  fontWeight: 600,
                  textAlign: 'center',
                  transform: `scale(${buttonScale})`,
                }}
              >
                Approve
              </div>
              <div
                style={{
                  flex: 1,
                  padding: '14px 20px',
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid rgba(239, 68, 68, 0.5)',
                  borderRadius: 10,
                  color: '#f87171',
                  fontSize: 16,
                  fontWeight: 600,
                  textAlign: 'center',
                }}
              >
                Override
              </div>
            </div>
          </div>
        </div>

        {/* Right - Audit Log */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              opacity: auditOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              marginBottom: 20,
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 16 }}>
              Audit Log
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div
                style={{
                  padding: 12,
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 8,
                  borderLeft: '3px solid #3b82f6',
                }}
              >
                <span style={{ color: '#64748b', fontSize: 11 }}>10:30:01 — </span>
                <span style={{ color: '#f1f5f9', fontSize: 13 }}>Agent flagged: anomaly_score=0.847</span>
              </div>
              <div
                style={{
                  padding: 12,
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 8,
                  borderLeft: '3px solid #22c55e',
                }}
              >
                <span style={{ color: '#64748b', fontSize: 11 }}>10:31:45 — </span>
                <span style={{ color: '#f1f5f9', fontSize: 13 }}>Compliance officer approved</span>
              </div>
              <div
                style={{
                  padding: 12,
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: 8,
                  borderLeft: '3px solid #94a3b8',
                }}
              >
                <span style={{ color: '#64748b', fontSize: 11 }}>10:31:45 — </span>
                <span style={{ color: '#f1f5f9', fontSize: 13 }}>Audit trail updated (SEC_17a4)</span>
              </div>
            </div>
          </div>

          {/* RBAC badge */}
          <div
            style={{
              opacity: rbacOpacity,
              padding: 16,
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderRadius: 12,
              border: '1px solid rgba(59, 130, 246, 0.3)',
            }}
          >
            <p style={{ color: '#60a5fa', fontSize: 14, margin: 0, fontWeight: 600 }}>
              Role-gated: 4 roles, 25 permissions
            </p>
            <p style={{ color: '#94a3b8', fontSize: 12, margin: '6px 0 0' }}>
              admin • compliance • analyst • viewer
            </p>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
