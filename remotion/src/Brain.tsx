import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

// Seamless 8s loop — all motion driven by sin/cos of (frame / duration) so
// frame 0 state == frame duration state.
export const BRAIN_FPS = 30;
export const BRAIN_DURATION = 240; // 8s
export const BRAIN_WIDTH = 1920;
export const BRAIN_HEIGHT = 1080;

// Hallmark Midnight+coral palette
const PAPER_DARK = "#07070f";
const PAPER_MID = "#14142a";
const INK = "#f0f0fa";
const INK_SOFT = "rgba(240, 240, 250, 0.55)";
const ACCENT = "#ff5470";     // coral
const POS = "#3ddc97";        // teal-green
const NEG = "#ff5470";        // coral
const THINKING = "#ffd166";   // amber

// Deterministic PRNG so positions are stable across frames
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

type Archetype = { id: number; angle: number; color: string; label: string };
type Neuron = {
  id: number;
  archetype: number;
  phase: number;      // 0..1 around its archetype
  radius: number;     // distance from archetype
  baseSent: number;   // -1..1 final sentiment
  flashOffset: number; // 0..1 when this neuron flashes
};

const ARCHETYPES: Archetype[] = [
  { id: 0, angle: 0,            color: ACCENT, label: "skeptics" },
  { id: 1, angle: Math.PI / 4,  color: "#ffa07a", label: "indie devs" },
  { id: 2, angle: Math.PI / 2,  color: POS,     label: "early adopters" },
  { id: 3, angle: 3 * Math.PI / 4, color: "#9b8cff", label: "lurkers" },
  { id: 4, angle: Math.PI,      color: NEG,     label: "trolls" },
  { id: 5, angle: 5 * Math.PI / 4, color: "#ffd166", label: "PMs" },
  { id: 6, angle: 3 * Math.PI / 2, color: "#5cd5ff", label: "founders" },
  { id: 7, angle: 7 * Math.PI / 4, color: "#c084fc", label: "VCs" },
];

const NEURON_COUNT = 240;

const NEURONS: Neuron[] = (() => {
  const rng = mulberry32(7);
  const out: Neuron[] = [];
  for (let i = 0; i < NEURON_COUNT; i++) {
    const archetype = i % ARCHETYPES.length;
    const phase = rng();
    const radius = 70 + rng() * 130;
    const baseSent = (rng() - 0.4) * 1.6; // skew slightly positive
    const flashOffset = rng();
    out.push({ id: i, archetype, phase, radius, baseSent, flashOffset });
  }
  return out;
})();

function tau(frame: number, duration: number) {
  return (frame / duration) * Math.PI * 2;
}

