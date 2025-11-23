// Generic helpers usable project-wide

export const getByPath = (obj, path) => {
  if (!obj || !path) return undefined;
  return path.split(".").reduce((o, k) => (o && k in o ? o[k] : undefined), obj);
};

export const normalizeFaq = (raw, mapping) => {
  const list = Array.isArray(raw) ? raw : [];
  const qPath = mapping?.question?.path || "question";
  const aPath = mapping?.answer?.path || "answer";
  return list.map((item) => ({
    question: getByPath(item, qPath) ?? item?.question ?? item?.q ?? "",
    answer:   getByPath(item, aPath) ?? item?.answer ?? item?.a ?? "",
  }));
};
