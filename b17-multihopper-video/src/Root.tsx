import { Composition } from "remotion";
import { MultiHopperDemo } from "./MultiHopperDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MultiHopperDemo"
      component={MultiHopperDemo}
      durationInFrames={4560}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
