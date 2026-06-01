import { Composition } from "remotion";
import { Promo, PROMO_DURATION, PROMO_FPS, PROMO_HEIGHT, PROMO_WIDTH } from "./Promo";
import { AppleDemo, DEMO_DURATION, DEMO_FPS, DEMO_WIDTH, DEMO_HEIGHT } from "./AppleDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AppleDemo"
        component={AppleDemo}
        durationInFrames={DEMO_DURATION}
        fps={DEMO_FPS}
        width={DEMO_WIDTH}
        height={DEMO_HEIGHT}
      />
      <Composition
        id="Promo"
        component={Promo}
        durationInFrames={PROMO_DURATION}
        fps={PROMO_FPS}
        width={PROMO_WIDTH}
        height={PROMO_HEIGHT}
      />
    </>
  );
};
