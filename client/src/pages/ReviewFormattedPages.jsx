// src/pages/ReviewFormattedDocument.jsx
import React, { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  Container,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  Link,
  List,
  ListItem,
  ListItemText,
  Paper,
  Snackbar,
  Stack,
  Typography,
} from "@mui/material";
import ManifestFieldsPanel from "../components/manifest/ManifestFieldsPanel";

function HtmlPreview({ html }) {
  return (
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
          borderLeft: (theme) => `4px solid ${theme.palette.divider}`,
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
}

export default function ReviewFormattedPages() {
  const { state } = useLocation();
  const navigate = useNavigate();

  // Pull from state or session cache
  const formatted = useMemo(() => {
    if (state && state.formatted) return state.formatted;
    try {
      const raw = sessionStorage.getItem("formattedDoc");
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }, [state]);

  // Support both shapes:
  // 1) results = { pages: [...], errors: [...] }
  // 2) legacy results = [...]
  const resultsObj = formatted?.results;
  const pages = Array.isArray(resultsObj?.pages)
    ? resultsObj.pages
    : Array.isArray(formatted?.results)
    ? formatted.results
    : [];

  const hasData = pages.length > 0;
  const clientId = formatted?.client_id || "";
  const globals = formatted?.globals || {};

  // UX bits
  const [snack, setSnack] = useState({ open: false, msg: "", severity: "success" });
  const [modal, setModal] = useState({ open: false, title: "", html: "" });

  const copyToClipboard = async (text, okMsg = "Copied!") => {
    try {
      await navigator.clipboard.writeText(text || "");
      setSnack({ open: true, msg: okMsg, severity: "success" });
    } catch (e) {
      setSnack({ open: true, msg: "Copy failed", severity: "error" });
    }
  };

  if (!hasData) {
    return (
      <Container maxWidth="lg" sx={{ py: 6 }}>
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>No formatted data available</Typography>
          <Stack direction="row" spacing={1}>
            <Button onClick={() => navigate("/")}>Go Home</Button>
            <Button onClick={() => navigate("/doc")}>Back to Breakdown</Button>
          </Stack>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 700 }}>
          Review Formatted Content {clientId ? `— ${clientId}` : ""}
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button onClick={() => navigate("/doc")}>Back</Button>
          <Button
            variant="contained"
            onClick={() => navigate("/upload", { state: { formatted } })}
          >
            Upload
          </Button>
        </Stack>
      </Stack>

      {/* Globals */}
      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="overline" color="text.secondary">Globals</Typography>
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={2} sx={{ mt: 1 }}>
          <Stack spacing={0.5} sx={{ minWidth: 220 }}>
            <Typography variant="subtitle2" color="text.secondary">Client Name</Typography>
            <Typography variant="body1">{globals?.clientName || "—"}</Typography>
          </Stack>
          <Divider flexItem orientation="vertical" />
          <Stack spacing={0.5} sx={{ minWidth: 320 }}>
            <Typography variant="subtitle2" color="text.secondary">Client URL</Typography>
            {globals?.clientUrl ? (
              <Link href={globals.clientUrl} target="_blank" rel="noopener">
                {globals.clientUrl}
              </Link>
            ) : (
              <Typography variant="body1">—</Typography>
            )}
          </Stack>
          <Divider flexItem orientation="vertical" />
          <Stack spacing={0.5} sx={{ minWidth: 160 }}>
            <Typography variant="subtitle2" color="text.secondary">Number of Pages (declared)</Typography>
            <Typography variant="body1">{globals?.numberOfPages ?? "—"}</Typography>
          </Stack>
          <Divider flexItem orientation="vertical" />
          <Stack spacing={0.5} sx={{ minWidth: 160 }}>
            <Typography variant="subtitle2" color="text.secondary">Pages (formatted)</Typography>
            <Typography variant="body1">{pages.length}</Typography>
          </Stack>
        </Stack>
      </Paper>

      {/* Pages */}
      <Paper variant="outlined" sx={{ p: 0 }}>
        <Box sx={{ px: 3, pt: 2 }}>
          <Typography variant="overline" color="text.secondary">
            Pages ({pages.length})
          </Typography>
        </Box>

        <List>
          {pages.map((pg, idx) => {
            const title =
              pg?.data?.pageHeading ||
              pg?.pageHeading ||
              (typeof pg?.pageNumber === "number" ? `Page ${pg.pageNumber}` : `Page ${idx + 1}`);

            return (
              <React.Fragment key={`${pg.pageNumber || idx}`}>
                <ListItem alignItems="flex-start">
                  <ListItemText
                    primary={
                      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                        {typeof pg.pageNumber === "number" ? (
                          <Chip size="small" label={`#${pg.pageNumber}`} />
                        ) : null}
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>{title}</Typography>
                      </Stack>
                    }
                    secondary={
                      <Stack spacing={1} sx={{ mt: 1 }}>
                        {/* URL (if present on top-level) */}
                        {pg.pageUrl ? (
                          <Typography variant="body2" color="text.secondary">
                            <strong>URL:</strong>{" "}
                            <Link href={pg.pageUrl} target="_blank" rel="noopener">{pg.pageUrl}</Link>
                          </Typography>
                        ) : null}

                        {/* Manifest-driven rendering */}
                        <ManifestFieldsPanel
                          manifest={pg.manifest}
                          data={pg.data}
                          onCopy={(text, okMsg) => copyToClipboard(text, okMsg)}
                          onExpand={(mTitle, html) => setModal({ open: true, title: mTitle, html })}
                        />
                      </Stack>
                    }
                  />
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            );
          })}
        </List>
      </Paper>

      {/* Big Preview Modal */}
      <Dialog
        open={modal.open}
        onClose={() => setModal({ open: false, title: "", html: "" })}
        fullWidth
        maxWidth="lg"
        scroll="paper"
      >
        <DialogTitle>{modal.title}</DialogTitle>
        <DialogContent dividers>
          <HtmlPreview html={modal.html} />
        </DialogContent>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snack.open}
        autoHideDuration={2000}
        onClose={() => setSnack({ ...snack, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert onClose={() => setSnack({ ...snack, open: false })} severity={snack.severity} variant="filled">
          {snack.msg}
        </Alert>
      </Snackbar>
    </Container>
  );
}
