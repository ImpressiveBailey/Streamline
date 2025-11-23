import React from "react";
import { Box, Divider, Typography } from "@mui/material";
import ManifestFieldRenderer from "./ManifestFieldRenderer";

/**
 * Renders ALL fields from a page result’s manifest.
 * Props:
 * - manifest: { fields: [...] }
 * - data: result.data
 * - onCopy(content, okMsg?)
 * - onExpand(title, html)
 * - title?: optional heading string shown above fields
 */
export default function ManifestFieldsPanel({
  manifest,
  data,
  onCopy,
  onExpand,
  title,
}) {
  const fields = Array.isArray(manifest?.fields) ? manifest.fields : [];

  return (
    <Box>
      {title ? (
        <Typography variant="overline" color="text.secondary" sx={{ display: "block", mb: 1 }}>
          {title}
        </Typography>
      ) : null}
      {fields.map((f, idx) => (
        <React.Fragment key={`${f.path || f.label || idx}`}>
          <ManifestFieldRenderer field={f} data={data} onCopy={onCopy} onExpand={onExpand} />
          {idx !== fields.length - 1 ? <Divider sx={{ my: 1.5 }} /> : null}
        </React.Fragment>
      ))}
    </Box>
  );
}
