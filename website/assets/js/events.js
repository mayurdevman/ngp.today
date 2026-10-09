(() => {
  const grid = document.getElementById('eventGrid');
  if (!grid) return;

  const cards = [...grid.querySelectorAll('.event')];
  const search = document.getElementById('eventSearch');
  const dateFilter = document.getElementById('dateFilter');
  if (!search || !dateFilter) return;

  const timeZone = 'Asia/Kolkata';
  const dateKey = value => {
    if (!value) return null;
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return null;
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone, year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(parsed);
    const part = type => parts.find(item => item.type === type)?.value;
    return `${part('year')}-${part('month')}-${part('day')}`;
  };
  const todayKey = dateKey(new Date().toISOString());
  const shiftDate = (key, days) => {
    const [year, month, day] = key.split('-').map(Number);
    const value = new Date(Date.UTC(year, month - 1, day + days));
    return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, '0')}-${String(value.getUTCDate()).padStart(2, '0')}`;
  };
  const weekday = key => new Date(`${key}T12:00:00Z`).getUTCDay();

  function weekendRange() {
    const day = weekday(todayKey);
    const daysUntilSaturday = (6 - day + 7) % 7;
    const start = day === 0 ? shiftDate(todayKey, -1) : shiftDate(todayKey, daysUntilSaturday);
    return [start, shiftDate(start, 1)];
  }

  function applyFilters() {
    const query = search.value.trim().toLocaleLowerCase('en-IN');
    const selectedDate = dateFilter.value;
    const [weekendStart, weekendEnd] = weekendRange();
    let shown = 0;

    cards.forEach(card => {
      const eventKey = dateKey(card.dataset.startsAt);
      const textMatch = !query || card.textContent.toLocaleLowerCase('en-IN').includes(query);
      let dateMatch = true;

      if (selectedDate === 'today') dateMatch = eventKey === todayKey;
      if (selectedDate === 'upcoming') dateMatch = !!eventKey && eventKey >= todayKey;
      if (selectedDate === 'weekend') {
        dateMatch = !!eventKey && eventKey >= todayKey &&
          eventKey >= weekendStart && eventKey <= weekendEnd;
      }

      const visible = textMatch && dateMatch;
      card.hidden = !visible;
      if (visible) shown++;
    });

    let empty = grid.querySelector('.filtered-empty');
    if (!shown && cards.length) {
      if (!empty) {
        empty = document.createElement('div');
        empty.className = 'empty filtered-empty';
        empty.textContent = 'No events match this search.';
        grid.appendChild(empty);
      }
    } else if (empty) {
      empty.remove();
    }
  }

  search.addEventListener('input', applyFilters);
  dateFilter.addEventListener('change', applyFilters);
  applyFilters();

  const submitForm = document.getElementById('submitForm');
  const toggleSubmit = document.getElementById('toggleSubmit');
  if (submitForm && toggleSubmit) {
    toggleSubmit.addEventListener('click', () => {
      const open = submitForm.classList.toggle('open');
      toggleSubmit.setAttribute('aria-expanded', String(open));
      toggleSubmit.textContent = open ? 'Close form' : '+ Submit an event';
    });
    submitForm.addEventListener('submit', event => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(submitForm).entries());
      const subject = encodeURIComponent('NGP Today event submission: ' + data.title);
      const body = encodeURIComponent(
        'Please review this event for NGP Today.\n\n' +
        'Title: ' + data.title + '\nCategory: ' + data.category +
        '\nDate: ' + data.date + '\nTime: ' + (data.time || 'Not provided') +
        '\nVenue: ' + data.venue + '\nEvent URL: ' + data.url +
        '\nCover image URL: ' + (data.image || 'Not provided') +
        '\nPrice: ' + (data.price || 'Not provided') +
        '\nDetails: ' + (data.details || 'Not provided') +
        '\nSubmitter email: ' + (data.email || 'Not provided') +
        '\n\nPlease verify details before publishing.'
      );
      const status = document.getElementById('formStatus');
      if (status) status.textContent = 'Your email app will open with the event details. Send the email to submit; the event will be reviewed before publishing.';
      window.location.href = 'mailto:hello@ngp.today?subject=' + subject + '&body=' + body;
    });
  }

})();
