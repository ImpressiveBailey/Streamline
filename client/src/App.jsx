// src/App.jsx
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import RequestGoogleDoc from "./pages/RequestGoogleDoc";
import ReviewDocument from "./pages/ReviewDocument";
import ReviewFormattedPages from "./pages/ReviewFormattedPages";
import UploadPages from "./pages/UploadPages";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RequestGoogleDoc />} />
        <Route path="/doc" element={<ReviewDocument />} />
        <Route path="/review" element={<ReviewFormattedPages />} />
        <Route path="/upload" element={<UploadPages />} />
        <Route path="*" element={<Navigate to={"/"} replace />} />
      </Routes>
    </Router>
  );
}
export default App;
