import Papa from "papaparse";

export function useFileUpload(setRaw) {
  function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const isCSV = file.name.toLowerCase().endsWith(".csv");
    const isJSON = file.name.toLowerCase().endsWith(".json");
    const reader = new FileReader();
    reader.onload = () => {
      try {
        if (isCSV) {
          const res = Papa.parse(reader.result, { header: true, skipEmptyLines: true });
          const rows = (res.data || [])
            .map(r => ({
              // Core volunteer info
              branch: String(r.branch ?? r.BRANCH ?? r.Branch ?? "").trim(),
              hours: Number(r.hours ?? r.HOURS ?? r.Hrs ?? 0) || 0,
              assignee: String(r.assignee ?? r.ASSIGNEE ?? r.Name ?? r.ASSIGNEE ?? "").trim(),
              date: r.date ? String(r.date) : (r.Date ? String(r.Date) : undefined),
              
              // Member information
              is_member: String(r.is_member ?? r.member ?? r.Member ?? r["ARE YOU A YMCA MEMBER"] ?? "")
                .toLowerCase().startsWith("y"),
              member_branch: String(r.member_branch ?? r["MEMBER BRANCH"] ?? r.MemberBranch ?? "").trim(),
              
              // Project information
              project_tag: String(r.project_tag ?? r["PROJECT TAG"] ?? r.ProjectTag ?? "").trim(),
              project_catalog: String(r.project_catalog ?? r["PROJECT CATALOG"] ?? r.ProjectCatalog ?? "").trim(),
              project: String(r.project ?? r.PROJECT ?? r.Project ?? "").trim(),
              
              // Additional fields
              category: String(r.category ?? r.Category ?? "").trim(),
              department: String(r.department ?? r.Department ?? "").trim(),
            }))
            .filter(r => r.hours > 0); // Automatically remove 0-hour entries
          setRaw(rows);
        } else if (isJSON) {
          const parsed = JSON.parse(reader.result);
          setRaw(parsed);
        } else {
          alert("Please upload a CSV or JSON file.");
        }
      } catch (err) {
        console.error(err);
        alert("Could not parse the file. Expected columns: branch, hours, assignee, is_member, date");
      }
    };
    reader.readAsText(file);
  }

  return handleFile;
}