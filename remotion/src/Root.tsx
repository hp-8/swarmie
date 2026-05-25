import { Composition } from "remotion";
import { Promo, PROMO_DURATION, PROMO_FPS, PROMO_HEIGHT, PROMO_WIDTH } from "./Promo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Promo"
      component={Promo}
      durationInFrames={PROMO_DURATION}
      fps={PROMO_FPS}
      width={PROMO_WIDTH}
      height={PROMO_HEIGHT}
    />
  );
};
