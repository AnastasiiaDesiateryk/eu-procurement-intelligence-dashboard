import React from "react";

type Props = {
  /** URL дашборда Superset, без ?standalone=1 — мы добавим сами */
  src: string;
  height?: number;
};

const SupersetEmbed: React.FC<Props> = ({ src, height = 900 }) => {
  const url = `${src}${src.includes("?") ? "&" : "?"}standalone=1`;
  return (
    <div
      style={{
        borderRadius: 16,
        overflow: "hidden",
        boxShadow: "0 6px 24px rgba(0,0,0,0.15)",
      }}
    >
      <iframe
        src={url}
        width="100%"
        height={height}
        style={{ border: 0 }}
        referrerPolicy="no-referrer"
      />
    </div>
  );
};

export default SupersetEmbed;
