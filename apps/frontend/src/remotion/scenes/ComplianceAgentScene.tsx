import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const ComplianceAgentScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
  
  // Transaction card animation
  const cardOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' });
  const cardX = spring({ frame: frame - 30, fps, from: -100, to: 0, durationInFrames: 30 });

  // Button click animation
  const buttonPressed = frame >= 80 && frame <= 90;
  const buttonScale = buttonPressed ? 0.95 : 1;

  // Result animation
  const resultOpacity = interpolate(frame, [100, 120], [0, 1], { extrapolateRight: 'clamp' });
  const resultY = spring({ frame: frame - 100, fps, from: 30, to: 0, durationInFrames: 30 });

  // Decision badge animation
  const badgeScale = spring({ frame: frame - 120, fps, from: 0, to: 1, durationInFrames: 20 });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 60,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div
        style={{
          opacity: headerOpacity,
          marginBottom: 40,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 48 }}>🤖</span>
          <h2 style={{ fontSize: 42, color: 'white', margin: 0, fontWeight: 700 }}>
            Financial Compliance Agent
          </h2>
        </div>
        <p style={{ fontSize: 24, color: '#94a3b8', marginTop: 12 }}>
          Real-time transaction monitoring with AI-powered decisions
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Left side - Transaction Input */}
        <div
          style={{
            flex: 1,
            opacity: cardOpacity,
            transform: `translateX(${cardX}px)`,
          }}
        >
          {/* Transaction Card */}
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 32,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 24, marginBottom: 24 }}>
              Transaction Details
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'ID', value: 'txn_suspicious_001' },
                { label: 'Amount', value: '$50,000', highlight: true },
                { label: 'Type', value: 'Wire Transfer', highlight: true },
                { label: 'Counterparty', value: 'ACME Corp' },
                { label: 'Account', value: '9876543210' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8', fontSize: 18 }}>{item.label}</span>
                  <span
                    style={{
                      color: item.highlight ? '#fbbf24' : '#f1f5f9',
                      fontSize: 18,
                      fontWeight: item.highlight ? 600 : 400,
                    }}
                  >
                    {item.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Run Button */}
            <button
              style={{
                marginTop: 32,
                width: '100%',
                padding: '16px 32px',
                backgroundColor: buttonPressed ? '#1d4ed8' : '#3b82f6',
                border: 'none',
                borderRadius: 12,
                color: 'white',
                fontSize: 20,
                fontWeight: 600,
                cursor: 'pointer',
                transform: `scale(${buttonScale})`,
                transition: 'transform 0.1s',
              }}
            >
              🔍 Run Compliance Check
            </button>
          </div>
        </div>

        {/* Right side - Results */}
        <div
          style={{
            flex: 1,
            opacity: resultOpacity,
            transform: `translateY(${resultY}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 32,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            {/* Decision Badge */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                marginBottom: 24,
                transform: `scale(${Math.min(badgeScale, 1)})`,
              }}
            >
              <div
                style={{
                  padding: '12px 24px',
                  backgroundColor: 'rgba(234, 179, 8, 0.2)',
                  border: '2px solid #eab308',
                  borderRadius: 8,
                  color: '#fbbf24',
                  fontSize: 20,
                  fontWeight: 700,
                }}
              >
                MANUAL REVIEW
              </div>
              <span style={{ color: '#94a3b8', fontSize: 18 }}>
                Confidence: <span style={{ color: '#f1f5f9', fontWeight: 600 }}>85%</span>
              </span>
            </div>

            {/* Reasoning */}
            <div
              style={{
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderLeft: '4px solid #3b82f6',
                padding: 20,
                borderRadius: '0 8px 8px 0',
                marginBottom: 24,
              }}
            >
              <p style={{ color: '#60a5fa', fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
                🧠 Agent Reasoning:
              </p>
              <p style={{ color: '#93c5fd', fontSize: 16, lineHeight: 1.5 }}>
                High anomaly score (0.800) requires human review. Statistical outlier detected - unusual transaction pattern.
              </p>
            </div>

            {/* Audit Trail */}
            <div
              style={{
                backgroundColor: 'rgba(148, 163, 184, 0.1)',
                padding: 16,
                borderRadius: 8,
              }}
            >
              <p style={{ color: '#94a3b8', fontSize: 14, fontWeight: 600, marginBottom: 12 }}>
                📋 Audit Trail
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 14 }}>Regulation:</span>
                  <span style={{ color: '#f1f5f9', fontSize: 14 }}>SEC_17a4</span>
                </div>
                <div style={{ display: 'flex', gap: 12 }}>
                  <span style={{ color: '#64748b', fontSize: 14 }}>Agent:</span>
                  <span style={{ color: '#f1f5f9', fontSize: 14 }}>AnomalyDetector</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