export const Brain: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const cx = width / 2;
  const cy = height / 2;
  const t = tau(frame, durationInFrames); // 0..2π over the loop

  // Root pulse
  const rootPulse = 0.5 + 0.5 * Math.sin(t * 2); // 2 pulses per loop
  const rootRadius = 56 + rootPulse * 14;
  const rootGlow = 40 + rootPulse * 40;

  // Archetype ring slow rotation (one full turn per loop)
  const archRingRotation = t;

  return (
    <AbsoluteFill style={{ background: PAPER_DARK, fontFamily: "ui-sans-serif, system-ui" }}>
      {/* Radial atmosphere */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse at center, ${PAPER_MID} 0%, ${PAPER_DARK} 70%)`,
        }}
      />

      {/* Subtle drifting noise band (parallax) — done with two soft radial highlights */}
      <AbsoluteFill style={{ opacity: 0.35 }}>
        <div
          style={{
            position: "absolute",
            left: cx + Math.cos(t) * 220 - 300,
            top: cy + Math.sin(t) * 180 - 300,
            width: 600,
            height: 600,
            background: `radial-gradient(circle, ${ACCENT}22 0%, transparent 60%)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: cx + Math.cos(t + Math.PI) * 260 - 320,
            top: cy + Math.sin(t + Math.PI) * 200 - 320,
            width: 640,
            height: 640,
            background: `radial-gradient(circle, ${POS}1a 0%, transparent 60%)`,
          }}
        />
      </AbsoluteFill>

      {/* SVG world */}
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: "absolute", inset: 0 }}
      >
        <defs>
          <radialGradient id="rootGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={ACCENT} stopOpacity="0.9" />
            <stop offset="60%" stopColor={ACCENT} stopOpacity="0.15" />
            <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="flashGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={THINKING} stopOpacity="1" />
            <stop offset="60%" stopColor={THINKING} stopOpacity="0.2" />
            <stop offset="100%" stopColor={THINKING} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Root glow halo */}
        <circle cx={cx} cy={cy} r={rootRadius * 3.2} fill="url(#rootGlow)" opacity={0.6 + rootPulse * 0.3} />

        {/* Spokes root → archetypes */}
        {ARCHETYPES.map((a) => {
          const ax = cx + Math.cos(a.angle + archRingRotation) * 340;
          const ay = cy + Math.sin(a.angle + archRingRotation) * 340;
          return (
            <line
              key={`spoke-${a.id}`}
              x1={cx}
              y1={cy}
              x2={ax}
              y2={ay}
              stroke={INK}
              strokeOpacity={0.08 + rootPulse * 0.05}
              strokeWidth={1}
            />
          );
        })}

        {/* Neurons — synapses + dots */}
        {NEURONS.map((n) => {
          const arch = ARCHETYPES[n.archetype];
          const ax = cx + Math.cos(arch.angle + archRingRotation) * 340;
          const ay = cy + Math.sin(arch.angle + archRingRotation) * 340;
          // Neuron orbits its archetype, full orbit per loop
          const orbitAngle = n.phase * Math.PI * 2 + t;
          const nx = ax + Math.cos(orbitAngle) * n.radius;
          const ny = ay + Math.sin(orbitAngle) * n.radius;

          // Flash window: each neuron has a 20-frame flash centered on its offset
          const flashCenter = n.flashOffset * durationInFrames;
          let flashDist = Math.abs(frame - flashCenter);
          flashDist = Math.min(flashDist, durationInFrames - flashDist); // wrap-around
          const flashIntensity = interpolate(flashDist, [0, 18], [1, 0], {
            extrapolateRight: "clamp",
          });

          // After flash, settle into sentiment color
          const sent = n.baseSent;
          const settleColor = sent > 0.15 ? POS : sent < -0.15 ? NEG : "#a0a0b8";
          const baseR = 2.6;
          const flashR = baseR + flashIntensity * 5;

          return (
            <g key={`n-${n.id}`}>
              {/* synapse from archetype */}
              <line
                x1={ax}
                y1={ay}
                x2={nx}
                y2={ny}
                stroke={flashIntensity > 0.2 ? THINKING : settleColor}
                strokeOpacity={flashIntensity > 0.2 ? 0.55 : 0.07}
                strokeWidth={0.7}
              />
              {/* flash halo */}
              {flashIntensity > 0.05 && (
                <circle
                  cx={nx}
                  cy={ny}
                  r={flashR * 3.2}
                  fill="url(#flashGlow)"
                  opacity={flashIntensity}
                />
              )}
              {/* the neuron */}
              <circle
                cx={nx}
                cy={ny}
                r={flashR}
                fill={flashIntensity > 0.2 ? THINKING : settleColor}
                opacity={0.85}
              />
            </g>
          );
        })}

        {/* Archetype core circles (on top of neurons) */}
        {ARCHETYPES.map((a) => {
          const ax = cx + Math.cos(a.angle + archRingRotation) * 340;
          const ay = cy + Math.sin(a.angle + archRingRotation) * 340;
          return (
            <g key={`a-${a.id}`}>
              <circle cx={ax} cy={ay} r={22} fill={a.color} opacity={0.18} />
              <circle cx={ax} cy={ay} r={11} fill={a.color} stroke={INK} strokeOpacity={0.7} strokeWidth={1.4} />
              <text
                x={ax}
                y={ay + 36}
                textAnchor="middle"
                fill={INK_SOFT}
                fontSize={13}
                fontFamily="ui-monospace, SF Mono, Menlo, monospace"
                letterSpacing={1.4}
              >
                {a.label.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* Root node */}
        <circle cx={cx} cy={cy} r={rootRadius} fill={INK} />
        <text
          x={cx}
          y={cy + 5}
          textAnchor="middle"
          fill={PAPER_DARK}
          fontSize={16}
          fontWeight={700}
          fontFamily="ui-monospace, SF Mono, Menlo, monospace"
          letterSpacing={2}
        >
          PITCH
        </text>

        {/* Outer faint ring */}
        <circle
          cx={cx}
          cy={cy}
          r={rootRadius + 30 + rootPulse * 16}
          fill="none"
          stroke={ACCENT}
          strokeOpacity={0.35}
          strokeWidth={1}
        />
      </svg>

      {/* Live stats overlay */}
      <StatsOverlay t={t} />
    </AbsoluteFill>
  );
};

const StatsOverlay: React.FC<{ t: number }> = ({ t }) => {
  // Counters cycle but should land on similar values at frame 0 and frame end.
  const reacted = Math.floor(180 + 60 * (0.5 + 0.5 * Math.sin(t)));
  const thinking = Math.floor(8 + 12 * (0.5 + 0.5 * Math.sin(t * 3)));
  const silent = 500 - reacted - thinking;

  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        top: 56,
        display: "flex",
        flexDirection: "column",
        gap: 6,
        fontFamily: "ui-monospace, SF Mono, Menlo, monospace",
        color: INK_SOFT,
        letterSpacing: 2,
        fontSize: 13,
        textTransform: "uppercase",
      }}
    >
      <span style={{ color: ACCENT, fontWeight: 700 }}>● live</span>
      <span>swarmie · inside the brain</span>
    </div>
  );
};
