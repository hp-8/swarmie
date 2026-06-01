import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Easing,
  spring,
  staticFile,
} from "remotion";
import { Audio } from "@remotion/media";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadJetBrains } from "@remotion/google-fonts/JetBrainsMono";

const { fontFamily: INTER } = loadInter();
const { fontFamily: FRAUNCES } = loadFraunces();
const { fontFamily: MONO } = loadJetBrains();

export const DEMO_FPS = 30;
export const DEMO_DURATION = 1350; // 45s
export const DEMO_WIDTH = 1920;
export const DEMO_HEIGHT = 1080;

// Hallmark Midnight+coral
const PAPER = "#07070f";
const PAPER_2 = "#0f0f1e";
const PAPER_3 = "#1a1a32";
const INK = "#f0f0fa";
const INK_2 = "rgba(240,240,250,0.82)";
const INK_3 = "rgba(240,240,250,0.50)";
const INK_4 = "rgba(240,240,250,0.30)";
const ACCENT = "#ff5470";
const ACCENT_BRIGHT = "#ff7a92";
const LIVE = "#3ddc97";
const AMBER = "#ffd166";
const BLUE = "#5cd5ff";
const PURPLE = "#c084fc";
const ORANGE = "#ffa07a";

const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);
const appleEase = Easing.bezier(0.25, 0.1, 0.25, 1);

function mulberry(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ─── Apple-style 3D Camera ───
// Wraps children in perspective + smooth transform

const Camera3D: React.FC<
  React.PropsWithChildren<{
    z?: number;
    rotateX?: number;
    rotateY?: number;
    x?: number;
    y?: number;
    scale?: number;
  }>
> = ({ children, z = 0, rotateX = 0, rotateY = 0, x = 0, y = 0, scale = 1 }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      perspective: 1200,
      perspectiveOrigin: "50% 50%",
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 0,
        transform: `translate3d(${x}px, ${y}px, ${z}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`,
        transformStyle: "preserve-3d",
        transformOrigin: "center center",
      }}
    >
      {children}
    </div>
  </div>
);

// ─── Shared ───

const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.035 }) => (
  <svg
    width="100%"
    height="100%"
    style={{
      position: "absolute",
      inset: 0,
      mixBlendMode: "screen",
      opacity,
      pointerEvents: "none",
    }}
  >
    <filter id="grain">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch" />
    </filter>
    <rect width="100%" height="100%" filter="url(#grain)" />
  </svg>
);

const Glow: React.FC<{
  x: number; y: number; size: number; color: string; opacity?: number;
}> = ({ x, y, size, color, opacity = 0.2 }) => (
  <div
    style={{
      position: "absolute",
      left: x - size / 2,
      top: y - size / 2,
      width: size,
      height: size,
      borderRadius: "50%",
      background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
      opacity,
      pointerEvents: "none",
    }}
  />
);

// ─── Scene 1: Hook (0–190) ───
// Camera: starts zoomed in tight, slowly pulls back to reveal text
// Parallax glow layers drift at different speeds

