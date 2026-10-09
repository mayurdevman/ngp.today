(() => {
  const grid = document.getElementById('eventGrid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.event')];
  const search = document.getElementById('eventSearch');
  const date = document.getElementById('dateFilter');
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const dateOf = card => { const raw = card.dataset.startsAt; if (!raw) return null; const parsed = new Date(raw); return Number.isNaN(parsed.getTime()) ? null : parsed; };
  function applyFilters() {
    const query = search.value.trim().toLocaleLowerCase();
    let shown = 0;
    cards.forEach(card => {
      const eventDate = dateOf(card);
      const textMatch = !query || card.textContent.toLocaleLowerCase().includes(query);
      let dateMatch = true;
      if (date.value === 'today') dateMatch = !!eventDate && eventDate.toDateString() === today.toDateString();
      if (date.value === 'upcoming') dateMatch = !!eventDate && eventDate >= today;
      if (date.value === 'weekend') {
        const day = today.getDay();
        const start = new Date(today);
        start.setDate(today.getDate() + ((6 - day + 7) % 7));
        const end = new Date(start);
        end.setDate(start.getDate() + 1);
        dateMatch = !!eventDate && eventDate >= today && eventDate <= end;
      }
      const visible = textMatch && dateMatch;
      card.hidden = !visible;
      if (visible) shown++;
    });
    let empty = grid.querySelector('.filtered-empty');
    if (!shown && cards.length) {
      if (!empty) { empty = document.createElement('div'); empty.className = 'empty filtered-empty'; empty.textContent = 'No events match this search.'; grid.appendChild(empty); }
    } else if (empty) empty.remove();
  }
  [search, date].forEach(element => element.addEventListener('input', applyFilters));
  applyFilters();
})();
