import React from "react";
import { DefaultTypeRegistry, TextFieldView } from "./FieldViews";
import { getByPath } from "./manifestUtils";

/**
 * Renders ONE field from a manifest using a registry.
 * Props:
 * - field: { label, path, type, upload? { ... }, ... }
 * - data:  the page's `data` object (i.e. result.data)
 * - registry: optional registry to override/add types
 * - onCopy(content, okMsg?)
 * - onExpand(title, htmlContent)
 */
export default function ManifestFieldRenderer({
  field,
  data,
  registry = DefaultTypeRegistry,
  onCopy,
  onExpand,
}) {
  if (!field) return null;

  const { label, path, type, upload } = field;
  const value = getByPath({ data }, path); // manifest paths assume "data.xxx"
  const View = registry[type] || TextFieldView;

  // For FAQ we also want mapping for q/a
  const mapping = field?.upload?.mapping || field?.mapping;

  // Pass a minimal, consistent prop shape
  const viewProps = {
    label: label || upload?.metafield || path,
    value,
    html: value,     // used by HtmlFieldView
    mapping,         // used by FaqFieldView
    onCopy,
    onExpand,
  };

  return <View {...viewProps} />;
}