const Scene1Hook: React.FC = () => {
  const frame = useCurrentFrame();

  // Camera pulls back from z=200 to z=0, slight tilt
  const camZ = interpolate(frame, [0, 190], [200, 0], {
    extrapolateRight: "clamp",
    easing: appleEase,
  });
  const camRotX = interpolate(frame, [0, 190], [3, 0], {
    extrapolateRight: "clamp",
    easing: appleEase,
  });
  const camY = interpolate(frame, [0, 190], [30, 0], {
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  // Text reveals — staggered word groups
  const w1 = interpolate(frame, [15, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const w2 = interpolate(frame, [35, 65], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const w3 = interpolate(frame, [55, 85], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const w4 = interpolate(frame, [75, 105], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  // Accent line sweeps across
  const lineX = interpolate(frame, [90, 150], [-100, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: easeInOut,
  });

  // Parallax glows — different Z speeds
  const drift = frame / 120;

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />

      {/* Deep background glow — slow drift */}
      <Glow x={960 + Math.sin(drift) * 120} y={540 + Math.cos(drift * 0.7) * 80} size={1200} color={ACCENT} opacity={0.06} />
      {/* Mid glow — medium drift */}
      <Glow x={700 + Math.cos(drift * 1.3) * 80} y={400 + Math.sin(drift) * 60} size={600} color={BLUE} opacity={0.04} />
      {/* Near glow — fast drift */}
      <Glow x={1200 + Math.sin(drift * 1.8) * 50} y={650 + Math.cos(drift * 1.5) * 40} size={400} color={PURPLE} opacity={0.05} />

      <Camera3D z={camZ} rotateX={camRotX} y={camY}>
        <AbsoluteFill style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 8 }}>
          {/* Line 1 */}
          <div style={{
            fontFamily: FRAUNCES, fontStyle: "italic", fontWeight: 400,
            fontSize: 92, color: INK, letterSpacing: -2.5, lineHeight: 1.05, textAlign: "center",
          }}>
            <span style={{ opacity: w1, transform: `translateY(${(1 - w1) * 30}px)`, display: "inline-block" }}>What if </span>
            <span style={{ opacity: w2, transform: `translateY(${(1 - w2) * 30}px)`, display: "inline-block", color: ACCENT }}>500 users </span>
            <span style={{ opacity: w3, transform: `translateY(${(1 - w3) * 30}px)`, display: "inline-block" }}>could</span>
          </div>
          {/* Line 2 */}
          <div style={{
            fontFamily: FRAUNCES, fontStyle: "italic", fontWeight: 400,
            fontSize: 92, color: INK, letterSpacing: -2.5, lineHeight: 1.05, textAlign: "center",
          }}>
            <span style={{ opacity: w4, transform: `translateY(${(1 - w4) * 30}px)`, display: "inline-block" }}>
              roast your startup<span style={{ color: ACCENT }}>?</span>
            </span>
          </div>

          {/* Sweeping accent line */}
          <div style={{
            width: 500, height: 2, marginTop: 28, overflow: "hidden", position: "relative",
          }}>
            <div style={{
              position: "absolute",
              left: `${lineX}%`,
              top: 0,
              width: 200,
              height: 2,
              background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`,
            }} />
          </div>
        </AbsoluteFill>
      </Camera3D>
    </AbsoluteFill>
  );
};

// ─── Scene 2: Problem (190–530) ───
// Camera: dolly forward into the stats, then push past them

const Scene2Problem: React.FC = () => {
  const frame = useCurrentFrame();

  // Camera pushes forward slowly, slight rotation
  const camZ = interpolate(frame, [0, 340], [-50, 150], {
    extrapolateRight: "clamp",
    easing: appleEase,
  });
  const camRotY = interpolate(frame, [0, 340], [-1.5, 1.5], {
    extrapolateRight: "clamp",
    easing: appleEase,
  });

  const stats = [
    { text: "$10,000", sub: "on user interviews", delay: 20, color: INK },
    { text: "6 months", sub: "on wrong positioning", delay: 55, color: INK },
    { text: "3 objections", sub: "found in 60 seconds", delay: 95, color: ACCENT },
  ];

  // Bottom text
  const tagOp = interpolate(frame, [160, 195], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const tagY = interpolate(frame, [160, 195], [25, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  // Exit — everything scales up and fades as camera pushes through
  const exitOp = interpolate(frame, [290, 340], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exitScale = interpolate(frame, [290, 340], [1, 1.15], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });

  const drift = frame / 100;

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />
      <Glow x={960 + Math.cos(drift) * 100} y={540 + Math.sin(drift * 0.8) * 70} size={900} color={AMBER} opacity={0.05} />

      <Camera3D z={camZ} rotateY={camRotY}>
        <AbsoluteFill style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 60,
          opacity: exitOp, transform: `scale(${exitScale})`,
        }}>
          <div style={{ display: "flex", gap: 100, alignItems: "flex-start" }}>
            {stats.map((s, i) => {
              const enter = spring({ frame: Math.max(0, frame - s.delay), fps: 30, config: { damping: 18, mass: 0.7, stiffness: 100 } });
              const isLast = i === stats.length - 1;
              return (
                <div key={i} style={{
                  textAlign: "center",
                  transform: `scale(${enter}) translateY(${(1 - enter) * 40}px)`,
                  opacity: enter,
                }}>
                  <div style={{
                    fontFamily: FRAUNCES, fontStyle: "italic", fontWeight: 500,
                    fontSize: isLast ? 76 : 84, color: s.color, letterSpacing: -2, lineHeight: 1,
                  }}>
                    {s.text}
                  </div>
                  <div style={{
                    fontFamily: MONO, fontSize: 13, color: INK_3, letterSpacing: 2,
                    textTransform: "uppercase", marginTop: 14,
                  }}>
                    {s.sub}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{
            fontFamily: INTER, fontSize: 24, fontWeight: 400, color: INK_3,
            opacity: tagOp, transform: `translateY(${tagY}px)`, letterSpacing: 0.5,
          }}>
            The signal was always there. The access wasn't.
          </div>
        </AbsoluteFill>
      </Camera3D>
    </AbsoluteFill>
  );
};

// ─── Scene 3: Product (530–700) ───
// Camera: screen flies toward viewer from deep Z, settles center

const Scene3Product: React.FC = () => {
  const frame = useCurrentFrame();

  // Screen approaches from deep
  const screenZ = interpolate(frame, [0, 40], [-400, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });
  const screenRotX = interpolate(frame, [0, 40], [8, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });
  const screenOp = interpolate(frame, [0, 25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Slow dolly in during scene
  const camZ = interpolate(frame, [40, 170], [0, 80], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });

  // Typing
  const fullText = "AI inbox triage for B2B AEs hitting >50 cold replies/day. $49/seat.";
  const charCount = Math.min(fullText.length, Math.max(0, Math.floor((frame - 50) * 1.6)));
  const typedText = fullText.slice(0, charCount);
  const showCursor = frame > 50 && frame % 16 < 10;

  // Slider
  const sliderVal = interpolate(frame, [100, 130], [20, 500], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  // Button
  const btnOp = interpolate(frame, [135, 155], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />

      {/* Eyebrow floats above — parallax (doesn't move with camera) */}
      <div style={{
        position: "absolute", top: 50, left: 0, right: 0, textAlign: "center",
        fontFamily: MONO, fontSize: 13, letterSpacing: 4, textTransform: "uppercase", color: ACCENT,
        opacity: interpolate(frame, [5, 25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }}>
        three steps. sixty seconds.
      </div>

      <Camera3D z={camZ}>
        <div style={{
          position: "absolute", inset: 0,
          display: "flex", alignItems: "center", justifyContent: "center",
          perspective: 1200,
        }}>
          <div style={{
            width: 1300, height: 760,
            background: PAPER_2,
            border: `1px solid rgba(240,240,250,0.08)`,
            borderRadius: 18, overflow: "hidden",
            opacity: screenOp,
            transform: `translateZ(${screenZ}px) rotateX(${screenRotX}deg)`,
            boxShadow: `0 40px 120px rgba(0,0,0,0.7), 0 0 60px ${ACCENT}15`,
          }}>
            {/* Top bar */}
            <div style={{
              display: "flex", alignItems: "center", gap: 12,
              padding: "12px 20px", borderBottom: `1px solid rgba(240,240,250,0.06)`,
            }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: ACCENT, boxShadow: `0 0 12px ${ACCENT}` }} />
              <span style={{ fontFamily: MONO, fontSize: 11, letterSpacing: 3, color: INK_3 }}>SWARMIE</span>
              <span style={{ fontFamily: MONO, fontSize: 11, color: INK_4, marginLeft: 4 }}>/ new roast</span>
            </div>

            <div style={{ padding: "36px 50px", display: "flex", flexDirection: "column", gap: 26 }}>
              <div style={{
                fontFamily: FRAUNCES, fontStyle: "italic", fontWeight: 400,
                fontSize: 40, color: INK, letterSpacing: -1, lineHeight: 1.1,
              }}>
                What are we roasting?
              </div>

              {/* Textarea */}
              <div style={{
                background: PAPER_3,
                border: `1px solid ${charCount > 0 ? ACCENT : "rgba(240,240,250,0.08)"}`,
                borderRadius: 14, padding: "18px 22px", minHeight: 140,
                fontFamily: MONO, fontSize: 14, lineHeight: 1.6,
                color: charCount > 0 ? INK : INK_4,
              }}>
                {charCount > 0 ? (
                  <span>{typedText}{showCursor && <span style={{ color: ACCENT, fontWeight: 700 }}>|</span>}</span>
                ) : "PROBLEM: What pain are you solving?"}
              </div>

              {/* Swarm size */}
              <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                <span style={{ fontFamily: MONO, fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: INK_3 }}>swarm size</span>
                <div style={{ flex: 1, height: 4, background: PAPER_3, borderRadius: 99, overflow: "hidden" }}>
                  <div style={{ width: `${((sliderVal - 20) / 480) * 100}%`, height: "100%", background: ACCENT, borderRadius: 99 }} />
                </div>
                <span style={{ fontFamily: MONO, fontSize: 20, fontWeight: 700, color: ACCENT_BRIGHT }}>{Math.round(sliderVal)}</span>
              </div>

              {/* Run button */}
              <div style={{ opacity: btnOp, display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{
                  padding: "14px 28px", background: ACCENT, borderRadius: 10,
                  fontFamily: INTER, fontWeight: 700, fontSize: 15, color: PAPER,
                  boxShadow: frame > 155 ? `0 0 ${30 + Math.sin(frame / 6) * 10}px ${ACCENT}60` : "none",
                }}>
                  run the swarm →
                </div>
                <span style={{ fontFamily: MONO, fontSize: 12, color: INK_4, letterSpacing: 1 }}>500 agents · ~60s</span>
              </div>
            </div>
          </div>
        </div>
      </Camera3D>
    </AbsoluteFill>
  );
};

// ─── Scene 4: Brain (700–1020) ───
// Camera: orbits slowly around the brain graph, slight tilt shifts

const Scene4Brain: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const rng = mulberry(7);

  // Camera orbits — subtle Y rotation + gentle Z push
  const camRotY = interpolate(frame, [0, 320], [-4, 4], { extrapolateRight: "clamp", easing: appleEase });
  const camRotX = interpolate(frame, [0, 320], [2, -1], { extrapolateRight: "clamp", easing: appleEase });
  const camZ = interpolate(frame, [0, 160, 320], [-30, 50, 0], { extrapolateRight: "clamp", easing: appleEase });

  const ARCHETYPES = [
    { angle: 0, color: ACCENT, label: "skeptics" },
    { angle: Math.PI / 4, color: ORANGE, label: "indie devs" },
    { angle: Math.PI / 2, color: LIVE, label: "early adopters" },
    { angle: (3 * Math.PI) / 4, color: PURPLE, label: "lurkers" },
    { angle: Math.PI, color: ACCENT, label: "trolls" },
    { angle: (5 * Math.PI) / 4, color: AMBER, label: "PMs" },
    { angle: (3 * Math.PI) / 2, color: BLUE, label: "founders" },
    { angle: (7 * Math.PI) / 4, color: PURPLE, label: "VCs" },
  ];

  const neuronCount = 160;
  const neurons = Array.from({ length: neuronCount }, (_, i) => {
    const archIdx = i % ARCHETYPES.length;
    const phase = rng();
    const radius = 55 + rng() * 115;
    const flashAt = 30 + rng() * 250;
    return { archIdx, phase, radius, flashAt, i };
  });

  const rootPulse = 0.5 + 0.5 * Math.sin((frame / 25) * Math.PI);
  const rootR = 48 + rootPulse * 14;
  const rot = (frame / 500) * Math.PI * 2;

  // Count overlay
  const count = Math.min(500, Math.floor(interpolate(frame, [80, 260], [0, 500], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut })));

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />
      <Glow x={cx} y={cy} size={900} color={ACCENT} opacity={0.1 + rootPulse * 0.06} />

      {/* Eyebrow — fixed layer, no camera */}
      <div style={{
        position: "absolute", top: 48, left: 72,
        display: "flex", flexDirection: "column", gap: 6,
        fontFamily: MONO, letterSpacing: 2, fontSize: 13, textTransform: "uppercase", color: INK_3,
        opacity: interpolate(frame, [0, 25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }}>
        <span style={{ color: ACCENT, fontWeight: 700 }}>● live</span>
        <span>swarmie · inside the brain</span>
      </div>

      <Camera3D z={camZ} rotateX={camRotX} rotateY={camRotY}>
        <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
          <defs>
            <radialGradient id="rg" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={ACCENT} stopOpacity="0.8" />
              <stop offset="60%" stopColor={ACCENT} stopOpacity="0.1" />
              <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
            </radialGradient>
          </defs>

          <circle cx={cx} cy={cy} r={rootR * 3} fill="url(#rg)" opacity={0.5} />

          {ARCHETYPES.map((a, i) => {
            const archEnter = interpolate(frame, [i * 6, i * 6 + 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
            const ax = cx + Math.cos(a.angle + rot) * 290 * archEnter;
            const ay = cy + Math.sin(a.angle + rot) * 290 * archEnter;
            return (
              <line key={`s-${i}`} x1={cx} y1={cy} x2={ax} y2={ay} stroke={INK} strokeOpacity={0.06 + rootPulse * 0.03} strokeWidth={1} />
            );
          })}

          {neurons.map((n) => {
            const arch = ARCHETYPES[n.archIdx];
            const archEnter = interpolate(frame, [n.archIdx * 6, n.archIdx * 6 + 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
            const ax = cx + Math.cos(arch.angle + rot) * 290 * archEnter;
            const ay = cy + Math.sin(arch.angle + rot) * 290 * archEnter;
            const orbitAngle = n.phase * Math.PI * 2 + rot * 1.5;
            const nx = ax + Math.cos(orbitAngle) * n.radius;
            const ny = ay + Math.sin(orbitAngle) * n.radius;

            const appearAt = 25 + (n.i / neuronCount) * 80;
            if (frame < appearAt) return null;
            const neuronEnter = interpolate(frame, [appearAt, appearAt + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

            const flashDist = Math.abs(frame - n.flashAt);
            const flash = interpolate(flashDist, [0, 15], [1, 0], { extrapolateRight: "clamp" });
            const color = flash > 0.3 ? AMBER : arch.color;
            const r = (2.5 + flash * 4) * neuronEnter;

            return (
              <g key={`n-${n.i}`}>
                <line x1={ax} y1={ay} x2={nx} y2={ny} stroke={color} strokeOpacity={flash > 0.3 ? 0.4 : 0.06} strokeWidth={0.6} />
                {flash > 0.1 && <circle cx={nx} cy={ny} r={r * 3} fill={AMBER} opacity={flash * 0.4} />}
                <circle cx={nx} cy={ny} r={r} fill={color} opacity={0.8} />
              </g>
            );
          })}

          {ARCHETYPES.map((a, i) => {
            const archEnter = interpolate(frame, [i * 6, i * 6 + 30], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
            const ax = cx + Math.cos(a.angle + rot) * 290 * archEnter;
            const ay = cy + Math.sin(a.angle + rot) * 290 * archEnter;
            return (
              <g key={`a-${i}`}>
                <circle cx={ax} cy={ay} r={16} fill={a.color} opacity={0.15 * archEnter} />
                <circle cx={ax} cy={ay} r={8} fill={a.color} opacity={archEnter} />
                <text x={ax} y={ay + 28} textAnchor="middle" fill={INK_3} fontSize={11} fontFamily="ui-monospace, monospace" letterSpacing={1.5}
                  opacity={interpolate(frame, [60, 90], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
                  {a.label.toUpperCase()}
                </text>
              </g>
            );
          })}

          <circle cx={cx} cy={cy} r={rootR} fill={INK} />
          <text x={cx} y={cy + 5} textAnchor="middle" fill={PAPER} fontSize={14} fontWeight={700} fontFamily="ui-monospace, monospace" letterSpacing={2}>PITCH</text>
          <circle cx={cx} cy={cy} r={rootR + 22 + rootPulse * 12} fill="none" stroke={ACCENT} strokeOpacity={0.3} strokeWidth={1} />
        </svg>
      </Camera3D>

      {/* Count — fixed layer, parallax offset */}
      <div style={{
        position: "absolute", bottom: 56, right: 72, textAlign: "right",
        opacity: interpolate(frame, [90, 120], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }}>
        <div style={{ fontFamily: FRAUNCES, fontStyle: "italic", fontSize: 68, fontWeight: 400, color: ACCENT_BRIGHT, lineHeight: 1 }}>{count}</div>
        <div style={{ fontFamily: MONO, fontSize: 12, color: INK_3, letterSpacing: 2, textTransform: "uppercase", marginTop: 6 }}>personas activated</div>
      </div>
    </AbsoluteFill>
  );
};

// ─── Scene 5: Dashboard (1020–1220) ───
// Camera: top-down tilt that levels out, panels rise from below

const Scene5Dashboard: React.FC = () => {
  const frame = useCurrentFrame();

  // Camera starts tilted forward (looking down), levels out
  const camRotX = interpolate(frame, [0, 60], [12, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });
  const camZ = interpolate(frame, [0, 60, 200], [-100, 0, 40], { extrapolateRight: "clamp", easing: appleEase });
  const camY = interpolate(frame, [0, 60], [50, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });

  const eyebrow: React.CSSProperties = { fontFamily: MONO, fontSize: 10, letterSpacing: 2, textTransform: "uppercase", color: INK_3 };

  const pmfScore = interpolate(frame, [30, 100], [0, 7.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });

  const objs = [
    { label: "price too high", v: 0.74, c: ACCENT },
    { label: "wrong ICP", v: 0.52, c: ORANGE },
    { label: "no moat", v: 0.41, c: AMBER },
    { label: "trust deficit", v: 0.28, c: PURPLE },
  ];

  const rxCount = Math.floor(interpolate(frame, [15, 90], [0, 247], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut }));

  // Panel enter: spring from below
  const panelEnter = (delay: number) => {
    const s = spring({ frame: Math.max(0, frame - delay), fps: 30, config: { damping: 16, mass: 0.7, stiffness: 90 } });
    return {
      opacity: s,
      transform: `translateY(${(1 - s) * 60}px)`,
    };
  };

  const panelBase: React.CSSProperties = {
    background: PAPER_2,
    border: `1px solid rgba(240,240,250,0.08)`,
    borderRadius: 14,
    padding: 20,
    display: "flex",
    flexDirection: "column",
    gap: 10,
  };

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />

      <div style={{
        position: "absolute", top: 36, left: 0, right: 0, textAlign: "center",
        fontFamily: MONO, fontSize: 12, letterSpacing: 4, textTransform: "uppercase", color: ACCENT,
        opacity: interpolate(frame, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      }}>
        your PMF scorecard
      </div>

      <Camera3D z={camZ} rotateX={camRotX} y={camY}>
        <div style={{
          position: "absolute", top: 80, left: 70, right: 70, bottom: 50,
          display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gridTemplateRows: "1fr 1fr", gap: 14,
        }}>
          {/* PMF */}
          <div style={{ ...panelBase, gridRow: "1 / 3", ...panelEnter(5) }}>
            <span style={eyebrow}>pmf score · /10</span>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
              <span style={{ fontFamily: FRAUNCES, fontStyle: "italic", fontSize: 150, fontWeight: 400, color: ACCENT_BRIGHT, lineHeight: 1, letterSpacing: -6 }}>
                {pmfScore.toFixed(1)}
              </span>
              <span style={{ fontFamily: INTER, fontSize: 17, color: INK_3, marginTop: 8 }}>positive lean</span>
              <div style={{ display: "flex", gap: 3, marginTop: 12, width: "80%" }}>
                {Array.from({ length: 10 }).map((_, i) => (
                  <div key={i} style={{ flex: 1, height: 5, borderRadius: 3, background: i < Math.floor(pmfScore) ? ACCENT : `${INK}15` }} />
                ))}
              </div>
            </div>
          </div>

          {/* Objections */}
          <div style={{ ...panelBase, ...panelEnter(15) }}>
            <span style={eyebrow}>top objections</span>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {objs.map((o, i) => {
                const grow = interpolate(frame, [30 + i * 8, 65 + i * 8], [0, o.v], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
                return (
                  <div key={i}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, fontWeight: 600, fontFamily: INTER, color: INK_2 }}>
                      <span>{o.label}</span>
                      <span style={{ fontFamily: MONO, color: o.c }}>{Math.round(grow * 100)}%</span>
                    </div>
                    <div style={{ height: 5, background: `${INK}10`, borderRadius: 99, overflow: "hidden", marginTop: 3 }}>
                      <div style={{ width: `${grow * 100}%`, height: "100%", background: o.c, borderRadius: 99 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Sentiment */}
          <div style={{ ...panelBase, ...panelEnter(25) }}>
            <span style={eyebrow}>sentiment split</span>
            <div style={{ display: "flex", height: 38, borderRadius: 8, overflow: "hidden", marginTop: 8 }}>
              {[
                { label: "38%", color: LIVE, flex: 38 },
                { label: "35%", color: AMBER, flex: 35 },
                { label: "27%", color: ACCENT, flex: 27 },
              ].map((seg, i) => {
                const grow = interpolate(frame, [35, 70], [0, seg.flex], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
                return (
                  <div key={i} style={{ flex: grow, background: seg.color, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: MONO, fontSize: 12, fontWeight: 700, color: i === 1 ? PAPER : "white" }}>
                    {grow > 8 ? seg.label : ""}
                  </div>
                );
              })}
            </div>
            <div style={{ display: "flex", gap: 14, marginTop: 6 }}>
              {[{ l: "positive", c: LIVE }, { l: "neutral", c: AMBER }, { l: "negative", c: ACCENT }].map((x, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: x.c }} />
                  <span style={{ fontFamily: MONO, fontSize: 10, color: INK_3, letterSpacing: 1 }}>{x.l}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reactions */}
          <div style={{ ...panelBase, ...panelEnter(35) }}>
            <span style={eyebrow}>reactions</span>
            <span style={{ fontFamily: FRAUNCES, fontStyle: "italic", fontSize: 68, fontWeight: 400, color: BLUE, lineHeight: 1 }}>{rxCount}</span>
            <span style={{ fontFamily: MONO, fontSize: 11, color: INK_4 }}>in 58 seconds</span>
          </div>

          {/* Cost */}
          <div style={{ ...panelBase, ...panelEnter(45) }}>
            <span style={eyebrow}>total cost</span>
            <span style={{ fontFamily: FRAUNCES, fontStyle: "italic", fontSize: 68, fontWeight: 400, color: LIVE, lineHeight: 1 }}>
              ${interpolate(frame, [45, 90], [0, 0.38], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut }).toFixed(2)}
            </span>
            <span style={{ fontFamily: MONO, fontSize: 11, color: INK_4 }}>500 agents · real LLM run</span>
          </div>
        </div>
      </Camera3D>
    </AbsoluteFill>
  );
};

// ─── Scene 6: Close (1220–1350) ───
// Camera: smooth zoom into logo from far, settles with gentle float

const Scene6Close: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const rng = mulberry(42);

  // Camera zooms in from far to settle
  const camZ = interpolate(frame, [0, 60], [-200, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });
  const camRotX = interpolate(frame, [0, 60], [-3, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: appleEase });

  // Particles
  const particleCount = 80;
  const particles = Array.from({ length: particleCount }, (_, i) => {
    const ang = rng() * Math.PI * 2;
    const r = 300 + rng() * 500;
    const sx = cx + Math.cos(ang) * r;
    const sy = cy + Math.sin(ang) * r;
    const colors = [ACCENT, LIVE, BLUE, AMBER, PURPLE];
    return { sx, sy, color: colors[i % colors.length], delay: i * 0.3, i };
  });

  const logoEnter = spring({ frame: Math.max(0, frame - 20), fps: 30, config: { damping: 18, mass: 0.8, stiffness: 80 } });
  const tagOp = interpolate(frame, [55, 80], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const tagY = interpolate(frame, [55, 80], [15, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const urlOp = interpolate(frame, [75, 100], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const ambient = Math.sin((frame / 30) * Math.PI * 2) * 2.5;

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <Grain />
      <Glow x={cx} y={cy} size={1000} color={ACCENT} opacity={0.08 + logoEnter * 0.1} />

      <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
        {particles.map((p) => {
          const local = frame - p.delay;
          const t = Math.min(1, Math.max(0, local / 40));
          const ease = easeInOut(t);
          const x = p.sx + (cx - p.sx) * ease;
          const y = p.sy + (cy - p.sy) * ease;
          const op = interpolate(t, [0, 0.1, 0.8, 1], [0, 0.7, 0.7, 0]);
          return <circle key={p.i} cx={x} cy={y} r={4 - t * 2.5} fill={p.color} opacity={op} />;
        })}
      </svg>

      <Camera3D z={camZ} rotateX={camRotX}>
        <AbsoluteFill style={{
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
          gap: 20, transform: `translateY(${ambient}px)`,
        }}>
          <div style={{
            transform: `scale(${logoEnter})`, opacity: logoEnter,
            display: "flex", alignItems: "center", gap: 18,
          }}>
            <svg width={85} height={85} viewBox="0 0 120 120">
              <circle cx={60} cy={60} r={36} fill={ACCENT} />
              <circle cx={28} cy={42} r={10} fill={BLUE} />
              <circle cx={92} cy={42} r={10} fill={LIVE} />
              <circle cx={28} cy={82} r={10} fill={AMBER} />
              <circle cx={92} cy={82} r={10} fill={PURPLE} />
              <line x1={60} y1={60} x2={28} y2={42} stroke={INK} strokeWidth={1.5} strokeOpacity={0.4} />
              <line x1={60} y1={60} x2={92} y2={42} stroke={INK} strokeWidth={1.5} strokeOpacity={0.4} />
              <line x1={60} y1={60} x2={28} y2={82} stroke={INK} strokeWidth={1.5} strokeOpacity={0.4} />
              <line x1={60} y1={60} x2={92} y2={82} stroke={INK} strokeWidth={1.5} strokeOpacity={0.4} />
            </svg>
            <span style={{ fontFamily: INTER, fontWeight: 800, fontSize: 96, color: INK, letterSpacing: -3 }}>
              Swarmie<span style={{ color: ACCENT }}>.</span>
            </span>
          </div>

          <div style={{
            fontFamily: INTER, fontSize: 30, fontWeight: 400, color: INK_2,
            opacity: tagOp, transform: `translateY(${tagY}px)`, textAlign: "center",
          }}>
            Roast before you launch<span style={{ color: ACCENT }}>.</span>
          </div>

          <div style={{
            fontFamily: MONO, fontSize: 14, color: INK_4, letterSpacing: 4, textTransform: "uppercase",
            opacity: urlOp, marginTop: 6,
          }}>
            swarmie.dev
          </div>
        </AbsoluteFill>
      </Camera3D>
    </AbsoluteFill>
  );
};

// ─── Fade wrapper ───
const FadeIn: React.FC<React.PropsWithChildren<{ frames?: number }>> = ({ children, frames = 12 }) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, frames], [0, 1], { extrapolateRight: "clamp" });
  return <div style={{ opacity: op, width: "100%", height: "100%" }}>{children}</div>;
};

// ─── Master ───
// Voiceover durations: 147f, 299f, 113f, 295f, 288f, 84f
// Voice starts 15f after scene start for visual lead-in

export const AppleDemo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: PAPER }}>
      {/* Music — fades in, ducks under voice at 0.25, fades out at end */}
      <Audio
        src={staticFile("demo-music.mp3")}
        volume={(f) =>
          interpolate(f, [0, 45, 1280, 1350], [0, 0.25, 0.25, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          })
        }
      />

      {/* Voiceover — 15f after each scene start */}
      <Sequence from={15} layout="none">
        <Audio src={staticFile("voiceover/scene1-hook.wav")} volume={0.95} />
      </Sequence>
      <Sequence from={205} layout="none">
        <Audio src={staticFile("voiceover/scene2-problem.wav")} volume={0.95} />
      </Sequence>
      <Sequence from={545} layout="none">
        <Audio src={staticFile("voiceover/scene3-product.wav")} volume={0.95} />
      </Sequence>
      <Sequence from={715} layout="none">
        <Audio src={staticFile("voiceover/scene4-brain.wav")} volume={0.95} />
      </Sequence>
      <Sequence from={1035} layout="none">
        <Audio src={staticFile("voiceover/scene5-dashboard.wav")} volume={0.95} />
      </Sequence>
      <Sequence from={1235} layout="none">
        <Audio src={staticFile("voiceover/scene6-close.wav")} volume={0.95} />
      </Sequence>

      {/* Scenes */}
      <Sequence from={0} durationInFrames={200} layout="none">
        <Scene1Hook />
      </Sequence>
      <Sequence from={190} durationInFrames={350} layout="none">
        <FadeIn><Scene2Problem /></FadeIn>
      </Sequence>
      <Sequence from={530} durationInFrames={180} layout="none">
        <FadeIn><Scene3Product /></FadeIn>
      </Sequence>
      <Sequence from={700} durationInFrames={330} layout="none">
        <FadeIn><Scene4Brain /></FadeIn>
      </Sequence>
      <Sequence from={1020} durationInFrames={210} layout="none">
        <FadeIn><Scene5Dashboard /></FadeIn>
      </Sequence>
      <Sequence from={1220} durationInFrames={130} layout="none">
        <FadeIn><Scene6Close /></FadeIn>
      </Sequence>
    </AbsoluteFill>
  );
};
