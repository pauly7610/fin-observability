import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

const transactions = [
  { id: 'TXN-001', amount: '$2,500', score: 0.12, action: 'approve' },
  { id: 'TXN-002', amount: '$8,200', score: 0.23, action: 'approve' },
  { id: 'TXN-003', amount: '$45,000', score: 0.87, action: 'manual_review' },
  { id: 'TXN-004', amount: '$125,000', score: 0.95, action: 'block' },
];

export const AnomalyDetectionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const line1Opacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' });
  const line2Opacity = interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' });

  const ifOpacity = interpolate(frame, [60, 85], [0, 1], { extrapolateRight: 'clamp' });
  const pcaOpacity = interpolate(frame, [85, 110], [0, 1], { extrapolateRight: 'clamp' });
  const arrowOpacity = interpolate(frame, [115, 135], [0, 1], { extrapolateRight: 'clamp' });
  const ensembleOpacity = interpolate(frame, [140, 165], [0, 1], { extrapolateRight: 'clamp' });
  const ensembleScale = spring({ frame: frame - 140, fps, from: 0.8, to: 1, durationInFrames: 25 });

  const tableOpacity = interpolate(frame, [175, 195], [0, 1], { extrapolateRight: 'clamp' });
  const onnxOpacity = interpolate(frame, [200, 220], [0, 1], { extrapolateRight: 'clamp' });

  const getActionStyle = (action: string) => {
    switch (action) {
      case 'approve':
        return { bg: 'rgba(34, 197, 94, 0.2)', color: '#22c55e' };
      case 'manual_review':
        return { bg: 'rgba(234, 179, 8, 0.2)', color: '#eab308' };
      case 'block':
        return { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.2)', color: '#94a3b8' };
    }
  };

  const getActionLabel = (action: string) => {
    switch (action) {
      case 'approve':
        return 'approve';
      case 'manual_review':
        return 'manual review';
      case 'block':
        return 'block';
      default:
        return action;
    }
  };

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
          Real-Time Anomaly Detection
        </h2>
      </div>
      <div style={{ opacity: line1Opacity, marginBottom: 4 }}>
        <p style={{ fontSize: 20, color: '#f1f5f9', margin: 0, fontWeight: 600 }}>
          Ensemble ML: 2 models, higher precision
        </p>
      </div>
      <div style={{ opacity: line2Opacity, marginBottom: 28 }}>
        <p style={{ fontSize: 16, color: '#94a3b8', margin: 0 }}>
          ONNX Runtime: &lt;50ms inference
        </p>
      </div>

      <div style={{ display: 'flex', gap: 32 }}>
        {/* Left - Ensemble Architecture */}
        <div style={{ flex: 1.2 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 24,
              marginBottom: 28,
            }}
          >
            {/* Isolation Forest */}
            <div
              style={{
                flex: 1,
                opacity: ifOpacity,
                backgroundColor: 'rgba(30, 41, 59, 0.8)',
                borderRadius: 12,
                padding: 20,
                border: '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              <p style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8, fontWeight: 600 }}>
                Isolation Forest
              </p>
              <p style={{ color: '#3b82f6', fontSize: 28, margin: 0, fontWeight: 700 }}>
                0.82
              </p>
            </div>

            {/* Plus */}
            <span style={{ opacity: arrowOpacity, color: '#64748b', fontSize: 24, fontWeight: 700 }}>
              +
            </span>

            {/* PCA-Autoencoder */}
            <div
              style={{
                flex: 1,
                opacity: pcaOpacity,
                backgroundColor: 'rgba(30, 41, 59, 0.8)',
                borderRadius: 12,
                padding: 20,
                border: '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              <p style={{ color: '#94a3b8', fontSize: 12, marginBottom: 8, fontWeight: 600 }}>
                PCA-Autoencoder
              </p>
              <p style={{ color: '#8b5cf6', fontSize: 28, margin: 0, fontWeight: 700 }}>
                0.79
              </p>
            </div>

            {/* Arrow */}
            <span style={{ opacity: arrowOpacity, color: '#64748b', fontSize: 24 }}>→</span>

            {/* Ensemble */}
            <div
              style={{
                flex: 1,
                opacity: ensembleOpacity,
                transform: `scale(${ensembleScale})`,
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                borderRadius: 12,
                padding: 20,
                border: '2px solid rgba(34, 197, 94, 0.5)',
              }}
            >
              <p style={{ color: '#86efac', fontSize: 12, marginBottom: 8, fontWeight: 600 }}>
                Ensemble
              </p>
              <p style={{ color: '#22c55e', fontSize: 28, margin: 0, fontWeight: 700 }}>
                0.847
              </p>
              <p style={{ color: '#94a3b8', fontSize: 11, margin: '4px 0 0' }}>
                higher confidence
              </p>
            </div>
          </div>

          {/* Transaction Table */}
          <div
            style={{
              opacity: tableOpacity,
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 12,
              overflow: 'hidden',
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr 1fr',
                padding: '12px 20px',
                backgroundColor: 'rgba(15, 23, 42, 0.5)',
                borderBottom: '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              {['ID', 'Amount', 'Anomaly', 'Action'].map((h) => (
                <span key={h} style={{ color: '#94a3b8', fontSize: 12, fontWeight: 600 }}>
                  {h}
                </span>
              ))}
            </div>
            {transactions.map((txn) => {
              const style = getActionStyle(txn.action);
              return (
                <div
                  key={txn.id}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr 1fr',
                    padding: '12px 20px',
                    borderBottom: '1px solid rgba(148, 163, 184, 0.1)',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ color: '#f1f5f9', fontSize: 13, fontFamily: 'monospace' }}>
                    {txn.id}
                  </span>
                  <span style={{ color: '#f1f5f9', fontSize: 13 }}>{txn.amount}</span>
                  <span style={{ color: '#94a3b8', fontSize: 13 }}>{txn.score.toFixed(2)}</span>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: 6,
                      fontSize: 11,
                      fontWeight: 600,
                      backgroundColor: style.bg,
                      color: style.color,
                      width: 'fit-content',
                    }}
                  >
                    {getActionLabel(txn.action)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right - ONNX */}
        <div
          style={{
            flex: 0.8,
            opacity: onnxOpacity,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(139, 92, 246, 0.3)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 16 }}>
              ONNX Runtime
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'IF Model', value: 'Scikit-learn' },
                { label: 'PCA Model', value: 'ONNX' },
                { label: 'Inference', value: '<50ms' },
                { label: 'Threshold', value: '0.70' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8', fontSize: 13 }}>{item.label}</span>
                  <span style={{ color: '#f1f5f9', fontSize: 13, fontWeight: 500 }}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
