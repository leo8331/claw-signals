import re

# Read restored original file
with open(r'D:\tdx临时\历史数据\2026-06-05\sector.html', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original file size: {len(content)} bytes")

# Extract L2 table rows
# Find the tbody content for tbl-l2
l2_table_start = content.find('<table id="tbl-l2">')
if l2_table_start == -1:
    print("ERROR: Could not find tbl-l2")
    exit(1)

# Find tbody start and end for L2
l2_tbody_start = content.find('<tbody>', l2_table_start)
if l2_tbody_start == -1:
    print("ERROR: Could not find tbody for L2")
    exit(1)

# Find the closing </tbody> for L2 table
# It should be before the L3 table starts
l3_table_start = content.find('<table id="tbl-l3">')
if l3_table_start == -1:
    print("ERROR: Could not find tbl-l3")
    exit(1)

l2_tbody_end = content.rfind('</tbody>', l2_tbody_start, l3_table_start)
if l2_tbody_end == -1:
    print("ERROR: Could not find tbody end for L2")
    exit(1)

l2_rows = content[l2_tbody_start + 7:l2_tbody_end].strip()
print(f"L2 rows extracted: {len(l2_rows)} chars")
print(f"L2 rows sample: {l2_rows[:100]}")

# Extract L3 table rows
l3_tbody_start = content.find('<tbody>', l3_table_start)
if l3_tbody_start == -1:
    print("ERROR: Could not find tbody for L3")
    exit(1)

# Find the closing </tbody> for L3 table (before <div class="ft">)
ft_start = content.find('class="ft"', l3_table_start)
if ft_start == -1:
    print("ERROR: Could not find footer")
    exit(1)

l3_tbody_end = content.rfind('</tbody>', l3_tbody_start, ft_start)
if l3_tbody_end == -1:
    print("ERROR: Could not find tbody end for L3")
    exit(1)

l3_rows = content[l3_tbody_start + 7:l3_tbody_end].strip()
print(f"L3 rows extracted: {len(l3_rows)} chars")
print(f"L3 rows sample: {l3_rows[:100]}")

# Extract JavaScript
js_start = content.find('<script>')
js_end = content.find('</script>', js_start)
if js_start == -1 or js_end == -1:
    print("ERROR: Could not find JavaScript")
    exit(1)

js_code = content[js_start:js_end + 9]  # Include <script> and </script>
print(f"JavaScript extracted: {len(js_code)} chars")

print("\nData extraction complete. Building new HTML...")

# Build new HTML with design system
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
'''

html += js_code + '''
</body>
</html>'''

# Write the new file
output_path = r'D:\tdx临时\历史数据\2026-06-05\sector.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nNew file created: {output_path}")
print(f"File size: {len(html)} bytes")

# Verify
with open(output_path, 'r', encoding='utf-8') as f:
    new_content = f.read()

l2_count = new_content.count('<tr data')
print(f"Verification: {l2_count} table rows in new file")
