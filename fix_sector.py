import re

# Read original file
with open(r'D:\tdx临时\历史数据\2026-06-05\sector.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract L2 rows - find tbody content for tbl-l2
l2_start = content.find('id="tbl-l2"')
if l2_start == -1:
    print("Could not find tbl-l2")
    exit(1)

l2_tbody_start = content.find('<tbody>', l2_start)
if l2_tbody_start == -1:
    print("Could not find tbody for tbl-l2")
    exit(1)

l2_tbody_end = content.find('</tbody>', l2_tbody_start)
if l2_tbody_end == -1:
    print("Could not find end of tbody for tbl-l2")
    exit(1)

l2_rows = content[l2_tbody_start + 7:l2_tbody_end].strip()

# Extract L3 rows
l3_start = content.find('id="tbl-l3"')
if l3_start == -1:
    print("Could not find tbl-l3")
    exit(1)

l3_tbody_start = content.find('<tbody>', l3_start)
if l3_tbody_start == -1:
    print("Could not find tbody for tbl-l3")
    exit(1)

l3_tbody_end = content.find('</tbody>', l3_tbody_start)
if l3_tbody_end == -1:
    print("Could not find end of tbody for tbl-l3")
    exit(1)

l3_rows = content[l3_tbody_start + 7:l3_tbody_end].strip()

print(f"Extracted L2 rows: {len(l2_rows)} chars")
print(f"Extracted L3 rows: {len(l3_rows)} chars")

# Build new HTML
html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>行业排行 2026-06-05</title>
<link rel="stylesheet" href="../../style.css">
<style>
.update-info { color: var(--text-tertiary); font-size: 13px; margin-bottom: 20px; }
.update-info a { color: var(--accent); text-decoration: none; }
.update-info a:hover { color: #85B3F0; }
.sort-hint { float: right; font-size: 12px; color: var(--accent); }
#tbl-l3 { display: none; }
.up { color: var(--red); }
.dn { color: var(--green); }
th.sorted::after { content: " ▾"; font-size: 10px; color: var(--accent); }
</style>
</head>
<body>

<nav class="top-nav">
  <div class="nav-inner">
    <a href="../../" class="nav-brand">CLAW</a>
    <a href="../../" class="nav-link">首页</a>
    <a href="sector.html" class="nav-link nav-active">行业排行</a>
    <a href="stocks.html" class="nav-link">每日选股</a>
    <a href="portfolio.html" class="nav-link">持仓管理</a>
    <a href="backtest.html" class="nav-link">回测分析</a>
    <span class="nav-sep">|</span>
    <span class="nav-right" style="color:var(--text-muted);font-size:12px;">2026-06-05</span>
  </div>
</nav>

<main>
  <div class="page-header">
    <h1>行业排行 <span class="accent">2026-06-05</span></h1>
    <div class="subtitle">申万二级/三级行业 · 3/5/10/20日涨跌排行 · 点击表头排序</div>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('l2')">二级行业 (127)</div>
    <div class="tab" onclick="switchTab('l3')">三级行业 (344)</div>
  </div>

  <div id="tbl-wrapper">
    <table id="tbl-l2">
      <thead>
        <tr>
          <th>#</th>
          <th>行业</th>
          <th onclick="sortTable('l2',2)" class="sortable">3日涨跌</th>
          <th onclick="sortTable('l2',3)" class="sortable">5日涨跌</th>
          <th onclick="sortTable('l2',4)" class="sortable">10日涨跌</th>
          <th onclick="sortTable('l2',5)" class="sortable sorted">20日涨跌</th>
        </tr>
      </thead>
      <tbody>
'''
html += l2_rows + '''
      </tbody>
    </table>

    <table id="tbl-l3">
      <thead>
        <tr>
          <th>#</th>
          <th>行业</th>
          <th onclick="sortTable('l3',2)" class="sortable">3日涨跌</th>
          <th onclick="sortTable('l3',3)" class="sortable">5日涨跌</th>
          <th onclick="sortTable('l3',4)" class="sortable">10日涨跌</th>
          <th onclick="sortTable('l3',5)" class="sortable sorted">20日涨跌</th>
        </tr>
      </thead>
      <tbody>
'''
html += l3_rows + '''
      </tbody>
    </table>
  </div>
</main>

<footer class="page-footer">
  CLAW v3.0 | 2026-06-05
</footer>

<script>
let sortDir={l2:{},l3:{}};
function switchTab(tab){
  document.getElementById('tbl-l2').style.display=tab==='l2'?'table':'none';
  document.getElementById('tbl-l3').style.display=tab==='l3'?'table':'none';
  document.querySelectorAll('.tab').forEach(function(t){
    var isActive=(tab==='l2'&&t.textContent.indexOf('二级')>=0)||(tab==='l3'&&t.textContent.indexOf('三级')>=0);
    if(isActive)t.classList.add('active');else t.classList.remove('active');
  });
}
function sortTable(tbl,col){
  var t=document.getElementById('tbl-'+tbl);
  var rows=Array.prototype.slice.call(t.querySelectorAll('tbody tr'));
  var key=['','','r3','r5','r10','r20'][col];
  sortDir[tbl]=sortDir[tbl]||Object();
  sortDir[tbl][col]=sortDir[tbl][col]===-1?1:-1;
  rows.sort(function(a,b){return (parseFloat(a.dataset[key])-parseFloat(b.dataset[key]))*sortDir[tbl][col]});
  rows.forEach(function(r){t.querySelector('tbody').appendChild(r)});
  t.querySelectorAll('th').forEach(function(h){h.classList.remove('sorted')});
  t.querySelectorAll('th')[col].classList.add('sorted');
}
</script>
</body>
</html>'''

# Write output
output_path = r'D:\tdx临时\历史数据\2026-06-05\sector.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"File created successfully: {output_path}")
print(f"Total file size: {len(html)} bytes")
