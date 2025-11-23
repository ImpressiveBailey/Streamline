import React, { useMemo, useRef, useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Tabs,
  Tab,
  Box,
  Paper,
  Stack,
  TextField,
  Button,
  IconButton,
  Chip,
  Divider,
  InputAdornment,
} from "@mui/material";
import {
  ContentPaste,
  Link as LinkIcon,
  UploadFile,
  Delete,
  Add,
  Save,
} from "@mui/icons-material";

// ----- helpers -----
const slugify = (str) =>
  (str || "")
    .toString()
    .trim()
    .toLowerCase()
    .replace(/['"]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");

const extractH1 = (raw) => {
  if (!raw) return "";
  // Try Markdown # Heading
  const md = raw.match(/^\s*#\s+(.+)$/m);
  if (md) return md[1].trim();
  // Try HTML <h1>
  const html = raw.match(/<h1[^>]*>(.*?)<\/h1>/i);
  if (html) return html[1].replace(/<[^>]*>/g, "").trim();
  // Fallback: first non-empty line
  const first = raw.split(/\r?\n/).find((l) => l.trim().length > 0);
  return (first || "").trim();
};

// ----- component -----
export default function Home() {
  const [tab, setTab] = useState(0); // 0=paste, 1=url, 2=file
  const fileInputRef = useRef(null);

  const [rawInput, setRawInput] = useState(""); // paste/file text
  const [docUrl, setDocUrl] = useState(""); // google doc url

  const [title, setTitle] = useState("");
  const [h1, setH1] = useState("");
  const [slug, setSlug] = useState("");
  const [metaTitle, setMetaTitle] = useState("");
  const [metaDescription, setMetaDescription] = useState("");

  const [tags, setTags] = useState([]);
  const [tagDraft, setTagDraft] = useState("");

  const [faqs, setFaqs] = useState([{ q: "", a: "" }]);

  // Auto-suggest H1 & slug off paste content
  const suggestedH1 = useMemo(() => (h1 ? h1 : extractH1(rawInput)), [rawInput, h1]);
  const suggestedSlug = useMemo(
    () => (slug ? slug : slugify(title || suggestedH1)),
    [title, suggestedH1, slug]
  );

  const jsonPreview = useMemo(
    () =>
      ({
        source: ["paste", "url", "file"][tab],
        docUrl,
        title: title || suggestedH1,
        h1: suggestedH1,
        slug: suggestedSlug,
        metaTitle,
        metaDescription,
        tags,
        faqs: faqs.filter((f) => f.q.trim() || f.a.trim()),
        raw: rawInput,
      }),
    [
      tab,
      docUrl,
      title,
      suggestedH1,
      suggestedSlug,
      metaTitle,
      metaDescription,
      tags,
      faqs,
      rawInput,
    ]
  );

  const handleAddTag = () => {
    const t = tagDraft.trim();
    if (!t) return;
    if (!tags.includes(t)) setTags((prev) => [...prev, t]);
    setTagDraft("");
  };

  const handleRemoveTag = (t) => {
    setTags((prev) => prev.filter((x) => x !== t));
  };

  const handleAddFaq = () => setFaqs((prev) => [...prev, { q: "", a: "" }]);
  const handleRemoveFaq = (idx) =>
    setFaqs((prev) => prev.filter((_, i) => i !== idx));

  const handleFilePick = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Basic text read; you can add .docx/.gdoc parsing later.
    const text = await file.text();
    setRawInput(text);
    if (!title) setTitle(extractH1(text));
  };

  const handleIngestFromUrl = () => {
    // Placeholder: you’ll later call your Flask endpoint to fetch/clean Google Doc.
    // For now we just stash the URL; you can set rawInput from the response.
    console.log("TODO -> fetch & parse Google Doc:", docUrl);
  };

  const handleSubmit = () => {
    // For now, just log. Later: POST to Flask (e.g., /api/content/ingest)
    console.log("SUBMIT PAYLOAD", jsonPreview);
    alert("Payload ready. Check console for JSON. Wire to Flask next.");
  };

  const resetAll = () => {
    setTab(0);
    setRawInput("");
    setDocUrl("");
    setTitle("");
    setH1("");
    setSlug("");
    setMetaTitle("");
    setMetaDescription("");
    setTags([]);
    setTagDraft("");
    setFaqs([{ q: "", a: "" }]);
  };

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Content Upload Assistant
          </Typography>
          <Button color="inherit" onClick={resetAll}>
            Reset
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Intake tabs */}
        <Paper variant="outlined" sx={{ mb: 3 }}>
          <Tabs
            value={tab}
            onChange={(_, v) => setTab(v)}
            variant="fullWidth"
            textColor="primary"
            indicatorColor="primary"
          >
            <Tab icon={<ContentPaste />} label="Paste Content" />
            <Tab icon={<LinkIcon />} label="Google Doc URL" />
            <Tab icon={<UploadFile />} label="Upload File" />
          </Tabs>

          <Box sx={{ p: 3 }}>
            {tab === 0 && (
              <Stack spacing={2}>
                <TextField
                  label="Paste raw content (Markdown or HTML)"
                  placeholder="# Heading\n\nBody content…"
                  value={rawInput}
                  onChange={(e) => setRawInput(e.target.value)}
                  multiline
                  minRows={10}
                  fullWidth
                />
              </Stack>
            )}

            {tab === 1 && (
              <Stack spacing={2}>
                <TextField
                  label="Google Doc URL"
                  placeholder="https://docs.google.com/document/d/…"
                  value={docUrl}
                  onChange={(e) => setDocUrl(e.target.value)}
                  fullWidth
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LinkIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                <Stack direction="row" spacing={1}>
                  <Button variant="contained" onClick={handleIngestFromUrl}>
                    Fetch & Parse (stub)
                  </Button>
                  <Typography variant="body2" color="text.secondary" sx={{ alignSelf: "center" }}>
                    (Wires to Flask later)
                  </Typography>
                </Stack>
              </Stack>
            )}

            {tab === 2 && (
              <Stack spacing={2}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.md,.html"
                  style={{ display: "none" }}
                  onChange={handleFilePick}
                />
                <Button
                  variant="contained"
                  startIcon={<UploadFile />}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Choose file
                </Button>
                <Typography variant="body2" color="text.secondary">
                  For now, simple text/Markdown/HTML files are supported. Add .docx/.gdoc parsing later in Flask.
                </Typography>
              </Stack>
            )}
          </Box>
        </Paper>

        {/* Mapping / metadata */}
        <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Map & Enrich
          </Typography>
          <Stack spacing={2}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="If blank, we’ll use H1"
                fullWidth
              />
              <TextField
                label="H1"
                value={h1 || suggestedH1}
                onChange={(e) => setH1(e.target.value)}
                fullWidth
              />
            </Stack>

            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Slug"
                value={slug || suggestedSlug}
                onChange={(e) => setSlug(e.target.value)}
                fullWidth
              />
              <TextField
                label="Meta Title"
                value={metaTitle}
                onChange={(e) => setMetaTitle(e.target.value)}
                fullWidth
              />
            </Stack>

            <TextField
              label="Meta Description"
              value={metaDescription}
              onChange={(e) => setMetaDescription(e.target.value)}
              placeholder="150–160 characters recommended"
              multiline
              minRows={3}
              fullWidth
            />

            <Divider />

            {/* Tags */}
            <Typography variant="subtitle1">Tags</Typography>
            <Stack direction="row" spacing={1}>
              <TextField
                label="Add a tag"
                value={tagDraft}
                onChange={(e) => setTagDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
                size="small"
              />
              <Button variant="outlined" onClick={handleAddTag}>
                Add
              </Button>
            </Stack>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {tags.map((t) => (
                <Chip key={t} label={t} onDelete={() => handleRemoveTag(t)} sx={{ mb: 1 }} />
              ))}
            </Stack>

            <Divider />

            {/* FAQs */}
            <Typography variant="subtitle1">FAQs</Typography>
            <Stack spacing={2}>
              {faqs.map((f, i) => (
                <Paper key={i} variant="outlined" sx={{ p: 2 }}>
                  <Stack spacing={1}>
                    <TextField
                      label={`Q${i + 1}`}
                      value={f.q}
                      onChange={(e) =>
                        setFaqs((prev) =>
                          prev.map((x, idx) => (idx === i ? { ...x, q: e.target.value } : x))
                        )
                      }
                      fullWidth
                    />
                    <TextField
                      label="Answer"
                      value={f.a}
                      onChange={(e) =>
                        setFaqs((prev) =>
                          prev.map((x, idx) => (idx === i ? { ...x, a: e.target.value } : x))
                        )
                      }
                      fullWidth
                      multiline
                      minRows={2}
                    />
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <IconButton color="error" onClick={() => handleRemoveFaq(i)} size="small">
                        <Delete />
                      </IconButton>
                    </Stack>
                  </Stack>
                </Paper>
              ))}
            </Stack>
            <Button startIcon={<Add />} onClick={handleAddFaq}>
              Add FAQ
            </Button>
          </Stack>
        </Paper>

        {/* Actions + Preview */}
        <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
          <Paper variant="outlined" sx={{ p: 3, flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              Actions
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleSubmit}
              >
                Save / Send to API
              </Button>
              <Button variant="text" color="inherit" onClick={resetAll}>
                Clear
              </Button>
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 3, flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              JSON Preview
            </Typography>
            <Box
              component="pre"
              sx={{
                m: 0,
                p: 2,
                bgcolor: (t) => (t.palette.mode === "dark" ? "#0b0b0b" : "#f6f8fa"),
                borderRadius: 1,
                maxHeight: 400,
                overflow: "auto",
                fontSize: 13,
              }}
            >
              {JSON.stringify(jsonPreview, null, 2)}
            </Box>
          </Paper>
        </Stack>
      </Container>
    </>
  );
}
