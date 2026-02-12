import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const MCPScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const headerOpacity = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: 'clamp' });
  const configOpacity = interpolate(frame, [35, 55], [0, 1], { extrapolateRight: 'clamp' });
  const configX = spring({ frame: frame - 35, fps, from: -60, to: 0, durationInFrames: 25 });

  const chatQuestionOpacity = interpolate(frame, [90, 110], [0, 1], { extrapolateRight: 'clamp' });
  const chatResponseOpacity = interpolate(frame, [125, 150], [0, 1], { extrapolateRight: 'clamp' });
  const chatResponseY = spring({ frame: frame - 125, fps, from: 20, to: 0, durationInFrames: 25 });

  const taglineOpacity = interpolate(frame, [160, 175], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)',
        padding: 50,
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: 28 }}>
        <h2 style={{ fontSize: 36, color: 'white', margin: 0, fontWeight: 700 }}>
          MCP Server — Connect Claude or Cursor
        </h2>
        <p style={{ fontSize: 18, color: '#94a3b8', marginTop: 8 }}>
          Model Context Protocol — 9 tools for any AI agent
        </p>
      </div>

      <div style={{ display: 'flex', gap: 40 }}>
        {/* Left - JSON Config */}
        <div
          style={{
            flex: 1,
            opacity: configOpacity,
            transform: `translateX(${configX}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.9)',
              borderRadius: 12,
              padding: 20,
              border: '1px solid rgba(148, 163, 184, 0.2)',
              fontFamily: 'monospace',
            }}
          >
            <p style={{ color: '#64748b', fontSize: 12, marginBottom: 12 }}>
              Add to mcp.json / Cursor settings
            </p>
            <pre
              style={{
                color: '#22c55e',
                fontSize: 13,
                margin: 0,
                whiteSpace: 'pre-wrap',
                lineHeight: 1.6,
              }}
            >
              {`{
  "mcpServers": {
    "fin-observability": {
      "url": "https://fin-observability-production.up.railway.app/mcp",
      "transport": "streamable-http"
    }
  }
}`}
            </pre>
          </div>

          <div
            style={{
              marginTop: 20,
              display: 'flex',
              gap: 8,
              flexWrap: 'wrap',
            }}
          >
            {['check_transaction_compliance', 'explain_transaction', 'batch_check_compliance'].map(
              (tool, i) => (
                <span
                  key={tool}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                    borderRadius: 6,
                    color: '#60a5fa',
                    fontSize: 11,
                    fontFamily: 'monospace',
                  }}
                >
                  {tool}
                </span>
              )
            )}
          </div>
        </div>

        {/* Right - Chat Mock */}
        <div style={{ flex: 1 }}>
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.8)',
              borderRadius: 16,
              padding: 24,
              border: '1px solid rgba(148, 163, 184, 0.2)',
            }}
          >
            <h3 style={{ color: '#f1f5f9', fontSize: 18, marginBottom: 20 }}>
              Chat interface mock
            </h3>

            {/* User message */}
            <div
              style={{
                opacity: chatQuestionOpacity,
                marginBottom: 16,
                padding: 14,
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                borderRadius: 12,
                borderLeft: '4px solid #3b82f6',
              }}
            >
              <p style={{ color: '#93c5fd', fontSize: 14, margin: 0 }}>
                Is this wire transfer suspicious?
              </p>
              <p style={{ color: '#64748b', fontSize: 11, margin: '6px 0 0' }}>
                $50,000 to ACME Corp, 2:00 AM
              </p>
            </div>

            {/* Assistant response */}
            <div
              style={{
                opacity: chatResponseOpacity,
                transform: `translateY(${chatResponseY}px)`,
                padding: 14,
                backgroundColor: 'rgba(30, 41, 59, 0.9)',
                borderRadius: 12,
                border: '1px solid rgba(148, 163, 184, 0.2)',
              }}
            >
              <p style={{ color: '#f1f5f9', fontSize: 14, margin: '0 0 8px' }}>
                Decision: <strong style={{ color: '#eab308' }}>manual_review</strong>
              </p>
              <p style={{ color: '#94a3b8', fontSize: 12, margin: 0, lineHeight: 1.5 }}>
                Anomaly score: 0.847. SHAP: amount (+0.32), off_hours (+0.28). FINRA 4511
                reference.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tagline */}
      <div
        style={{
          position: 'absolute',
          bottom: 50,
          left: 50,
          right: 50,
          textAlign: 'center',
          opacity: taglineOpacity,
        }}
      >
        <p style={{ color: '#94a3b8', fontSize: 20, margin: 0, fontWeight: 600 }}>
          9 MCP tools. Connect Claude, Cursor, any AI agent.
        </p>
      </div>
    </AbsoluteFill>
  );
};
