// src/pages/UploadPages.jsx
import React from "react";
import { useLocation } from "react-router-dom";
import { Container, Typography, Stack, Button } from "@mui/material";

export default function UploadPages() {
  const { state } = useLocation();
  const formatted =
    state?.formatted || JSON.parse(sessionStorage.getItem("formattedDoc") || "null");

  // Normalise page list (support results.pages or flat array)
  const resultsObj = formatted?.results;
  const pages = Array.isArray(resultsObj?.pages)
    ? resultsObj.pages
    : Array.isArray(formatted?.results)
    ? formatted.results
    : [];

  const pageCount = pages.length;

  const handleDownloadJson = () => {
    try {
      // Only export the actual pages/page fields
      const exportPayload = pages;

      const blob = new Blob([JSON.stringify(exportPayload, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pages.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("JSON download failed", err);
    }
  };

  const handleDownloadCsv = async () => {
    if (!formatted) return;

    try {
      const res = await fetch("/api/parse/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formatted),
      });

      if (!res.ok) {
        console.error("CSV export failed", res.status);
        return;
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${formatted.client_id || "pages"}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("CSV export error", err);
    }
  };


  const handleUploadPages = async () => {
    if (!formatted) return;

    try {
      const res = await fetch("/api/upload/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formatted),
      });

      if (!res.ok) {
        console.error("Upload failed", res.status);
        alert("Upload failed — see console for details.");
        return;
      }

      const data = await res.json();

      alert(
        `Upload Complete:\n\n` +
        `Uploaded: ${data.uploaded}\n` +
        `Failed: ${data.failed}\n\n` +
        `Check console for details.`
      );

      console.log("Upload Summary:", data);

    } catch (err) {
      console.error("Upload error", err);
      alert("Unexpected error while uploading.");
    }
  };


  return (
    <Container sx={{ py: 6 }}>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
        Upload Document
      </Typography>

      <Typography variant="body2">
        Ready to upload {pageCount} page{pageCount === 1 ? "" : "s"}.
      </Typography>

      <Stack direction="row" spacing={2} sx={{ mt: 3 }} flexWrap="wrap">
        <Button variant="outlined" onClick={handleDownloadJson}>
          Download JSON
        </Button>
        <Button variant="outlined" onClick={handleDownloadCsv}>
          Download CSV
        </Button>
        <Button variant="contained" onClick={handleUploadPages}>
          Upload Pages to Site
        </Button>
      </Stack>
    </Container>
  );
}
