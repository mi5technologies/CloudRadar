function i(e,o="CloudRadar Report"){const a=e.trimStart().toLowerCase().startsWith("<!doctype")||e.trimStart().toLowerCase().startsWith("<html")?e:`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${o}</title>
  <style>
    body { font-family: sans-serif; font-size: 13px; color: #111; padding: 24px; }
    pre  { background: #f1f5f9; padding: 16px; border-radius: 6px; font-size: 12px;
           white-space: pre-wrap; word-break: break-word; }
    h1   { font-size: 18px; margin-bottom: 16px; }
    @media print { body { padding: 0; } }
  </style>
</head>
<body>
  <h1>${o}</h1>
  <pre>${e.replace(/</g,"&lt;").replace(/>/g,"&gt;")}</pre>
</body>
</html>`,t=window.open("","_blank");if(!t){const n=new Blob([a],{type:"text/html"}),c=URL.createObjectURL(n),r=document.createElement("a");r.href=c,r.download=`${o.replace(/\s+/g,"_")}.html`,r.click(),URL.revokeObjectURL(c);return}t.document.write(a),t.document.close(),t.onload=()=>{t.focus(),t.print()},setTimeout(()=>{try{t.focus(),t.print()}catch{}},600)}export{i as o};
