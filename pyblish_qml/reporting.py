"""Render optional JAM report dictionaries without a dependency on the host."""
from html import escape
import json


def render_report(report):
    if not isinstance(report, dict) or report.get("schema_version") != 1:
        raise ValueError("Unsupported validation report")
    checks = report["checks"]
    counts = {s: sum(c["status"] == s for c in checks)
              for s in ("failed", "warning", "crashed", "passed", "skipped")}
    heading = "Checks could not complete" if counts["crashed"] else (
        "Publishing blocked" if counts["failed"] else "Validation complete")
    # Qt rich text has generous default block margins; use compact report spacing.
    style = ("<style>p { margin-top: 3px; margin-bottom: 4px; } "
             "h2 { font-size: 16px; margin-top: 0px; margin-bottom: 4px; } "
             "h3 { font-size: 13px; margin-top: 8px; margin-bottom: 3px; }</style>")
    out = [style, "<h2>" + heading + "</h2>", "<p><b>" + escape(report.get("instance", "Context")) + "</b></p>", "<p>" + escape(
        ", ".join("{} {}".format(n, s) for s, n in counts.items()) + " checks") + "</p>"]
    details = [report.get("traceback", "")]
    grouped = {}
    for check in sorted(checks, key=lambda c: {"crashed": 0, "failed": 1, "warning": 2}.get(c["status"], 3)):
        details.append("{}: {}\n{}".format(check["rule"], check["status"], check.get("detail", "")))
        for finding in check["findings"]:
            key = (check["rule"], finding["title"], finding.get("status", check["status"]))
            grouped.setdefault(key, []).append(finding)
    for (rule, title, status), findings in grouped.items():
        out.append("<h3>{} &mdash; {}</h3>".format(escape(title), escape(status)))
        for description in dict.fromkeys(f["description"] for f in findings):
            out.append("<p>" + escape(description).replace("\n", "<br>") + "</p>")
        rows = [r for f in findings for r in f.get("comparisons", [])]
        if rows:
            out.append('<table width="100%" cellpadding="3" cellspacing="0"><tr><th align="left">Current</th><th align="left">Expected</th></tr>')
            for row in rows:
                out.append("<tr><td>{}</td><td>{}</td></tr>".format(escape(str(row["actual"])), escape(str(row["expected"]))))
            out.append("</table>")
        affected = list(dict.fromkeys(str(a) for f in findings for a in f.get("affected", [])))
        if affected:
            out.append("<p><b>Affected:</b><br>" + "<br>".join(map(escape, affected)) + "</p>")
        for remedy in dict.fromkeys(f.get("remedy", "") for f in findings):
            if remedy:
                out.append("<p><b>Next step:</b> " + escape(remedy) + "</p>")
        out.append("<p><small>" + escape(rule) + "</small></p><hr>")
    return heading, "".join(out), "\n\n".join(details)


def report_json(report):
    return json.dumps(report, ensure_ascii=False, indent=2)
