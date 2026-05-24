/** Shared skeleton loaders for dashboard tables */
function skeletonTableRows(cols, rows = 5) {
  let html = '';
  for (let r = 0; r < rows; r++) {
    html += '<tr>';
    for (let c = 0; c < cols; c++) {
      const w = c === 0 ? 'short' : c % 2 ? 'med' : 'wide';
      html += `<td><div class="skeleton-line ${w}"></div></td>`;
    }
    html += '</tr>';
  }
  return html;
}

function skeletonStatCards(n = 3) {
  return `<div class="skeleton-cards">${'<div class="skeleton-card-block"></div>'.repeat(n)}</div>`;
}
