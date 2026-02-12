import { Composition } from 'remotion';
import { DemoVideo } from './DemoVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DemoVideo"
        component={DemoVideo}
        durationInFrames={1860} // 62 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
