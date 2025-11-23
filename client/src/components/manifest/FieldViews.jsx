import React from "react";
import {
  Box, Typography, Stack, IconButton, Tooltip, List, ListItem, ListItemText,
} from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import { normalizeFaq } from "./manifestUtils";

// Simple HTML preview block shared by HTML/FAQ answers
export const HtmlPreview = ({ html }) => (
  <Box
    sx={{
      p: 2,
      border: (t) => `1px solid ${t.palette.divider}`,
      borderRadius: 1,
      overflowX: "auto",
      "& h1": { fontSize: "1.6rem", fontWeight: 700, mt: 2.5, mb: 1 },
      "& h2": { fontSize: "1.3rem", fontWeight: 700, mt: 2, mb: 1 },
      "& h3": { fontSize: "1.1rem", fontWeight: 600, mt: 1.5, mb: 0.75 },
      "& h4, & h5, & h6": { mt: 1.25, mb: 0.5, fontWeight: 600 },
      "& p": { lineHeight: 1.75, mb: 1.25 },
      "& ul, & ol": { pl: 3.5, mb: 1.25 },
      "& li": { mb: 0.5 },
      "& a": { textDecoration: "underline", wordBreak: "break-word" },
      "& img": { maxWidth: "100%", height: "auto", borderRadius: 1, my: 1.25 },
      "& blockquote": {
        borderLeft: (t) => `4px solid ${t.palette.divider}`,
        pl: 2,
        color: "text.secondary",
        fontStyle: "italic",
        my: 1.25,
      },
      "& code, & pre": {
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontSize: "0.95em",
        backgroundColor: (t) =>
          t.palette.mode === "dark" ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
      },
      "& pre": { p: 2, borderRadius: 1, overflowX: "auto" },
      "& table": { width: "100%", borderCollapse: "collapse", my: 1.25 },
      "& th, & td": {
        border: (t) => `1px solid ${t.palette.divider}`,
        p: 1,
        textAlign: "left",
        verticalAlign: "top",
      },
    }}
    dangerouslySetInnerHTML={{ __html: html || "" }}
  />
);

export const TextFieldView = ({ label, value, onCopy }) => (
  <Stack spacing={0.5} sx={{ mb: 2 }}>
    <Stack direction="row" alignItems="center" spacing={1}>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>{label}</Typography>
      <Tooltip title="Copy">
        <IconButton size="small" onClick={() => onCopy?.(value ?? "")}>
          <ContentCopyIcon fontSize="inherit" />
        </IconButton>
      </Tooltip>
    </Stack>
    <Typography variant="body2" color="text.secondary">{value || "—"}</Typography>
  </Stack>
);

export const HtmlFieldView = ({ label, html, onCopy, onExpand }) => (
  <Stack spacing={1} sx={{ mb: 2 }}>
    <Stack direction="row" alignItems="center" spacing={1}>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>{label}</Typography>
      <Tooltip title="Copy HTML">
        <IconButton size="small" onClick={() => onCopy?.(html || "", "HTML copied!")}>
          <ContentCopyIcon fontSize="inherit" />
        </IconButton>
      </Tooltip>
      <Tooltip title="Open large preview">
        <IconButton size="small" onClick={() => onExpand?.(label, html || "")}>
          <OpenInFullIcon fontSize="inherit" />
        </IconButton>
      </Tooltip>
    </Stack>
    <HtmlPreview html={html} />
  </Stack>
);

export const FaqFieldView = ({ label, value, mapping, onCopy, onExpand }) => {
  const faqs = normalizeFaq(value, mapping);
  return (
    <Stack spacing={1} sx={{ mb: 2 }}>
      <Stack direction="row" alignItems="center" spacing={1}>
        <Typography variant="body2" sx={{ fontWeight: 600 }}>{label}</Typography>
        {!!faqs.length && (
          <Tooltip title="Copy all (plain text)">
            <IconButton
              size="small"
              onClick={() =>
                onCopy?.(
                  faqs.map(f => `Q: ${f.question}\nA: ${f.answer}`).join("\n\n"),
                  "FAQs copied!"
                )
              }
            >
              <ContentCopyIcon fontSize="inherit" />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      {faqs.length ? (
        <List dense sx={{ pl: 0 }}>
          {faqs.map((f, i) => (
            <ListItem
              key={`faq-${i}`}
              alignItems="flex-start"
              sx={{ pl: 0 }}
              secondaryAction={
                <Tooltip title="Copy Q&A">
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={() => onCopy?.(`Q: ${f.question}\nA: ${f.answer}`, "FAQ copied!")}
                  >
                    <ContentCopyIcon fontSize="inherit" />
                  </IconButton>
                </Tooltip>
              }
            >
              <ListItemText
                primary={<Typography variant="body2" sx={{ fontWeight: 600 }}>{f.question || "—"}</Typography>}
                secondary={
                  // Answers can be HTML; render nicely
                  <HtmlPreview html={String(f.answer || "")} />
                }
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography variant="body2" color="text.secondary">—</Typography>
      )}
    </Stack>
  );
};

// Registry so you can extend types later without touching callers
export const DefaultTypeRegistry = {
  text: TextFieldView,
  html: HtmlFieldView,
  faq: FaqFieldView,
};
