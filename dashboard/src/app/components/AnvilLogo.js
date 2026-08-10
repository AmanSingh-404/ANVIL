export default function AnvilLogo({ size = "nav" }) {
  const dimensions =
    size === "footer"
      ? { width: 28, height: 20 }
      : { width: 38, height: 28 };

  return (
    <svg
      viewBox="0 0 120 80"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        ...dimensions,
        display: "block",
        flexShrink: 0,
      }}
      aria-label="ANVIL"
    >
      {/* Main anvil silhouette */}
      <path
        fill="currentColor"
        d="M5 15 H112 L116 19 L113 27 L92 33 C82 36 77 41 75 48 L91 58 H99 L104 72 H69 C67 62 64 58 60 58 C56 58 53 62 51 72 H16 L21 58 H29 L45 48 C42 39 34 35 24 31 C15 27 9 21 5 15 Z"
      />

      {/* Horn cut */}
      <path
        d="M11 18 L45 18 L45 24 L25 22 Z"
        fill="var(--logo-bg, #f5f5f2)"
      />

      {/* Minimal AI mark */}
      <path
        d="M66 27 V38 L72 44 V53 M77 23 V34 L83 40"
        fill="none"
        stroke="var(--logo-bg, #f5f5f2)"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      <circle
        cx="66"
        cy="25"
        r="3"
        fill="var(--logo-bg, #f5f5f2)"
      />

      <circle
        cx="77"
        cy="21"
        r="3"
        fill="var(--logo-bg, #f5f5f2)"
      />
    </svg>
  );
}