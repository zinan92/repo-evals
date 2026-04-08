const searchInput = document.querySelector('[data-role="search"]');
const bucketSelect = document.querySelector('[data-role="bucket-filter"]');
const confidenceSelect = document.querySelector('[data-role="confidence-filter"]');
const cards = Array.from(document.querySelectorAll('[data-role="repo-card"]'));

function applyFilters() {
  const q = (searchInput?.value || '').trim().toLowerCase();
  const bucket = bucketSelect?.value || '';
  const confidence = confidenceSelect?.value || '';

  for (const card of cards) {
    const hay = (card.dataset.search || '').toLowerCase();
    const matchesSearch = !q || hay.includes(q);
    const matchesBucket = !bucket || card.dataset.bucket === bucket;
    const matchesConfidence = !confidence || card.dataset.confidence === confidence;
    card.style.display = (matchesSearch && matchesBucket && matchesConfidence) ? '' : 'none';
  }
}

for (const el of [searchInput, bucketSelect, confidenceSelect]) {
  if (el) el.addEventListener('input', applyFilters);
}
