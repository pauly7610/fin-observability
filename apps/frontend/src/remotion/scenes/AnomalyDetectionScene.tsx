import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const transactions = [
  { id: 'TXN-001', amount: '$2,500', score: 0.12, status: 'normal' },
  { id: 'TXN-002', amount: '$8,200', score: 0.23, status: 'normal' },
  { id: 'TXN-003', amount: '$45,000', score: 0.87, status: 'anomaly' },
  { id: 'TXN-004', amount: '$1,800', score: 0.08, status: 'normal' },
  { id: 'TXN-005', amount: '$125,000', score: 0.95, status: 'anomaly' },
];

export const AnomalyDetectionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Stagger row animations
  const getRowAnimation = (index: number) => {
    const startFrame = 30 + index * 15;
    const opacity = interpolate(frame, [startFrame, startFrame + 15], [0, 1], { extrapolateRight: 'clamp' });
    const x = spring({ frame: frame - startFrame, fps, from: -50, to: 0, durationInFrames: 20 });
    return { opacity, x };
  };

  // Highlight anomaly pulse
  const pulseOpacity = interpolate(
    frame % 30,
    [0, 15, 30],
    [0.3, 0.6, 0.3],
    { extrapolateRight: 'clamp' }
  );

  // Model info animation
  const modelInfoOpacity = interpolate(frame, [120, 140], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 60,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 48 }}>🔬</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            Real-Time Anomaly Detection
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          Isolation Forest ML model identifies suspicious transactions instantly
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Transaction Table */}
        <div style={{ flex: 2 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              overflow: 'hidden',
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            {/* Table Header */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr 1fr',
                padding: '16px 24px',
                backgroundColor: 'rgba(15, 23, 42, 0.5)',
                borderBottom: '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              {['Transaction ID', 'Amount', 'Anomaly Score', 'Status'].map((header) => (
                <span key={header} style={{ color: '#94a3b8', fontSize: 14, fontWeight: 600 }}>
                  {header}
                </span>
              ))}
            </div>

            {/* Table Rows */}
            {transactions.map((txn, index) => {
              const { opacity, x } = getRowAnimation(index);
              const isAnomaly = txn.status === 'anomaly';
              
              return (
                <div
                  key={txn.id}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr 1fr',
                    padding: '16px 24px',
                    opacity,
                    transform: `translateX(${x}px)`,
                    backgroundColor: isAnomaly ? `rgba(239, 68, 68, ${pulseOpacity})` : 'transparent',
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                  }}
                >
                  <span style={{ color: '#f1f5f9', fontSize: 16 }}>{txn.id}</span>
                  <span style={{ color: isAnomaly ? '#fca5a5' : '#f1f5f9', fontSize: 16, fontWeight: isAnomaly ? 600 : 400 }}>
                    {txn.amount}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div
                      style={{
                        width: 60,
                        height: 8,
                        backgroundColor: 'rgba(148, 163, 184, 0.2)',
                        borderRadius: 4,
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${txn.score * 100}%`,
                          height: '100%',
                          backgroundColor: txn.score > 0.7 ? '#ef4444' : txn.score > 0.4 ? '#eab308' : '#22c55e',
                          borderRadius: 4,
                        }}
                      />
                    </div>
                    <span style={{ color: '#94a3b8', fontSize: 14 }}>{txn.score.toFixed(2)}</span>
                  </div>
                  <span
                    style={{
                      padding: '4px 12px',
                      borderRadius: 12,
                      fontSize: 12,
                      fontWeight: 600,
                      backgroundColor: isAnomaly ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                      color: isAnomaly ? '#ef4444' : '#22c55e',
                      width: 'fit-content',
                    }}
                  >
                    {isAnomaly ? '⚠️ ANOMALY' : '✓ Normal'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Model Info */}
        <div
          style={{
            flex: 1,
            opacity: modelInfoOpacity,
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
            <h3 style={{ color: '#f1f5f9', fontSize: 20, marginBottom: 20 }}>
              🧠 Model Details
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'Algorithm', value: 'Isolation Forest' },
                { label: 'Contamination', value: '1%' },
                { label: 'Features', value: '12' },
                { label: 'Threshold', value: '0.70' },
                { label: 'Last Trained', value: '2 hours ago' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8', fontSize: 14 }}>{item.label}</span>
                  <span style={{ color: '#f1f5f9', fontSize: 14, fontWeight: 500 }}>{item.value}</span>
                </div>
              ))}
            </div>

            <div
              style={{
                marginTop: 24,
                padding: 16,
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                borderRadius: 8,
                border: '1px solid rgba(139, 92, 246, 0.3)',
              }}
            >
              <p style={{ color: '#a78bfa', fontSize: 14, margin: 0 }}>
                💡 Model retrains automatically from historical transaction data
              </p>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
