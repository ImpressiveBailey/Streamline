// src/pages/DocumentView.jsx
import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box, Button, Container, Dialog, DialogContent, DialogTitle, Divider, Link, List,
  ListItem, ListItemText, Paper, Stack, Typography,
  FormControl, InputLabel, Select, MenuItem, CircularProgress, Alert,
  TextField, Tabs, Tab, Snackbar
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";

const normalizeId = (s = "") =>
  s.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");

function buildOutline(html) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(html || "", "text/html");
  const seen = new Set();
  const mkId = (txt) => {
    const base =
      (txt || "").toLowerCase().replace(/[^a-z0-9\s-]/g, "").trim().replace(/\s+/g, "-").slice(0, 64) || "section";
    let id = base, i = 2;
    while (seen.has(id)) id = `${base}-${i++}`;
    seen.add(id);
    return id;
  };
  doc.querySelectorAll("h1,h2,h3").forEach((h) => {
    const text = (h.textContent || "").trim();
    if (!text) return;
    const existing = h.getAttribute("id");
    h.setAttribute("id", existing || mkId(text));
  });
  return { html: doc.body.innerHTML };
}

export default function ReviewDocument() {
  const { state } = useLocation();
  const navigate = useNavigate();

  // Restore parsed state from session if needed
  let parsedState = state;
  if (!parsedState) {
    try {
      const cached = sessionStorage.getItem("parsedDoc");
      if (cached) parsedState = JSON.parse(cached);
    } catch {}
  }

  const parsed = parsedState && parsedState.parsed ? parsedState.parsed : undefined;
  const hasDoc = Boolean(parsed);
  const globals = parsed?.globals;

  // Keep pages in local state so we can edit them
  const [pages, setPages] = useState(() => {
    const arr = Array.isArray(parsed?.pages) ? parsed.pages : [];
    return [...arr].sort((a, b) => (a.pageNumber || 0) - (b.pageNumber || 0));
  });

  // If parsed changes (rare), refresh pages
  useEffect(() => {
    const arr = Array.isArray(parsed?.pages) ? parsed.pages : [];
    setPages([...arr].sort((a, b) => (a.pageNumber || 0) - (b.pageNumber || 0)));
  }, [parsed?.pages]);

  const [openId, setOpenId] = useState(null);
  const activePage = pages.find((p) => p.pageNumber === openId) || null;

  // ----- Editable modal state -----
  const [tab, setTab] = useState("preview"); // preview | source
  const [editHeading, setEditHeading] = useState("");
  const [editTitle, setEditTitle] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editHtml, setEditHtml] = useState("");
  const [snack, setSnack] = useState({ open: false, msg: "", severity: "success" });

  // Load modal fields when opening / page changes
  useEffect(() => {
    if (!activePage) return;
    setEditHeading(activePage.pageHeading || "");
    setEditTitle(activePage.metaTitle || "");
    setEditDesc(activePage.metaDescription || "");
    setEditHtml(activePage.pageBody || "");
    setTab("preview");
  }, [activePage?.pageNumber]); // eslint-disable-line react-hooks/exhaustive-deps

  const processed = useMemo(() => {
    if (!activePage) return { html: "" };
    return buildOutline(editHtml || "");
  }, [activePage, editHtml]);

  // --- Clients & Content Types (unchanged) ---
  const [clients, setClients] = useState([]);
  const [clientsLoading, setClientsLoading] = useState(false);
  const [clientsError, setClientsError] = useState("");

  const [selectedClient, setSelectedClient] = useState(() => {
    try { return sessionStorage.getItem("selectedClient") || ""; } catch { return ""; }
  });

  useEffect(() => {
    if (!clients.length || selectedClient) return;
    const globalName = globals?.clientName || "";
    if (!globalName) return;
    const wantedId = normalizeId(globalName);
    const byId = clients.find(c => c.id === wantedId);
    const byLabel = clients.find(c => (c.label || "").toLowerCase() === globalName.toLowerCase());
    const match = byId || byLabel;
    if (match) setSelectedClient(match.id);
  }, [clients, selectedClient, globals?.clientName]);

  const [contentTypes, setContentTypes] = useState([]);
  const [ctLoading, setCtLoading] = useState(false);
  const [ctError, setCtError] = useState("");

  const [pageContentType, setPageContentType] = useState(() => {
    try {
      const raw = sessionStorage.getItem("pageContentType");
      return raw ? JSON.parse(raw) : {};
    } catch { return {}; }
  });

  useEffect(() => {
    const run = async () => {
      setClientsLoading(true); setClientsError("");
      try {
        const res = await fetch("/api/clients");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setClients(data.clients || []);
      } catch (e) {
        setClientsError(e.message || "Failed to load clients");
      } finally {
        setClientsLoading(false);
      }
    };
    run();
  }, []);

  useEffect(() => {
    if (!selectedClient) { setContentTypes([]); return; }
    const run = async () => {
      setCtLoading(true); setCtError("");
      try {
        const res = await fetch(`/api/clients/${encodeURIComponent(selectedClient)}/content-types`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setContentTypes(data.contentTypes || []);
      } catch (e) {
        setCtError(e.message || "Failed to load content types");
        setContentTypes([]);
      } finally {
        setCtLoading(false);
      }
    };
    run();
  }, [selectedClient]);

  useEffect(() => {
    try { sessionStorage.setItem("selectedClient", selectedClient || ""); } catch {}
  }, [selectedClient]);
  useEffect(() => {
    try { sessionStorage.setItem("pageContentType", JSON.stringify(pageContentType || {})); } catch {}
  }, [pageContentType]);

  const handleChangeClient = (e) => {
    const newClient = e.target.value || "";
    setSelectedClient(newClient);
    setPageContentType({});
  };

  const handleChangePageCT = (pageNumber, value) => {
    setPageContentType((prev) => ({ ...prev, [pageNumber]: value || "" }));
  };

  // ---------- FORMAT FLOW ----------
  const [formatLoading, setFormatLoading] = useState(false);
  const [formatError, setFormatError] = useState("");

  const allPagesHaveCT = useMemo(() => {
    if (!pages.length) return false;
    return pages.every(p => !!pageContentType[p.pageNumber]);
  }, [pages, pageContentType]);

  const canFormat = !!selectedClient && allPagesHaveCT && !ctLoading && !clientsLoading;

  // Persist the edited pages back into session parsedDoc
  const persistParsedDoc = (nextPages) => {
    try {
      const nextParsedDoc = {
        ...(parsedState || {}),
        parsed: {
          ...(parsed || {}),
          pages: nextPages,
        },
      };
      sessionStorage.setItem("parsedDoc", JSON.stringify(nextParsedDoc));
    } catch {}
  };

  const handleFormat = async () => {
    setFormatError("");
    if (!selectedClient) {
      setFormatError("Please select a client.");
      return;
    }
    if (!allPagesHaveCT) {
      setFormatError("Please select a content type for every page.");
      return;
    }

    // Build payload using the *edited* pages
    const payload = {
      client_id: selectedClient,
      globals: globals || {},
      pages: pages.map(p => ({
        ...p,
        content_type: pageContentType[p.pageNumber] || ""
      })),
    };

    try {
      setFormatLoading(true);
      const res = await fetch("/api/parse/pages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const t = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}${t ? ` — ${t}` : ""}`);
      }
      const data = await res.json(); // { client_id, globals, results }
      try { sessionStorage.setItem("formattedDoc", JSON.stringify(data)); } catch {}
      navigate("/review", { state: { formatted: data } });
    } catch (e) {
      setFormatError(e.message || "Failed to format pages");
    } finally {
      setFormatLoading(false);
    }
  };

  // ----- Modal handlers -----
  const openPreview = (pageNumber) => setOpenId(pageNumber);

  const saveModalEdits = () => {
    if (!activePage) return;
    const nextPages = pages.map((p) =>
      p.pageNumber === activePage.pageNumber
        ? {
            ...p,
            pageHeading: editHeading,
            metaTitle: editTitle,
            metaDescription: editDesc,
            pageBody: editHtml,
          }
        : p
    );
    setPages(nextPages);
    persistParsedDoc(nextPages);
    setSnack({ open: true, msg: "Saved changes to this page", severity: "success" });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      {!hasDoc ? (
        <Paper variant="outlined" sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>No document loaded</Typography>
          <Button onClick={() => navigate("/")}>Go back</Button>
        </Paper>
      ) : (
        <Stack spacing={3}>
          {/* Header */}
          <Stack direction="row" alignItems="center" justifyContent="space-between" flexWrap="wrap" gap={1}>
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              Google Doc Breakdown
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button onClick={() => navigate("/")}>Back</Button>
              <Button
                variant="contained"
                onClick={handleFormat}
                disabled={!canFormat || formatLoading}
              >
                {formatLoading ? "Formatting…" : "Format"}
              </Button>
            </Stack>
          </Stack>

          {formatError ? <Alert severity="error">{formatError}</Alert> : null}

          {/* Globals (with Client selector) */}
          <Paper variant="outlined" sx={{ p: 3 }}>
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
                <Typography variant="subtitle2" color="text.secondary">Number of Pages</Typography>
                <Typography variant="body1">{globals?.numberOfPages ?? "—"}</Typography>
              </Stack>

              <Divider flexItem orientation="vertical" />

              <Stack spacing={1} sx={{ minWidth: 260 }}>
                <FormControl size="small" fullWidth>
                  <InputLabel id="client-select-label">Select Client</InputLabel>
                  <Select
                    labelId="client-select-label"
                    label="Select Client"
                    value={selectedClient}
                    onChange={handleChangeClient}
                    disabled={clientsLoading}
                    renderValue={(v) => {
                      if (!v) return "Select Client";
                      const found = clients.find((c) => c.id === v);
                      return found ? found.label : v;
                    }}
                  >
                    {clientsLoading ? (
                      <MenuItem disabled>
                        <CircularProgress size={18} sx={{ mr: 1 }} /> Loading…
                      </MenuItem>
                    ) : clientsError ? (
                      <MenuItem disabled>Error: {clientsError}</MenuItem>
                    ) : clients.length ? (
                      clients.map((c) => (
                        <MenuItem key={c.id} value={c.id}>{c.label}</MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No clients found</MenuItem>
                    )}
                  </Select>
                </FormControl>
                {selectedClient ? (
                  ctLoading ? (
                    <Typography variant="caption" color="text.secondary">Loading content types…</Typography>
                  ) : ctError ? (
                    <Typography variant="caption" color="error">Failed to load content types: {ctError}</Typography>
                  ) : null
                ) : (
                  <Typography variant="caption" color="text.secondary">Choose a client to load content types</Typography>
                )}
              </Stack>
            </Stack>
          </Paper>

          {/* Pages List with per-page CT selector (right side) */}
          <Paper variant="outlined" sx={{ p: 0 }}>
            <Box sx={{ px: 3, pt: 2 }}>
              <Typography variant="overline" color="text.secondary">Pages ({pages.length})</Typography>
            </Box>
            <List>
              {pages.map((p) => (
                <React.Fragment key={String(p.pageNumber)}>
                  <ListItem
                    secondaryAction={
                      <Stack direction="row" spacing={1} alignItems="center">
                        <FormControl size="small" sx={{ minWidth: 220 }}>
                          <InputLabel id={`ct-label-${p.pageNumber}`}>Content Type</InputLabel>
                          <Select
                            labelId={`ct-label-${p.pageNumber}`}
                            label="Content Type"
                            value={pageContentType[p.pageNumber] || ""}
                            onChange={(e) => handleChangePageCT(p.pageNumber, e.target.value)}
                            disabled={!selectedClient || ctLoading || !!ctError}
                            renderValue={(v) => {
                              if (!v) return "Content Type";
                              const found = contentTypes.find((ct) => ct.id === v);
                              return found ? found.label : v;
                            }}
                          >
                            {!selectedClient ? (
                              <MenuItem disabled>Select a client first</MenuItem>
                            ) : ctLoading ? (
                              <MenuItem disabled>
                                <CircularProgress size={18} sx={{ mr: 1 }} /> Loading…
                              </MenuItem>
                            ) : ctError ? (
                              <MenuItem disabled>Error: {ctError}</MenuItem>
                            ) : contentTypes.length ? (
                              contentTypes.map((ct) => (
                                <MenuItem key={ct.id} value={ct.id}>{ct.label}</MenuItem>
                              ))
                            ) : (
                              <MenuItem disabled>No content types</MenuItem>
                            )}
                          </Select>
                        </FormControl>

                        <Button
                          size="small"
                          variant="contained"
                          startIcon={<VisibilityIcon />}
                          onClick={() => openPreview(p.pageNumber)}
                        >
                          Preview
                        </Button>
                      </Stack>
                    }
                  >
                    <ListItemText
                      primary={
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {p.pageHeading || p.titleMarker || "Untitled"}
                        </Typography>
                      }
                      secondary={
                        p.pageUrl ? (
                          <Typography variant="body2" color="text.secondary">
                            <strong>URL:</strong>{" "}
                            <Link href={p.pageUrl} target="_blank" rel="noopener">
                              {p.pageUrl}
                            </Link>
                          </Typography>
                        ) : null
                      }
                    />
                  </ListItem>
                  <Divider component="li" />
                </React.Fragment>
              ))}
            </List>
          </Paper>

          {/* Modal (editable) */}
          <Dialog open={Boolean(activePage)} onClose={() => setOpenId(null)} fullWidth maxWidth="md" scroll="paper">
            {activePage ? (
              <>
                <DialogTitle sx={{ pr: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                    {activePage.pageHeading || "Page Details"}
                  </Typography>
                  <Stack spacing={1.25}>
                    <TextField
                      label="Page Heading (H1)"
                      value={editHeading}
                      onChange={(e) => setEditHeading(e.target.value)}
                      size="small"
                      fullWidth
                    />
                    <TextField
                      label="Meta Title"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      size="small"
                      fullWidth
                    />
                    <TextField
                      label="Meta Description"
                      value={editDesc}
                      onChange={(e) => setEditDesc(e.target.value)}
                      size="small"
                      fullWidth
                      multiline
                      minRows={2}
                    />
                  </Stack>
                </DialogTitle>

                <DialogContent dividers>
                  <Stack spacing={1.5}>
                    <Stack direction="row" alignItems="center" justifyContent="space-between">
                      <Typography variant="subtitle2">Body HTML</Typography>
                      <Tabs
                        value={tab}
                        onChange={(_, v) => setTab(v)}
                        aria-label="HTML tabs"
                        sx={{
                          minHeight: 32,
                          "& .MuiTab-root": { minHeight: 32, py: 0.5 },
                        }}
                      >
                        <Tab value="preview" label="Preview" />
                        <Tab value="source" label="Source" />
                      </Tabs>
                    </Stack>

                    {tab === "preview" ? (
                      <Box
                        sx={{
                          p: 2,
                          border: (t) => `1px solid ${t.palette.divider}`,
                          borderRadius: 1,
                          overflowX: "auto",
                          "& h1": { fontSize: "2rem", fontWeight: 700, mt: 3, mb: 1.5 },
                          "& h2": { fontSize: "1.6rem", fontWeight: 700, mt: 3, mb: 1.25 },
                          "& h3": { fontSize: "1.3rem", fontWeight: 600, mt: 2.5, mb: 1 },
                          "& p": { lineHeight: 1.75, mb: 2 },
                          "& ul, & ol": { pl: 3.5, mb: 2 },
                          "& li": { mb: 0.5 },
                          "& a": { textDecoration: "underline", wordBreak: "break-word" },
                          "& img": { maxWidth: "100%", height: "auto", borderRadius: 1, my: 2 },
                          "& blockquote": {
                            borderLeft: (theme) => `4px solid ${theme.palette.divider}`,
                            pl: 2,
                            color: "text.secondary",
                            fontStyle: "italic",
                            my: 2,
                          },
                          "& code, & pre": {
                            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                            fontSize: "0.95em",
                            backgroundColor: (theme) =>
                              theme.palette.mode === "dark" ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                          },
                          "& pre": { p: 2, borderRadius: 1, overflowX: "auto" },
                          "& table": { width: "100%", borderCollapse: "collapse", my: 2 },
                          "& th, & td": {
                            border: (theme) => `1px solid ${theme.palette.divider}`,
                            p: 1,
                            textAlign: "left",
                          },
                        }}
                        dangerouslySetInnerHTML={{ __html: processed.html }}
                      />
                    ) : (
                      <TextField
                        label="Body HTML (source)"
                        value={editHtml}
                        onChange={(e) => setEditHtml(e.target.value)}
                        fullWidth
                        size="small"
                        multiline
                        minRows={12}
                      />
                    )}

                    <Stack direction="row" justifyContent="flex-end" spacing={1}>
                      <Button onClick={() => setOpenId(null)}>Close</Button>
                      <Button variant="contained" onClick={saveModalEdits}>
                        Save changes
                      </Button>
                    </Stack>
                  </Stack>
                </DialogContent>
              </>
            ) : null}
          </Dialog>

          <Snackbar
            open={snack.open}
            autoHideDuration={2000}
            onClose={() => setSnack({ ...snack, open: false })}
            anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
            message={snack.msg}
          />
        </Stack>
      )}
    </Container>
  );
}
