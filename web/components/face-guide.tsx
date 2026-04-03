"use client";

/**
 * FaceGuide — SVG overlay showing a head/shoulders silhouette outline
 * so the user can align their face within the correct zone.
 *
 * Positioned absolutely inside the webcam container.
 * Adapts to the container size.
 */

export default function FaceGuide() {
  return (
    <svg
      viewBox="0 0 400 400"
      className="absolute inset-0 w-full h-full pointer-events-none"
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Dim overlay with transparent cutout */}
      <defs>
        <mask id="face-cutout">
          <rect width="400" height="400" fill="white" />
          {/* Head oval */}
          <ellipse cx="200" cy="145" rx="72" ry="92" fill="black" />
          {/* Neck */}
          <rect x="175" y="225" width="50" height="30" rx="4" fill="black" />
          {/* Shoulders */}
          <ellipse cx="200" cy="290" rx="110" ry="40" fill="black" />
        </mask>
      </defs>

      {/* Semi-transparent overlay outside the guide */}
      <rect
        width="400"
        height="400"
        fill="rgba(0, 0, 0, 0.45)"
        mask="url(#face-cutout)"
      />

      {/* Glowing outline — Head */}
      <ellipse
        cx="200"
        cy="145"
        rx="72"
        ry="92"
        fill="none"
        stroke="rgba(0, 212, 255, 0.8)"
        strokeWidth="2"
        strokeDasharray="8 4"
      >
        <animate
          attributeName="stroke-opacity"
          values="0.5;1;0.5"
          dur="2s"
          repeatCount="indefinite"
        />
      </ellipse>

      {/* Outline — Shoulders */}
      <ellipse
        cx="200"
        cy="290"
        rx="110"
        ry="40"
        fill="none"
        stroke="rgba(0, 212, 255, 0.4)"
        strokeWidth="1.5"
        strokeDasharray="6 4"
      />

      {/* Neck connector */}
      <line
        x1="175"
        y1="230"
        x2="175"
        y2="260"
        stroke="rgba(0, 212, 255, 0.3)"
        strokeWidth="1"
        strokeDasharray="4 3"
      />
      <line
        x1="225"
        y1="230"
        x2="225"
        y2="260"
        stroke="rgba(0, 212, 255, 0.3)"
        strokeWidth="1"
        strokeDasharray="4 3"
      />

      {/* Center crosshair — subtle */}
      <line
        x1="195"
        y1="145"
        x2="205"
        y2="145"
        stroke="rgba(0, 212, 255, 0.6)"
        strokeWidth="1"
      />
      <line
        x1="200"
        y1="140"
        x2="200"
        y2="150"
        stroke="rgba(0, 212, 255, 0.6)"
        strokeWidth="1"
      />

      {/* Eye-line guide */}
      <line
        x1="155"
        y1="130"
        x2="245"
        y2="130"
        stroke="rgba(0, 212, 255, 0.25)"
        strokeWidth="0.8"
        strokeDasharray="3 5"
      />

      {/* Instruction text */}
      <text
        x="200"
        y="370"
        textAnchor="middle"
        fill="rgba(0, 212, 255, 0.9)"
        fontSize="13"
        fontFamily="Inter, system-ui, sans-serif"
        fontWeight="600"
      >
        Align your face within the outline
      </text>
    </svg>
  );
}
