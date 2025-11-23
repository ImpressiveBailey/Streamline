// src/pages/Home.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Container, Paper, Stack, TextField, Button, Typography
} from "@mui/material";

export default function RequestGoogleDoc() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFetch = async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/gdoc/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, format: "html" }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json(); // { docId, format, content }
      // inside handleFetch, after const data = await res.json();
      const parsedPayload = { parsed: data.content, docId: data.docId };
      sessionStorage.setItem("parsedDoc", JSON.stringify(parsedPayload));
      navigate("/doc", { state: parsedPayload });
    } catch (e) {
      alert(`Failed to fetch: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={2}>
          <Typography variant="h6">Fetch Google Doc</Typography>
          <TextField
            label="Google Doc URL"
            placeholder="https://docs.google.com/document/d/…/edit"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            fullWidth
          />
          <Button
            variant="contained"
            onClick={handleFetch}
            disabled={loading || !url.trim()}
          >
            {loading ? "Fetching…" : "Fetch"}
          </Button>
        </Stack>
      </Paper>
    </Container>
  );
}
