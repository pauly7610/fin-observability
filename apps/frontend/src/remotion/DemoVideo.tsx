import { AbsoluteFill, Sequence } from 'remotion';
import { IntroScene } from './scenes/IntroScene';
import { ComplianceAgentScene } from './scenes/ComplianceAgentScene';
import { ExplainabilityScene } from './scenes/ExplainabilityScene';
import { AnomalyDetectionScene } from './scenes/AnomalyDetectionScene';
import { MCPScene } from './scenes/MCPScene';
import { AgenticWorkflowScene } from './scenes/AgenticWorkflowScene';
import { AutoRetrainingScene } from './scenes/AutoRetrainingScene';
import { GrafanaScene } from './scenes/GrafanaScene';
import { WebhookScene } from './scenes/WebhookScene';
import { OutroScene } from './scenes/OutroScene';

export const DemoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#0f172a' }}>
      {/* 1. Intro - 5s */}
      <Sequence from={0} durationInFrames={150}>
        <IntroScene />
      </Sequence>

      {/* 2. Compliance Agent - 8s */}
      <Sequence from={150} durationInFrames={240}>
        <ComplianceAgentScene />
      </Sequence>

      {/* 3. Explainability - 8s */}
      <Sequence from={390} durationInFrames={240}>
        <ExplainabilityScene />
      </Sequence>

      {/* 4. Anomaly Detection - 6s */}
      <Sequence from={630} durationInFrames={180}>
        <AnomalyDetectionScene />
      </Sequence>

      {/* 5. MCP - 6s */}
      <Sequence from={810} durationInFrames={180}>
        <MCPScene />
      </Sequence>

      {/* 6. Agentic Workflow (Human-in-the-Loop) - 6s */}
      <Sequence from={990} durationInFrames={180}>
        <AgenticWorkflowScene />
      </Sequence>

      {/* 7. Auto-Retraining - 7s */}
      <Sequence from={1170} durationInFrames={210}>
        <AutoRetrainingScene />
      </Sequence>

      {/* 8. Grafana - 6s */}
      <Sequence from={1380} durationInFrames={180}>
        <GrafanaScene />
      </Sequence>

      {/* 9. Webhook - 5s */}
      <Sequence from={1560} durationInFrames={150}>
        <WebhookScene />
      </Sequence>

      {/* 10. Outro - 5s */}
      <Sequence from={1710} durationInFrames={150}>
        <OutroScene />
      </Sequence>
    </AbsoluteFill>
  );
};
