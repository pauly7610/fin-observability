import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const testTransactions = [
  { id: 'txn_safe_001', label: 'Safe ($5k ACH)', type: 'ach', selected: false },
  { id: 'txn_suspicious_001', label: 'Suspicious ($50k Wire)', type: 'wire', selected: true },
  { id: 'txn_blocked_001', label: 'Should Block ($150k Wire)', type: 'wire', selected: false },
];

export const ComplianceAgentScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  const badgesOpacity = interpolate(frame, [25, 45], [0, 1], { extrapolateRight: 'clamp' });

  const txnButtonsOpacity = interpolate(frame, [50, 70], [0, 1], { extrapolateRight: 'clamp' });
  const txnButtonsX = spring({ frame: frame - 50, fps, from: -80, to: 0, durationInFrames: 25 });

  const payloadOpacity = interpolate(frame, [80, 100], [0, 1], { extrapolateRight: 'clamp' });

  const buttonPressed = frame >= 110 && frame <= 125;
  const buttonScale = buttonPressed ? 0.95 : 1;

  const scoreOpacity = interpolate(frame, [140, 160], [0, 1], { extrapolateRight: 'clamp' });
  const badgeOpacity = interpolate(frame, [170, 190], [0, 1], { extrapolateRight: 'clamp' });
  const reasoningOpacity = interpolate(frame, [200, 220], [0, 1], { extrapolateRight: 'clamp' });
  const auditOpacity = interpolate(frame, [220, 235], [0, 1], { extrapolateRight: 'clamp' });

  const taglineOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 50,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Tagline */}
      <div
        style={{
          position: 'absolute',
          top: 24,
          left: 50,
          right: 50,
          textAlign: 'center',
          opacity: taglineOpacity,
        }}
      >
        <p style={{ color: '#94a3b8', fontSize: 18, margin: 0, fontWeight: 500 }}>
          Transaction → ML Score → Agent Decision → Audit Log
        </p>
      </div>

      {/* Header */}
      <div
        style={{
          opacity: headerOpacity,
          marginBottom: 24,
          marginTop: 56,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h2 style={{ fontSize: 32, color: 'white', margin: 0, fontWeight: 700 }}>
            Financial Compliance Agent
          </h2>
        </div>
      </div>

      {/* Badges */}
      <div
        style={{
          display: 'flex',
          gap: 12,
          opacity: badgesOpacity,
          marginBottom: 24,
        }}
      >
        {[
          { label: 'FINRA 4511', color: '#3b82f6' },
          { label: 'SEC 17a-4', color: '#3b82f6' },
          { label: 'Isolation Forest ML v2.0.0', color: '#8b5cf6' },
        ].map((b) => (
          <div
            key={b.label}
            style={{
              padding: '6px 14px',
              backgroundColor: `${b.color}20`,
              border: `1px solid ${b.color}50`,
              borderRadius: 6,
              color: b.color === '#3b82f6' ? '#60a5fa' : '#a78bfa',
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {b.label}
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        {/* Left - Transaction Input */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              opacity: txnButtonsOpacity,
              transform: `translateX(${txnButtonsX}px)`,
              marginBottom: 20,
            }}
          >
            <p style={{ color: '#94a3b8', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
              Test Transaction
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              {testTransactions.map((txn) => (
                <div
                  key={txn.id}
                  style={{
                    flex: 1,
                    padding: 14,
                    borderRadius: 10,
                    border: txn.selected ? '2px solid #3b82f6' : '1px solid rgba(148, 163, 184, 0.2)',
                    backgroundColor: txn.selected ? 'rgba(59, 130, 246, 0.1)' : 'rgba(30, 41, 59, 0.8)',
                  }}
                >
                  <span style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase' }}>
                    {txn.type}
                  </span>
                  <div style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 600, marginTop: 4 }}>
                    {txn.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              opacity: payloadOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 10,
              padding: 16,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <p style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, marginBottom: 8 }}>
              Transaction Payload
            </p>
            <pre
              style={{
                color: '#94a3b8',
                fontSize: 11,
                fontFamily: 'monospace',
                margin: 0,
                whiteSpace: 'pre-wrap',
              }}
            >
              {`{
  "id": "txn_suspicious_001",
  "amount": 50000,
  "type": "wire",
  "counterparty": "ACME Corp"
}`}
            </pre>
          </div>

          <div
            style={{
              marginTop: 20,
              width: '100%',
              padding: '14px 24px',
              backgroundColor: buttonPressed ? '#1d4ed8' : '#3b82f6',
              border: 'none',
              borderRadius: 10,
              color: 'white',
              fontSize: 16,
              fontWeight: 600,
              transform: `scale(${buttonScale})`,
            }}
          >
            Run Compliance Check
          </div>
        </div>

        {/* Right - Results */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 28,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            {/* Anomaly Score */}
            <div style={{ opacity: scoreOpacity, marginBottom: 20 }}>
              <p style={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}>Anomaly Score</p>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <div
                  style={{
                    flex: 1,
                    height: 8,
                    backgroundColor: 'rgba(148, 163, 184, 0.2)',
                    borderRadius: 4,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: '84.7%',
                      height: '100%',
                      backgroundColor: '#eab308',
                      borderRadius: 4,
                    }}
                  />
                </div>
                <span style={{ color: '#f1f5f9', fontSize: 18, fontWeight: 700 }}>0.847</span>
              </div>
            </div>

            {/* Decision Badge */}
            <div
              style={{
                opacity: badgeOpacity,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginBottom: 20,
              }}
            >
              <div
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'rgba(234, 179, 8, 0.2)',
                  border: '2px solid #eab308',
                  borderRadius: 8,
                  color: '#fbbf24',
                  fontSize: 16,
                  fontWeight: 700,
                }}
              >
                MANUAL REVIEW
              </div>
              <span style={{ color: '#94a3b8', fontSize: 14 }}>
                Confidence: <span style={{ color: '#f1f5f9', fontWeight: 600 }}>85%</span>
              </span>
            </div>

            {/* Reasoning */}
            <div
              style={{
                opacity: reasoningOpacity,
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderLeft: '4px solid #3b82f6',
                padding: 16,
                borderRadius: '0 8px 8px 0',
                marginBottom: 20,
              }}
            >
              <p style={{ color: '#60a5fa', fontSize: 14, fontWeight: 600, marginBottom: 6 }}>
                Agent Reasoning
              </p>
              <p style={{ color: '#93c5fd', fontSize: 14, lineHeight: 1.5, margin: 0 }}>
                High anomaly score (0.847) requires human review. Statistical outlier detected —
                unusual transaction pattern for off-hours wire transfer.
              </p>
            </div>

            {/* Audit Trail */}
            <div
              style={{
                opacity: auditOpacity,
                backgroundColor: 'rgba(148, 163, 184, 0.1)',
                padding: 14,
                borderRadius: 8,
              }}
            >
              <p style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600, marginBottom: 10 }}>
                Audit Trail
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 12 }}>Regulation:</span>
                  <span style={{ color: '#f1f5f9', fontSize: 12 }}>SEC_17a4</span>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 12 }}>Agent:</span>
                  <span style={{ color: '#f1f5f9', fontSize: 12 }}>AnomalyDetector</span>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 12 }}>Timestamp:</span>
                  <span style={{ color: '#f1f5f9', fontSize: 12 }}>2024-02-12T10:30:00Z</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
